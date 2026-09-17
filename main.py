import os
import sqlite3
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- تنظیمات اجباری Volume ---
DB_DIR = "/myfiles"

# بررسی اجباری: اگر مسیر ولوم وجود نداشته باشد، برنامه کلاً بالا نمی‌آید و خطا می‌دهد
if not os.path.exists(DB_DIR):
    raise RuntimeError(
        f"\n\n❌ ERROR: Volume path '{DB_DIR}' was not found!\n"
        "mount it\n"
    )

DB_PATH = os.path.join(DB_DIR, "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT NOT NULL,
            product TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()
