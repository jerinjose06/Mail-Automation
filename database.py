import sqlite3
import os

DB_NAME = "email_agent.db"

def init_db(db_path=DB_NAME):
    """
    Initialize the SQLite database and create necessary tables if they don't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create alert_rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY,
            sender_email TEXT,
            condition TEXT
        )
    ''')

    # Create triggered_alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS triggered_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT NOT NULL,
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create processed_emails table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_id TEXT PRIMARY KEY,
            processed_at TIMESTAMP,
            summary TEXT,
            is_alert_triggered INTEGER,
            is_read_by_user INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

def add_alert_rule(sender_email: str, condition: str = "") -> bool:
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO alert_rules (sender_email, condition) VALUES (?, ?)", (sender_email, condition))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding alert rule: {e}")
        return False

def delete_alert_rules(sender_email: str = None) -> bool:
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if sender_email and sender_email.lower() != "all":
            cursor.execute("DELETE FROM alert_rules WHERE sender_email = ?", (sender_email,))
        else:
            cursor.execute("DELETE FROM alert_rules")
            
        cursor.execute("DELETE FROM processed_emails WHERE is_alert_triggered = 1")
        cursor.execute("DELETE FROM triggered_alerts")
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting alert rules: {e}")
        return False

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_NAME}")
