# db_utils.py
import os
import sqlite3
from datetime import datetime
import pandas as pd

DB_PATH = "data/db.sqlite"
RESULTS_DIR = "data/results"


def init_storage():
    """Create folders and DB table if not present."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_result(user_id: str, topic: str, difficulty: str,
                score: int, total_questions: int):
    """Save one quiz attempt to SQLite + CSV."""
    os.makedirs(RESULTS_DIR, exist_ok=True)

    percentage = round((score / total_questions) * 100, 2) if total_questions else 0.0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_for_filename = now.split(" ")[0]  # YYYY-MM-DD

    # ---- 1) Save to SQLite ----
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO quiz_results
        (user_id, topic, difficulty, score, total_questions, percentage, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, topic, difficulty, score, total_questions, percentage, now),
    )
    conn.commit()
    conn.close()

    # ---- 2) Save to CSV ----
    safe_user = user_id.replace(" ", "_")
    safe_topic = topic.replace(" ", "_")
    safe_diff = difficulty.replace(" ", "_")
    filename = f"{safe_user}_{safe_topic}_{safe_diff}_{date_for_filename}.csv"
    csv_path = os.path.join(RESULTS_DIR, filename)

    df = pd.DataFrame(
        [{
            "user_id": user_id,
            "topic": topic,
            "difficulty": difficulty,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "timestamp": now,
        }]
    )
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    return percentage, csv_path


def load_user_history(user_id: str) -> pd.DataFrame:
    """Return all results for a given user_id as a DataFrame."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT timestamp, topic, difficulty, score, total_questions, percentage
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY timestamp DESC
        """,
        conn,
        params=(user_id,),
    )
    conn.close()
    return df
