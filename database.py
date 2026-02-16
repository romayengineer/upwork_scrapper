import sqlite3
import config
from datetime import datetime


def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            url TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
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
    print("Database initialized.\n")


def save_job(job_data: dict):
    conn = sqlite3.connect(config.DB_PATH)
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
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY scraped_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_job_by_id(job_id):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    url = f"{config.JOBS_URL}/{job_id}"
    cursor.execute("SELECT * FROM jobs where url = ? LIMIT 1", (url,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_url():
    jobs = get_all_jobs()
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    for job in jobs:
        url = job[0]
        job_id = url.split("/")[-1]
        new_url = f"https://www.upwork.com/jobs/{job_id}"
        print(url, new_url)
        cursor.execute("UPDATE jobs SET url = ? WHERE url = ?", (new_url, url))
    conn.commit()
    conn.close()
