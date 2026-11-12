"""Quan ly danh muc: khoa, lop, mon hoc, phong hoc, giang vien, sinh vien (FR-18..FR-23)."""
import sqlite3

from ..config import GIANG_VIEN, SINH_VIEN
from ..errors import AppError, Conflict, NotFound
from . import tai_khoan


# Moi danh muc gom: ten bang, khoa chinh, truong nhap, cau SELECT hien thi,
# cac cot tim kiem va thu tu sap xep.
RESOURCES = {
    'khoa': dict(
        bang='Khoa',
        pk='maKhoa',
        truong=[('tenKhoa', 'str', True)],
        select='SELECT maKhoa, tenKhoa FROM Khoa',
        tim=['tenKhoa'],
        thu_tu='tenKhoa',
    ),
    'lop': dict(
        bang='Lop',
        pk='maLop',
        truong=[
            ('tenLop', 'str', True),
            ('khoaHoc', 'str', False),
            ('maKhoa', 'int', True),
        ],
        select=(
            'SELECT x.maLop, COALESCE(NULLIF(x.tenHienThi, \'\'), x.tenLop) AS tenLop, x.khoaHoc, x.maKhoa, k.tenKhoa '
            'FROM Lop x JOIN Khoa k ON k.maKhoa=x.maKhoa'
        ),
        tim=['x.tenLop', 'x.tenHienThi', 'k.tenKhoa'],
        thu_tu='x.tenLop',
        alias='x',
    ),
    'mon-hoc': dict(
        bang='MonHoc',
        pk='maMonHoc',
        truong=[('tenMonHoc', 'str', True), ('soTinChi', 'int', True)],
        select='SELECT maMonHoc, tenMonHoc, soTinChi FROM MonHoc',
        tim=['tenMonHoc'],
        thu_tu='tenMonHoc',
    ),
    'phong-hoc': dict(
        bang='PhongHoc',
        pk='maPhong',
        truong=[('tenPhong', 'str', True), ('sucChua', 'int', True)],
        select='SELECT maPhong, tenPhong, sucChua FROM PhongHoc',
        tim=['tenPhong'],
        thu_tu='tenPhong',
    ),
    'giang-vien': dict(
        bang='GiangVien',
        pk='maGiangVien',
        truong=[
            ('hoTen', 'str', True),
            ('email', 'str', False),
            ('soDienThoai', 'str', False),
            ('maKhoa', 'int', True),
        ],
        select=(
            'SELECT x.maGiangVien, x.hoTen, x.email, x.soDienThoai, '
            'x.maKhoa, k.tenKhoa, a.tenDangNhap '
            'FROM GiangVien x '
            'JOIN Khoa k ON k.maKhoa=x.maKhoa '
            'LEFT JOIN TaiKhoan a ON a.maTaiKhoan=x.maTaiKhoan'
        ),
        tim=['x.hoTen', 'x.email', 'k.tenKhoa'],
        thu_tu='x.hoTen',
        alias='x',
        vai_tro=GIANG_VIEN,
    ),
    'sinh-vien': dict(
        bang='SinhVien',
        pk='maSinhVien',
        # Ma so sinh vien do Phong dao tao nhap va duoc kiem tra duy nhat.
        truong=[
            ('maSoSinhVien', 'str', True),
            ('hoTen', 'str', True),
            ('email', 'str', False),
            ('soDienThoai', 'str', False),
            ('maLop', 'int', True),
        ],
        select=(
            'SELECT x.maSinhVien, x.maSoSinhVien, x.hoTen, x.email, '
            'x.soDienThoai, x.maLop, COALESCE(NULLIF(l.tenHienThi, \'\'), l.tenLop) AS tenLop, a.tenDangNhap '
            'FROM SinhVien x '
            'JOIN Lop l ON l.maLop=x.maLop '
            'LEFT JOIN TaiKhoan a ON a.maTaiKhoan=x.maTaiKhoan'
        ),
        tim=['x.maSoSinhVien', 'x.hoTen', 'x.email', 'l.tenLop', 'l.tenHienThi'],
        thu_tu='x.hoTen',
        alias='x',
        vai_tro=SINH_VIEN,
    ),
}


def cau_hinh(ten):
    if ten not in RESOURCES:
        raise NotFound('Danh muc khong ton tai')
    return RESOURCES[ten]


def _gia_tri(cfg, d):
    """Lay va kiem tra cac truong du lieu duoc phep nhap."""
    out = {}
    for ten, kieu, bat_buoc in cfg['truong']:
        v = d.get(ten)
        if isinstance(v, str):
            v = v.strip()
        if v in (None, ''):
            if bat_buoc:
                raise AppError(f'Thieu thong tin bat buoc: {ten}')
            out[ten] = None
            continue
        if kieu == 'int':
            try:
                v = int(v)
            except (ValueError, TypeError):
                raise AppError(f'Gia tri khong hop le: {ten}')
        out[ten] = v
    return out


def danh_sach(db, ten, q=None):
    cfg = cau_hinh(ten)
    sql, args = cfg['select'], []
    if q and q.strip():
        sql += ' WHERE ' + ' OR '.join(f'{cot} LIKE ?' for cot in cfg['tim'])
        args = [f'%{q.strip()}%'] * len(cfg['tim'])
    sql += f" ORDER BY {cfg['thu_tu']}"
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def _lay_mot(db, cfg, ma):
    cot = (
        f"{cfg.get('alias', cfg['bang'])}.{cfg['pk']}"
        if 'alias' in cfg else cfg['pk']
    )
    r = db.execute(cfg['select'] + f' WHERE {cot}=?', (ma,)).fetchone()
    if r is None:
        raise NotFound('Khong tim thay ban ghi')
    return dict(r)


def _thuc_thi(db, fn):
    try:
        return fn()
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if 'UNIQUE' in msg:
            raise Conflict('Gia tri da ton tai (trung ten hoac ma)')
        if 'FOREIGN KEY' in msg:
            raise AppError('Tham chieu khong hop le (khoa/lop khong ton tai)')
        raise AppError('Du lieu vi pham rang buoc')


def tao(db, ten, d):
    cfg = cau_hinh(ten)
    v = _gia_tri(cfg, d)

    def run():
        if 'vai_tro' in cfg and (d.get('tenDangNhap') or d.get('matKhau')):
            ma_tk = tai_khoan.tao_tai_khoan(
                db, d.get('tenDangNhap'), d.get('matKhau'), cfg['vai_tro']
            )
            v['maTaiKhoan'] = ma_tk

        cols = ', '.join(v)
        placeholders = ', '.join('?' for _ in v)
        cur = db.execute(
            f"INSERT INTO {cfg['bang']}({cols}) VALUES ({placeholders})",
            list(v.values()),
        )
        ma = cur.lastrowid

        db.commit()
        return ma

    try:
        ma = _thuc_thi(db, run)
    except AppError:
        db.rollback()
        raise
    return _lay_mot(db, cfg, ma)


def sua(db, ten, ma, d):
    cfg = cau_hinh(ten)
    _lay_mot(db, cfg, ma)
    v = _gia_tri(cfg, d)
    sets = ', '.join(f'{k}=?' for k in v)
    try:
        _thuc_thi(
            db,
            lambda: db.execute(
                f"UPDATE {cfg['bang']} SET {sets} WHERE {cfg['pk']}=?",
                list(v.values()) + [ma],
            ),
        )
        db.commit()
    except AppError:
        db.rollback()
        raise
    return _lay_mot(db, cfg, ma)


def xoa(db, ten, ma):
    """VR-07: tu choi xoa neu ban ghi dang duoc tham chieu."""
    cfg = cau_hinh(ten)
    _lay_mot(db, cfg, ma)
    try:
        db.execute(f"DELETE FROM {cfg['bang']} WHERE {cfg['pk']}=?", (ma,))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise Conflict(
            'Khong the xoa vi du lieu dang duoc su dung '
            '(vi du lop, giang vien hoac thoi khoa bieu lien quan)'
        )
