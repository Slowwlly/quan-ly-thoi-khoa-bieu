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
    """Tao bang neu chua co, giu tenHienThi lop, va nang cap CSDL cu (co sao luu truoc khi nang cap)."""
    from . import migrations
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    da_co_du_lieu = False
    if os.path.exists(path):
        c0 = sqlite3.connect(path)
        try:
            da_co_du_lieu = c0.execute("SELECT 1 FROM sqlite_master WHERE name='SinhVien'").fetchone() is not None \
                and migrations.can_nang_cap(c0)
        finally:
            c0.close()
    if da_co_du_lieu:
        migrations.sao_luu(path)

    con = sqlite3.connect(path, isolation_level=None)
    try:
        con.execute('PRAGMA foreign_keys = OFF')   # can thiet khi dung lai bang
        with open(SCHEMA, encoding='utf-8') as f:
            con.executescript(f.read())
        if migrations.can_nang_cap(con):
            migrations.nang_cap(con)
        # Tuong thich CSDL rat cu: cot tenHienThi / maSoSinhVien
        lop_cols = {r[1] for r in con.execute('PRAGMA table_info(Lop)')}
        if 'tenHienThi' not in lop_cols:
            con.execute('ALTER TABLE Lop ADD COLUMN tenHienThi TEXT')
    finally:
        con.close()
