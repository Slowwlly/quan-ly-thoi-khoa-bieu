"""Xac thuc va phan quyen (muc 3.4.7): kiem tra o phia may chu, khong chi an nut tren giao dien."""
from functools import wraps
from flask import session
from .db import get_db
from .errors import AppError, Forbidden


def current_user():
    """Tra ve dict nguoi dung hien tai (kem ma giang vien/sinh vien/lop) hoac None."""
    ma = session.get('maTaiKhoan')
    if not ma:
        return None
    db = get_db()
    tk = db.execute('SELECT maTaiKhoan, tenDangNhap, vaiTro FROM TaiKhoan WHERE maTaiKhoan=?', (ma,)).fetchone()
    if tk is None:
        session.clear()
        return None
    u = dict(tk)
    gv = db.execute('SELECT maGiangVien, hoTen FROM GiangVien WHERE maTaiKhoan=?', (ma,)).fetchone()
    sv = db.execute('SELECT s.maSinhVien, s.hoTen, s.maLop, l.tenLop FROM SinhVien s JOIN Lop l ON l.maLop=s.maLop '
                    'WHERE s.maTaiKhoan=?', (ma,)).fetchone()
    u.update(dict(gv) if gv else {})
    u.update(dict(sv) if sv else {})
    u['hoTen'] = u.get('hoTen') or ('Phong dao tao' if u['vaiTro'] == 'PHONG_DAO_TAO' else u['tenDangNhap'])
    return u


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        user = current_user()
        if user is None:
            raise AppError('Vui long dang nhap', 401)
        return fn(user, *a, **kw)
    return wrapper


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapper(user, *a, **kw):
            if user['vaiTro'] not in roles:
                raise Forbidden()
            return fn(user, *a, **kw)
        return wrapper
    return deco
