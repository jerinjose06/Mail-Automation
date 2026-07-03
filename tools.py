from langchain_core.tools import tool
from pydantic import BaseModel, Field
from email_service import search_emails, slice_text, delete_email, bulk_delete_emails, send_email
from database import add_alert_rule, delete_alert_rules
from typing import Optional, List, Union

class SearchEmailsArgs(BaseModel):
    date: Optional[str] = Field(
        default=None, 
        description="The date to search for. You MUST normalize natural dates (like 'July 5th, 2026') into 'DD-MM-YYYY' string format (e.g., '05-07-2026')."
    )
    sender: Optional[str] = Field(
        default=None, 
        description="The sender's name or email address to filter by."
    )
    query: Optional[str] = Field(
        default=None,
        description="A free-text custom query string to filter emails (e.g. 'Security Alert'). Passed directly to Gmail API."
    )

@tool("search_emails_tool", args_schema=SearchEmailsArgs)
def search_emails_tool(date: Optional[str] = None, sender: Optional[str] = None, query: Optional[str] = None) -> str:
    """Search for emails by date, sender, or custom query."""
    results = search_emails(date=date, sender=sender, custom_query=query)
    
    if not results:
        return "No emails found matching the criteria."
        
    formatted_results = []
    for email in results:
        body = slice_text(email['body'])
        formatted_results.append(
            f"ID: {email['id']}\nDate: {email['date']}\nSender: {email['sender']}\nSubject: {email['subject']}\nBody: {body}\n"
        )
    return "\n---\n".join(formatted_results)

class DeleteEmailArgs(BaseModel):
    email_id: Union[str, List[str]] = Field(
        description="The ID of the email, or a list of email IDs, to move to the trash."
    )

@tool("delete_email_tool", args_schema=DeleteEmailArgs)
def delete_email_tool(email_id: Union[str, List[str]]) -> str:
    """Move one or more emails to the trash by their IDs."""
    if isinstance(email_id, str):
        email_ids = [email_id]
    else:
        email_ids = email_id
        
    success_count = 0
    for eid in email_ids:
        if delete_email(eid):
            success_count += 1
            
    return f"Successfully moved {success_count}/{len(email_ids)} emails to the trash."

class BulkDeleteArgs(BaseModel):
    query_filter: Optional[str] = Field(
        default=None,
        description="Optional Gmail search query filter (e.g. 'from:alice' or 'Security Alert'). Defaults to 'is:unread'."
    )

@tool("bulk_delete_inbox_tool", args_schema=BulkDeleteArgs)
def bulk_delete_inbox_tool(query_filter: Optional[str] = None) -> str:
    """Bulk delete emails matching a query without reading their content."""
    count = bulk_delete_emails(query_filter)
    return f"Successfully moved {count} emails to the trash folder directly."

class SendEmailArgs(BaseModel):
    to_email: str = Field(description="The recipient's email address.")
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The body content of the email.")
    thread_id: Optional[str] = Field(default=None, description="The Gmail thread ID if this is a reply.")
    in_reply_to: Optional[str] = Field(default=None, description="The original Message-ID header if this is a reply.")
    references: Optional[str] = Field(default=None, description="The original Message-ID header if this is a reply.")

@tool("send_email_tool", args_schema=SendEmailArgs)
def send_email_tool(to_email: str, subject: str, body: str, thread_id: Optional[str] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> str:
    """Compose and send an email."""
    if send_email(to_email, subject, body, thread_id=thread_id, in_reply_to=in_reply_to, references=references):
        return f"Successfully sent email to {to_email} with subject '{subject}'."
    else:
        return f"Failed to send email to {to_email}."

class AddAlertRuleArgs(BaseModel):
    sender_email: str = Field(description="The email address to monitor for new incoming messages.")
    condition: Optional[str] = Field(default="", description="Optional keyword or condition to match in the subject or body.")

@tool("add_alert_rule_tool", args_schema=AddAlertRuleArgs)
def add_alert_rule_tool(sender_email: str, condition: Optional[str] = "") -> str:
    """Add a new background alert monitoring rule to the database."""
    if add_alert_rule(sender_email, condition):
        return f"Successfully added background alert rule for {sender_email}."
    else:
        return f"Failed to add background alert rule for {sender_email}."

class DeleteAlertRuleArgs(BaseModel):
    sender_email: Optional[str] = Field(default=None, description="The specific sender email to stop tracking, or None/'all' to clear all rules.")

@tool("delete_alert_rules_tool", args_schema=DeleteAlertRuleArgs)
def delete_alert_rules_tool(sender_email: Optional[str] = None) -> str:
    """Delete specific or all background alert monitoring rules."""
    if delete_alert_rules(sender_email):
        return "Successfully cleared alert rules from the local database."
    else:
        return "Failed to clear alert rules."
