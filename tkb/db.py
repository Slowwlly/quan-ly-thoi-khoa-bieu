import os
import sqlite3
from flask import g, current_app

SCHEMA = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(path):
    """Tao bang neu chua co (khong xoa du lieu cu)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path)
    with open(SCHEMA, encoding='utf-8') as f:
        con.executescript(f.read())
    con.commit()
    con.close()
