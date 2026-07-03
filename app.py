import streamlit as st
import sqlite3
import subprocess
import threading
from poller import start_polling_loop
from agent import app as agent_app
from langchain_core.messages import HumanMessage, AIMessage
from email_service import get_gmail_service, fetch_email_data
from database import init_db
from datetime import datetime

DB_NAME = "email_agent.db"

st.set_page_config(page_title="Local Email Agent", layout="wide")

# Initialize session state for the agent and chat history
if "agent_app" not in st.session_state:
    st.session_state.agent_app = agent_app

if "messages" not in st.session_state:
    st.session_state.messages = []

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@st.cache_resource
def init_app():
    init_db()
    try:
        subprocess.Popen(["ollama", "run", "qwen3.5:4b"], creationflags=0x08000000)
    except Exception:
        pass
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM processed_emails WHERE email_id IN ('abc123xyz', '4')")
        conn.commit()
        conn.close()
    except Exception:
        pass

init_app()

if "poller_thread" not in st.session_state:
    thread = threading.Thread(target=start_polling_loop, daemon=True)
    thread.start()
    st.session_state.poller_thread = thread
    print("[SYSTEM] Background email poller thread started successfully.")

def get_active_rules():
    conn = get_db_connection()
    rules = conn.execute("SELECT * FROM alert_rules").fetchall()
    conn.close()
    return rules

def add_rule(sender, condition):
    conn = get_db_connection()
    conn.execute("INSERT INTO alert_rules (sender_email, condition) VALUES (?, ?)", (sender, condition))
    conn.commit()
    conn.close()

def get_triggered_alerts():
    conn = get_db_connection()
    alerts = conn.execute("SELECT sender_email, summary, timestamp FROM triggered_alerts ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(a) for a in alerts]

st.title("🛡️ Local Email Agent Dashboard")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("🔔 Triggered Alerts")
    
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="alerts_autorefresh")
    except ImportError:
        if st.button("Refresh Alerts"):
            st.rerun()
            
    alerts = get_triggered_alerts()
    if not alerts:
        st.info("No active alerts.")
    else:
        for alert in alerts:
            with st.container():
                timestamp_str = alert['timestamp']
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    friendly_time = dt.strftime("%B %d, %Y at %I:%M %p")
                except Exception:
                    friendly_time = timestamp_str

                st.markdown(f"**From:** {alert['sender_email']}")
                st.write(f"**Timestamp:** {friendly_time}")
                st.info(f"**Summary:** {alert['summary']}")
                st.divider()

    st.header("⚙️ Alert Rules")
    with st.expander("Add New Rule"):
        with st.form("new_rule_form"):
            sender_input = st.text_input("Sender Email (Optional)")
            condition_input = st.text_input("Condition/Keyword (Optional)")
            submitted = st.form_submit_button("Add Rule")
            if submitted:
                if sender_input or condition_input:
                    add_rule(sender_input, condition_input)
                    st.success("Rule added!")
                    st.rerun()
                else:
                    st.error("Please provide either a sender or a condition.")
    
    st.subheader("Active Rules")
    conn = get_db_connection()
    rules = conn.execute("SELECT sender_email, condition FROM alert_rules").fetchall()
    conn.close()
    if not rules:
        st.write("No rules set.")
    else:
        for rule in rules:
            st.markdown(f"* **Sender:** {rule[0]} | **Condition:** {rule[1]}")

with col2:
    st.header("💬 Agent Chat")
    st.write("Ask the local LLM agent to search and summarize emails.")
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # React to user input
    if prompt := st.chat_input("Summarize emails from Alice on July 5th..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Invoke agent
        with st.spinner("Thinking..."):
            initial_message = HumanMessage(content=prompt)
            needs_rerun = False
            try:
                final_state = st.session_state.agent_app.invoke({"messages": [initial_message]})
                response_content = final_state["messages"][-1].content
                
                for msg in final_state.get("messages", []):
                    tool_calls = getattr(msg, "tool_calls", [])
                    if tool_calls:
                        for tc in tool_calls:
                            if tc["name"] in ["add_alert_rule_tool", "delete_alert_rules_tool"]:
                                needs_rerun = True
            except Exception:
                st.error("Ollama is initializing, please wait 5 seconds and refresh...")
                response_content = None
            
        if response_content:
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response_content)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            
            if needs_rerun:
                st.rerun()
