import sqlite3

DB_PATH = 'linkedin_automation.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS perfis_contactados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        link TEXT UNIQUE,
        data_envio TEXT
    )''')
    conn.commit()
    conn.close()

def perfil_ja_contactado(link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM perfis_contactados WHERE link = ?', (link,))
    result = c.fetchone()
    conn.close()
    return result is not None

def registrar_envio(perfil):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO perfis_contactados (nome, link, data_envio) VALUES (?, ?, ?)',
              (perfil['nome'], perfil['link'], datetime.now().isoformat()))
    conn.commit()
    conn.close()
