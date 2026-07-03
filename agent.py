from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from tools import search_emails_tool, delete_email_tool, bulk_delete_inbox_tool, send_email_tool, add_alert_rule_tool, delete_alert_rules_tool
import re
import uuid

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Initialize LLM and bind tool
# Ensure this strictly points to the same model we verified earlier
llm = ChatOllama(model="qwen3.5:4b", temperature=0)
tools = [search_emails_tool, delete_email_tool, bulk_delete_inbox_tool, send_email_tool, add_alert_rule_tool, delete_alert_rules_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = "CRITICAL: If the user's intent is to delete, trash, or clear emails, you MUST call 'delete_email_tool' immediately after obtaining the email IDs. Do not generate markdown summaries, tables, or helpful advice until the deletion action has been executed. When the user asks to delete all emails or empty the inbox, do not search for the emails. Immediately call 'bulk_delete_inbox_tool' with the appropriate keyword filter. You can also compose responses or send fresh notifications using 'send_email_tool' when explicitly requested. You are an assistant representing the user. The user's name is Jerin Jose. Whenever you compose, draft, or reply to an email, you must always sign off the email using the name 'Jerin Jose' at the bottom. Never leave placeholder brackets like '[Your Name]' or '[Sender]' under any circumstances. If the user asks you to alert them, monitor an email, or notify them when a message arrives from a specific sender, you must immediately call 'add_alert_rule_tool' with the sender's email. Inform the user that the background poller is now watching for those messages. When the user asks to delete all alerts, remove a specific tracking rule, or clear their alert configurations, immediately call 'delete_alert_rules_tool'. Confirm to the user that the dashboard list has been reset."

def llm_node(state: AgentState):
    print("--- LLM NODE ---")
    messages = list(state["messages"])
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
        
    response = llm_with_tools.invoke(messages)
    
    user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    if user_msgs:
        last_user_msg = user_msgs[-1].content.lower()
        if re.search(r'\b(delete|trash|clear)\b', last_user_msg):
            if not response.tool_calls:
                email_ids = re.findall(r'\b[0-9a-fA-F]{15,17}\b', response.content)
                if email_ids:
                    print(f"Fallback: Forcing delete_email_tool for IDs: {email_ids}")
                    response.tool_calls.append({
                        "name": "delete_email_tool",
                        "args": {"email_id": email_ids},
                        "id": f"call_{uuid.uuid4().hex[:8]}"
                    })
                    
    return {"messages": [response]}

def tool_node(state: AgentState):
    print("--- TOOL NODE ---")
    last_message = state["messages"][-1]
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        args = tool_call["args"]
        print(f"Executing tool {tool_call['name']} with args: {args}")
        if tool_call["name"] == "search_emails_tool":
            result = search_emails_tool.invoke(args)
        elif tool_call["name"] == "delete_email_tool":
            result = delete_email_tool.invoke(args)
        elif tool_call["name"] == "bulk_delete_inbox_tool":
            result = bulk_delete_inbox_tool.invoke(args)
        elif tool_call["name"] == "send_email_tool":
            result = send_email_tool.invoke(args)
        elif tool_call["name"] == "add_alert_rule_tool":
            result = add_alert_rule_tool.invoke(args)
        elif tool_call["name"] == "delete_alert_rules_tool":
            result = delete_alert_rules_tool.invoke(args)
        else:
            result = f"Error: Unknown tool {tool_call['name']}."
            
        print(f"Tool Result:\n{result}")
        tool_messages.append(
            ToolMessage(content=result, name=tool_call["name"], tool_call_id=tool_call["id"])
        )
    return {"messages": tool_messages}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "continue"
    return "end"

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("llm", llm_node)
workflow.add_node("tool", tool_node)
workflow.set_entry_point("llm")
workflow.add_conditional_edges("llm", should_continue, {"continue": "tool", "end": END})
workflow.add_edge("tool", "llm")

app = workflow.compile()

if __name__ == "__main__":
    print("Starting agent test...")
    # Explicitly asking about July 5th, 2026 to see if the LLM normalizes to 05-07-2026
    initial_message = HumanMessage(content="Summarize emails from Alice on July 5th, 2026.")
    
    final_state = app.invoke({"messages": [initial_message]})
    print("\n--- FINAL OUTPUT ---")
    print(final_state["messages"][-1].content)
