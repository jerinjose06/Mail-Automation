import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from poller import poll_inbox
import logging
import subprocess
import shutil

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Checking Ollama server status...")
    # Verify ollama CLI exists on the system path
    if shutil.which("ollama"):
        try:
            # Launch the model as a non-blocking background process
            # Windows flags to hide the console window popup: creationflags=subprocess.CREATE_NO_WINDOW
            subprocess.Popen(
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Start the background poller task
    task = asyncio.create_task(poller_task())
    yield
    # Cancel the background task on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Local Email Agent Running"}
