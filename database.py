import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            budget TEXT,
            skills TEXT,
            category TEXT,
            posted_at TEXT,
            client_info TEXT,
            scraped_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_job(job_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO jobs (url, title, description, budget, skills, category, posted_at, client_info, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_data.get("url"),
                job_data.get("title"),
                job_data.get("description"),
                job_data.get("budget"),
                job_data.get("skills"),
                job_data.get("category"),
                job_data.get("posted_at"),
                job_data.get("client_info"),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        result = cursor.rowcount > 0
    except Exception as e:
        print(f"Error saving job: {e}")
        result = False
    finally:
        conn.close()
    return result


def get_all_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY scraped_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
