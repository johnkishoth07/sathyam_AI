import sqlite3

DATABASE = "satyam.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS bidders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            gstin TEXT,
            pan_number TEXT,
            udyam_number TEXT,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_number TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bidder_id INTEGER NOT NULL,
            tender_id INTEGER NOT NULL,
            bid_amount REAL NOT NULL,
            FOREIGN KEY (bidder_id) REFERENCES bidders(id),
            FOREIGN KEY (tender_id) REFERENCES tenders(id)
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bidder_id INTEGER,
            tender_id INTEGER,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            document_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bidder_id) REFERENCES bidders(id),
            FOREIGN KEY (tender_id) REFERENCES tenders(id)
        );

        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_id INTEGER NOT NULL,
            requirement_text TEXT NOT NULL,
            requirement_type TEXT,
            FOREIGN KEY (tender_id) REFERENCES tenders(id)
        );

        CREATE TABLE IF NOT EXISTS verification_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id INTEGER NOT NULL,
            document_id INTEGER,
            status TEXT NOT NULL,
            confidence REAL,
            reason TEXT,
            FOREIGN KEY (requirement_id) REFERENCES requirements(id),
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("SATYAM database tables created successfully.")
    
