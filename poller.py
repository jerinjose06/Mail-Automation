import sqlite3
import datetime
import os
import winsound
import time
from plyer import notification
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from database import DB_NAME
from email_service import search_emails
from agent import app as agent_app
import re

def get_alert_rules(cursor):
    cursor.execute("SELECT id, sender_email, condition FROM alert_rules")
    return cursor.fetchall()

def is_processed(cursor, email_id):
    cursor.execute("SELECT 1 FROM processed_emails WHERE email_id = ?", (email_id,))
    return cursor.fetchone() is not None

def match_rules(email, rules):
    sender = email.get('sender', '')
    email_subject = email.get('subject', '')
    email_body = email.get('body', '')
    
    llm = ChatOllama(model="qwen3.5:4b", temperature=0)
    
    for rule_id, sender_email, condition in rules:
        if sender_email:
            clean_rule_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender_email)
            if clean_rule_email:
                target_domain_match = clean_rule_email.group(0).lower()
                if target_domain_match not in sender.lower():
                    continue
            else:
                if sender_email.lower() not in sender.lower():
                    continue
            
        if not condition or str(condition).strip() == "" or str(condition).lower() == "none":
            return rule_id
            
        eval_prompt = f"""
        Analyze if the following email matches the user's alerting criteria.
        
        Alert Criteria: {condition}
        
        Email ID: {email.get('id')}
        Thread ID: {email.get('threadId')}
        Original Message-ID Header: {email.get('message_id')}
        Email Subject: {email_subject}
        Email Body: {email_body}
        
        Does this email meet the alert criteria condition? Answer with exactly one word: 'YES' or 'NO'. Do not add punctuation or commentary.
        """
        try:
            response = llm.invoke([HumanMessage(content=eval_prompt)]).content.strip().upper()
            if "YES" in response:
                return rule_id
        except Exception as e:
            print(f"Error during semantic match: {e}")
            
    return None

def generate_summary(body):
    llm = ChatOllama(model="qwen3.5:4b", temperature=0)
    prompt = f"You are an email notification assistant. Do not analyze the tone or writing style of the email. Write a concise, 1-sentence summary describing the core action or event requested in the email body.\n\nEmail Body:\n{body}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

def poll_inbox():
    # Fetch unread emails from Gmail (max 10)
    inbox = search_emails(custom_query="is:unread", limit=10)

    if not inbox:
        print("No new emails found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    rules = get_alert_rules(cursor)

    for email in inbox:
        email_id = email.get('id')
        if not email_id:
            continue
            
        if is_processed(cursor, email_id):
            print(f"Email {email_id} already processed. Skipping.")
            continue

        print(f"Processing new email: {email_id}")
        matched_rule_id = match_rules(email, rules)
        is_alert = matched_rule_id is not None
        
        summary = ""
        processed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if is_alert:
            print(f"Alert rule triggered for email {email_id}. Generating summary...")
            raw_body = email.get('body', '')
            clean_body = re.sub(r'<[^>]+>', '', raw_body).strip()
            summary = clean_body[:300] + "..." if len(clean_body) > 300 else clean_body
            if not summary:
                summary = email.get('subject', 'No Subject')
                
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                notification.notify(
                    title=f"New Alert: {email.get('sender', 'Unknown')}",
                    message=summary if summary else "An alert was triggered.",
                    app_name="Local Email Agent",
                    timeout=5
                )
            except Exception as e:
                print(f"Notification error: {e}")

            condition_text = next((r[2] for r in rules if r[0] == matched_rule_id), "")
            prompt = f"""
            An email has arrived matching an automation rule.
            Rule Instructions: {condition_text}
            User Name: Jerin Jose
            
            Email ID: {email.get('id')}
            Thread ID: {email.get('threadId')}
            Original Message-ID Header: {email.get('message_id')}
            Email From: {email.get('sender', 'Unknown')}
            Email Subject: {email.get('subject', 'No Subject')}
            Email Body: {clean_body}
            
            You must draft a professional reply email content based on the instructions. When calling the tool to transmit the message, you MUST explicitly provide the 'thread_id', 'in_reply_to', and 'references' arguments using the provided Thread ID and Original Message-ID so it formats as a true inline reply thread. Always sign off as Jerin Jose.
            """
            try:
                print(f"[POLLER] Attempting background response for {email_id}...")
                agent_app.invoke({"messages": [HumanMessage(content=prompt)]})
            except Exception as e:
                print(f"[POLLER ERROR] Autonomous response failed: {str(e)}")

            # Populate triggered_alerts
            cursor.execute('''
                INSERT INTO triggered_alerts (sender_email, summary, timestamp) 
                VALUES (?, ?, ?)
            ''', (email.get('sender', 'Unknown'), summary, processed_at))
            
            # One-Shot Auto-Delete
            cursor.execute("DELETE FROM alert_rules WHERE id = ?", (matched_rule_id,))
            rules = [r for r in rules if r[0] != matched_rule_id]
        
        cursor.execute('''
            INSERT INTO processed_emails 
            (email_id, processed_at, summary, is_alert_triggered, is_read_by_user)
            VALUES (?, ?, ?, ?, ?)
        ''', (email_id, processed_at, summary, 1 if is_alert else 0, 0))
        
        conn.commit()
        print(f"Email {email_id} processed successfully.")

    conn.close()

def start_polling_loop():
    while True:
        try:
            poll_inbox()
        except Exception as e:
            print(f"Error in polling loop: {e}")
        time.sleep(60)

if __name__ == "__main__":
    start_polling_loop()
