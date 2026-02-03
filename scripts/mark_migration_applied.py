import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')

def mark(app, name):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Ensure table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
    if not cur.fetchone():
        print('django_migrations table not found in', DB)
        conn.close()
        return
    applied = datetime.utcnow().isoformat()
    try:
        cur.execute("INSERT INTO django_migrations(app, name, applied) VALUES (?, ?, ?)", (app, name, applied))
        conn.commit()
        print(f'Marked migration {app}.{name} as applied at {applied}')
    except Exception as e:
        print('Error inserting migration record:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    mark('app', '0003_combined')
