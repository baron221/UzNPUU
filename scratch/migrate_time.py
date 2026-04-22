
import sqlite3
import os

db_path = 'data/university.db'
if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
try:
    # Update questions
    conn.execute("UPDATE questions SET created_at = datetime(created_at, '+5 hours')")
    conn.execute("UPDATE questions SET answered_at = datetime(answered_at, '+5 hours') WHERE answered_at IS NOT NULL")
    
    # Update students
    conn.execute("UPDATE students SET created_at = datetime(created_at, '+5 hours')")
    
    # Update FAQ
    conn.execute("UPDATE faq_items SET created_at = datetime(created_at, '+5 hours')")
    
    conn.commit()
    print("Migration successful: Added +5 hours to existing records.")
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()
