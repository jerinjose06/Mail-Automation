import os.path
import base64
from datetime import datetime
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticates and returns the Gmail API service instance."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Missing {creds_path}. Please obtain credentials.json from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def fetch_email_data(service, message_id):
    """Fetches a single email by ID and extracts relevant fields."""
    try:
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        headers = msg['payload'].get('headers', [])
        
        email_data = {
            "id": msg['id'],
            "threadId": msg.get('threadId'),
            "message_id": "",
            "date": "",
            "sender": "",
            "subject": "",
            "body": ""
        }
        
        for header in headers:
            name = header['name'].lower()
            if name == 'from':
                email_data["sender"] = header['value']
            elif name == 'subject':
                email_data["subject"] = header['value']
            elif name == 'date':
                email_data["date"] = header['value']
            elif name == 'message-id':
                email_data["message_id"] = header['value']

        def get_body(payload):
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")
                    elif part.get('parts'):
                        res = get_body(part)
                        if res:
                            return res
            elif 'body' in payload and 'data' in payload['body']:
                data = payload['body']['data']
                return base64.urlsafe_b64decode(data).decode("utf-8")
            return ""

        email_data["body"] = get_body(msg['payload'])
        return email_data
    except Exception as e:
        print(f"Error fetching email {message_id}: {e}")
        return None

def search_emails(date: str = None, sender: str = None, custom_query: str = None, limit: int = 150) -> list:
    """Searches emails based on date, sender, or a custom query."""
    service = get_gmail_service()
    if not service:
        return []

    query_parts = []
    if date:
        # Optional: could attempt converting DD-MM-YYYY to Gmail format if needed
        query_parts.append(date) 
    if sender:
        query_parts.append(f"from:{sender}")
    if custom_query:
        query_parts.append(custom_query)
        
    q = " ".join(query_parts) if query_parts else ""
    
    try:
        batch_size = 50
        response = service.users().messages().list(userId='me', q=q, maxResults=batch_size).execute()
        messages = response.get('messages', [])
        
        while 'nextPageToken' in response and len(messages) < limit:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId='me', q=q, maxResults=batch_size, pageToken=page_token).execute()
            messages.extend(response.get('messages', []))
            
        messages = messages[:limit]
        
        results = []
        for message in messages:
            data = fetch_email_data(service, message['id'])
            if data:
                results.append(data)
        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def slice_text(text: str, max_length: int = 500) -> str:
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def delete_email(email_id: str) -> bool:
    service = get_gmail_service()
    if not service:
        return False
    try:
        service.users().messages().trash(userId='me', id=email_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting email {email_id}: {e}")
        return False

def bulk_delete_emails(query_filter: str = None) -> int:
    service = get_gmail_service()
    if not service:
        return 0
        
    q = query_filter if query_filter else "is:unread"
    success_count = 0
    try:
        # Request up to 150 items
        response = service.users().messages().list(userId='me', q=q, maxResults=150).execute()
        messages = response.get('messages', [])
        
        while 'nextPageToken' in response and len(messages) < 150:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId='me', q=q, maxResults=50, pageToken=page_token).execute()
            messages.extend(response.get('messages', []))
            
        messages = messages[:150]
        
        for msg in messages:
            try:
                service.users().messages().trash(userId='me', id=msg['id']).execute()
                success_count += 1
            except Exception as e:
                print(f"Error trashing {msg['id']}: {e}")
                
        return success_count
    except Exception as e:
        print(f"Bulk delete failed: {e}")
        return success_count

def send_email(to_email: str, subject: str, body: str, thread_id: str = None, in_reply_to: str = None, references: str = None) -> bool:
    service = get_gmail_service()
    if not service:
        return False
        
    try:
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
        if references:
            message['References'] = references
            
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        message_body = {
            'raw': raw_message
        }
        if thread_id:
            message_body['threadId'] = thread_id
            
        service.users().messages().send(userId='me', body=message_body).execute()
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False
