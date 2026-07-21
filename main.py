import asyncio
import logging
import shutil
import sqlite3
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from agent import app as agent_app
from database import init_db, DB_NAME
from poller import poll_inbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

async def poller_task():
    while True:
        try:
            logger.info("Polling inbox...")
            await asyncio.to_thread(poll_inbox)
        except asyncio.CancelledError:
            logger.info("Poller task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error while polling inbox: {e}")
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Checking Ollama server status...")
    ollama_process = None
    # Verify ollama CLI exists on the system path
    if shutil.which("ollama"):
        try:
            # Launch the model as a non-blocking background process
            # Windows flags to hide the console window popup: creationflags=subprocess.CREATE_NO_WINDOW
            ollama_process = subprocess.Popen(
                ["ollama", "run", "qwen3.5:4b"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Ollama model 'qwen3.5:4b' initialized automatically.")
        except Exception as e:
            print(f"Failed to auto-start Ollama model: {e}")
    else:
        print("Ollama CLI not found on system path. Please ensure Ollama is installed.")
    
    # Initialize the database
    init_db()

    # Start the background poller task
    task = asyncio.create_task(poller_task())
    
    yield
    
    # Cancel the background task on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    # Terminate Ollama subprocess
    if ollama_process:
        print("Terminating Ollama background process...")
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_process.kill()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

class RuleRequest(BaseModel):
    sender_email: str
    condition: str = ""

@app.get("/")
async def root():
    return {"status": "Local Email Agent Running"}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    initial_message = HumanMessage(content=req.prompt)
    try:
        final_state = await asyncio.to_thread(agent_app.invoke, {"messages": [initial_message]})
        response_content = final_state["messages"][-1].content
        return {"response": response_content}
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rules")
def get_rules(conn: sqlite3.Connection = Depends(get_db)):
    rules = conn.execute("SELECT id, sender_email, condition FROM alert_rules").fetchall()
    return {"rules": [dict(r) for r in rules]}

@app.post("/api/rules")
def add_rule(req: RuleRequest, conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("INSERT INTO alert_rules (sender_email, condition) VALUES (?, ?)", (req.sender_email, req.condition))
    conn.commit()
    return {"status": "success"}

@app.get("/api/alerts")
def get_alerts(conn: sqlite3.Connection = Depends(get_db)):
    alerts = conn.execute("SELECT id, sender_email, summary, timestamp FROM triggered_alerts ORDER BY timestamp DESC").fetchall()
    return {"alerts": [dict(a) for a in alerts]}
