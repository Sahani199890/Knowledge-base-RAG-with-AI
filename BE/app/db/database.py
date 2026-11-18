import sqlite3
import os
from contextlib import contextmanager
from app.config import settings
from app.logger import logger

def get_db_path() -> str:
    path = os.environ.get("DATABASE_PATH") or settings.DATABASE_PATH
    if not os.path.isabs(path):
        from app.config import BASE_DIR
        return os.path.abspath(os.path.join(BASE_DIR, path))
    return os.path.abspath(path)

@contextmanager
def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = DELETE;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()

def init_db():
    db_path = get_db_path()
    logger.info(f"Initializing database at: {os.path.abspath(db_path)}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            );
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at DESC);")
        
    logger.info("Database initialized successfully.")
