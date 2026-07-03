import os
from email_service import get_gmail_service, search_emails

def test_gmail():
    print("Testing Live Gmail Connection...")
    print("This may open a browser window for OAuth if token.json is missing or expired.")
    
    try:
        service = get_gmail_service()
        if not service:
            print("Failed to get Gmail service. Check credentials.")
            return
            
        print("\nSuccessfully authenticated!")
        print("Fetching latest unread emails...")
        
        emails = search_emails(custom_query="is:unread", limit=5)
        
        if not emails:
            print("No unread emails found.")
        else:
            for i, email in enumerate(emails, 1):
                print(f"\n--- Email {i} ---")
                print(f"From:    {email.get('sender')}")
                print(f"Subject: {email.get('subject')}")
                
        print("\nTest complete.")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Make sure you have downloaded credentials.json from the Google Cloud Console and placed it in this directory.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    test_gmail()
