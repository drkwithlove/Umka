import sqlite3
from datetime import datetime

DB_FILE = "memory.db"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Добавление сообщения
def add_message(role, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)', 
              (role, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# Получение всей истории
def get_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    return [{"role": role, "content": content} for role, content in rows]

# Очистка истории
def reset_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM messages')
    conn.commit()
    conn.close()

# Инициализация при запуске
init_db()
