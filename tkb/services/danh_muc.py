"""Quan ly danh muc: khoa, lop, mon hoc, phong hoc, giang vien, sinh vien (FR-18..FR-23)."""
import sqlite3

from ..config import GIANG_VIEN, SINH_VIEN
from ..errors import AppError, Conflict, NotFound
from . import nguoi_dung
from ..migrations import suy_ra_nam_tuyen_sinh


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
            ('namTuyenSinh', 'int', False),
            ('maKhoa', 'int', True),
        ],
        select=(
            'SELECT x.maLop, COALESCE(NULLIF(x.tenHienThi, \'\'), x.tenLop) AS tenLop, x.khoaHoc, x.namTuyenSinh, '
            'x.maKhoa, k.tenKhoa '
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
    """q co the la chuoi tim kiem hoac dict tham so (voi sinh-vien: loc/sap xep/phan trang)."""
    p = q if isinstance(q, dict) else {'q': q}
    q = p.get('q')
    if ten == 'sinh-vien':
        return nguoi_dung.danh_sach_sv(db, p)
    if ten == 'giang-vien':
        return nguoi_dung.danh_sach_gv(db, q)
    if ten == 'khoa-tuyen-sinh':
        return nguoi_dung.khoa_tuyen_sinh(db)
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


def _chuan_lop(d, cu=None):
    """Lop: tu suy ra khoa tuyen sinh tu khoaHoc/ten lop neu chua nhap."""
    if d.get('namTuyenSinh') in (None, ''):
        nam = suy_ra_nam_tuyen_sinh(d.get('khoaHoc'), d.get('tenLop'))
        if nam is None and cu:
            nam = cu.get('namTuyenSinh')
        if nam is None:
            raise AppError('Thieu thong tin bat buoc: Khoa tuyen sinh (nam)')
        d = {**d, 'namTuyenSinh': nam}
    try:
        nam = int(d['namTuyenSinh'])
    except (TypeError, ValueError):
        raise AppError('Khoa tuyen sinh khong hop le')
    if not 2000 <= nam <= 2099:
        raise AppError('Khoa tuyen sinh phai tu 2000 den 2099')
    return d


def tao(db, ten, d):
    if ten == 'sinh-vien':
        return nguoi_dung.tao_sv(db, d)
    if ten == 'giang-vien':
        return nguoi_dung.tao_gv(db, d)
    cfg = cau_hinh(ten)
    if ten == 'lop':
        d = _chuan_lop(d)
    v = _gia_tri(cfg, d)

    def run():
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
    if ten == 'sinh-vien':
        return nguoi_dung.sua_sv(db, ma, d)
    if ten == 'giang-vien':
        return nguoi_dung.sua_gv(db, ma, d)
    cfg = cau_hinh(ten)
    cu = _lay_mot(db, cfg, ma)
    if ten == 'lop':
        d = _chuan_lop(d, cu)
        if int(d['namTuyenSinh']) != cu.get('namTuyenSinh') and db.execute(
                'SELECT 1 FROM SinhVien WHERE maLop=?', (ma,)).fetchone():
            raise AppError('Khong the doi khoa tuyen sinh cua lop da co sinh vien (ma sinh vien gan voi khoa)')
    v = _gia_tri(cfg, d)
    sets = ', '.join(f'{k}=?' for k in v)
    if ten == 'lop':
        # Form chi cho sua ten hien thi: neu lop co tenHienThi thi cap nhat no, giu nguyen ma lop goc.
        row = db.execute("SELECT tenHienThi FROM Lop WHERE maLop=?", (ma,)).fetchone()
        if row and row['tenHienThi']:
            v['tenHienThi'] = v.pop('tenLop')
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
    if ten == 'sinh-vien':
        return nguoi_dung.xoa_sv(db, ma)
    if ten == 'giang-vien':
        return nguoi_dung.xoa_gv(db, ma)
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
