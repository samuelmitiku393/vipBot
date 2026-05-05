import psycopg2
import os
from .config import DATABASE_URL
from .utils import logger

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            receipt TEXT,
            status TEXT DEFAULT 'pending',
            approved_at TEXT,
            expiry_date TIMESTAMP,
            subscription_type TEXT,
            reminded_3d BOOLEAN DEFAULT FALSE,
            reminded_1d BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        logger.info("Database initialized successfully")
    except psycopg2.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_user_status(telegram_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE telegram_id = %s", (telegram_id,))
        res = cursor.fetchone()
        return res[0] if res else None
    finally:
        conn.close()

def upsert_user_pending(telegram_id, username):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (telegram_id, username, status)
            VALUES (%s, %s, %s)
            ON CONFLICT(telegram_id)
            DO UPDATE SET
                username = excluded.username,
                status = 'pending',
                receipt = NULL,
                approved_at = NULL
        """, (telegram_id, username, 'pending'))
        conn.commit()
    finally:
        conn.close()

def get_user_by_id(telegram_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE telegram_id = %s", (telegram_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def update_user_status(telegram_id, status, approved_at=None, expiry_date=None, sub_type=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if approved_at:
            cursor.execute(
                "UPDATE users SET status = %s, approved_at = %s, expiry_date = %s, subscription_type = %s, reminded_3d = FALSE, reminded_1d = FALSE WHERE telegram_id = %s",
                (status, approved_at, expiry_date, sub_type, telegram_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET status = %s WHERE telegram_id = %s",
                (status, telegram_id)
            )
        conn.commit()
    finally:
        conn.close()

def update_reminder_status(telegram_id, column_name):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # column_name is either 'reminded_3d' or 'reminded_1d'
        cursor.execute(f"UPDATE users SET {column_name} = TRUE WHERE telegram_id = %s", (telegram_id,))
        conn.commit()
    finally:
        conn.close()

def get_active_users():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE status = 'approved'")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_approved_users():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telegram_id, username, approved_at, expiry_date, reminded_3d, reminded_1d
            FROM users
            WHERE status = 'approved'
            ORDER BY approved_at DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()
