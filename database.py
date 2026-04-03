import sqlite3

DB_FILE = "saig_events.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Requirement 4: Mandatory Output Schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT,
            device_id TEXT,
            device_type TEXT,
            location TEXT,
            event_type TEXT,
            anomaly_flag INTEGER,
            confidence_score REAL,
            raw_source_reference TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database and schema initialized successfully.")

if __name__ == "__main__":
    init_db()