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
    """Tao bang neu chua co va bo sung cot ma sinh vien cho CSDL cu."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        with open(SCHEMA, encoding='utf-8') as f:
            con.executescript(f.read())

        # Bo sung tenHienThi de hien ten lop de doc ma khong doi ma lop goc.
        lop_cols = {r[1] for r in con.execute('PRAGMA table_info(Lop)')}
        if 'tenHienThi' not in lop_cols:
            con.execute('ALTER TABLE Lop ADD COLUMN tenHienThi TEXT')

        ten_lop_hien_thi = {
            'CT2201': 'CNTT 1',
            'CT2202': 'CNTT 2',
            'CT2301': 'CNTT 3',
            'CT2302': 'CNTT 4',
            'QT2201': 'QTKD 1',
            'QTKD2301': 'QTKD 2',
            'DL2301': 'Du lịch 1',
            'DL2302': 'Du lịch 2',
            'NN2301': 'Ngoại ngữ 1',
            'DDT2301': 'Điện - Điện tử 1',
            'DDT2302': 'Điện - Điện tử 2',
        }
        for ma_lop, ten_hien_thi in ten_lop_hien_thi.items():
            con.execute(
                'UPDATE Lop SET tenHienThi=? WHERE tenLop=? '
                'AND (tenHienThi IS NULL OR tenHienThi = ?)',
                (ten_hien_thi, ma_lop, '')
            )

        # Tuong thich voi CSDL cu chua co maSoSinhVien.
        sv_cols = {r[1] for r in con.execute('PRAGMA table_info(SinhVien)')}
        if 'maSoSinhVien' not in sv_cols:
            con.execute('ALTER TABLE SinhVien ADD COLUMN maSoSinhVien TEXT')

        # Bo sung ma cho cac sinh vien cu, khong ghi de ma da co.
        con.execute("""
            UPDATE SinhVien
            SET maSoSinhVien = 'SV' || printf('%04d', maSinhVien)
            WHERE maSoSinhVien IS NULL OR TRIM(maSoSinhVien) = ''
        """)
        con.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_sinhvien_maso
            ON SinhVien(maSoSinhVien)
        """)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
