"""Sinh vien va giang vien: tao/sua/xoa, ma sinh vien theo khoa, tai khoan theo quy tac."""
import sqlite3

from ..config import GIANG_VIEN, SINH_VIEN, SO_SV_TOI_DA_MOI_KHOA
from ..errors import AppError, Conflict, NotFound
from ..migrations import suy_ra_nam_tuyen_sinh
from . import dinh_danh, tai_khoan

TEN_LOP = "COALESCE(NULLIF(l.tenHienThi,''), l.tenLop)"
SELECT_SV = f"""SELECT x.maSinhVien, x.maSoSinhVien, x.hoTen, x.ngaySinh, x.email, x.soDienThoai,
  x.namTuyenSinh, x.maLop, {TEN_LOP} AS tenLop, k.tenKhoa AS tenNganh,
  a.tenDangNhap, (x.maTaiKhoan IS NOT NULL) AS coTaiKhoan
  FROM SinhVien x JOIN Lop l ON l.maLop=x.maLop JOIN Khoa k ON k.maKhoa=l.maKhoa
  LEFT JOIN TaiKhoan a ON a.maTaiKhoan=x.maTaiKhoan"""
SELECT_GV = """SELECT x.maGiangVien, x.hoTen, x.ngaySinh, x.email, x.soDienThoai, x.maKhoa, k.tenKhoa,
  a.tenDangNhap, (x.maTaiKhoan IS NOT NULL) AS coTaiKhoan
  FROM GiangVien x JOIN Khoa k ON k.maKhoa=x.maKhoa LEFT JOIN TaiKhoan a ON a.maTaiKhoan=x.maTaiKhoan"""


# ---------------- tien ich ----------------
def _str(d, k, toi_da=200):
    v = d.get(k)
    v = v.strip() if isinstance(v, str) else v
    if v is not None and len(str(v)) > toi_da:
        raise AppError(f'{k} qua dai')
    return v or None


def _int(v, ten):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise AppError(f'{ten} khong hop le')


def _ghi(db):
    """Mo giao dich ghi (khoa CSDL) de cap ma tuan tu, khong trung khi nhieu nguoi cung them."""
    if db.in_transaction:
        db.commit()
    db.execute('BEGIN IMMEDIATE')


def _lop(db, ma_lop):
    r = db.execute('SELECT maLop, namTuyenSinh FROM Lop WHERE maLop=?', (ma_lop,)).fetchone()
    if r is None:
        raise AppError('Lop khong ton tai')
    if r['namTuyenSinh'] is None:
        raise AppError('Lop chua co khoa tuyen sinh. Hay cap nhat nam tuyen sinh cho lop truoc.')
    return r


def cap_ma_sinh_vien(db, nam):
    """Cap ma ke tiep cua khoa `nam`. Goi TRONG giao dich BEGIN IMMEDIATE. Ma da xoa khong duoc cap lai."""
    nam = int(nam)
    if not 2000 <= nam <= 2099:
        raise AppError('Khoa tuyen sinh phai tu 2000 den 2099 de tao ma 4 chu so')
    yy = f'{nam % 100:02d}'
    dang_co = db.execute("SELECT COALESCE(MAX(CAST(substr(maSoSinhVien,3) AS INTEGER)),0) FROM SinhVien "
                         "WHERE maSoSinhVien GLOB ? ", (yy + '[0-9][0-9]',)).fetchone()[0]
    da_cap = db.execute('SELECT soCuoi FROM BoDemMaSinhVien WHERE namTuyenSinh=?', (nam,)).fetchone()
    stt = max(dang_co, da_cap[0] if da_cap else 0) + 1
    if stt > SO_SV_TOI_DA_MOI_KHOA:
        raise Conflict(f'Khoa {nam} da cap het {SO_SV_TOI_DA_MOI_KHOA} ma ({yy}01-{yy}{SO_SV_TOI_DA_MOI_KHOA}). '
                       'Khong the tao ma 4 chu so hop le. De xuat: mo rong ma sang 5 chu so (YYNNN, toi da 999 '
                       'sinh vien/khoa) hoac tach dot tuyen sinh; can Phong Dao tao quyet dinh truoc khi doi dinh dang.')
    db.execute('INSERT INTO BoDemMaSinhVien(namTuyenSinh, soCuoi) VALUES (?,?) '
               'ON CONFLICT(namTuyenSinh) DO UPDATE SET soCuoi=excluded.soCuoi', (nam, stt))
    return f'{yy}{stt:02d}'


def _tai_khoan_moi(db, ho_ten, ngay, vai_tro, d):
    return tai_khoan.tao_theo_quy_tac(db, ho_ten, ngay, vai_tro, bool(d.get('chapNhanHauTo')))


def _bao_loi_rang_buoc(e):
    m = str(e)
    if 'UNIQUE' in m:
        return Conflict('Gia tri da ton tai (trung ma hoac tai khoan)')
    if 'FOREIGN KEY' in m:
        return AppError('Tham chieu khong hop le')
    return AppError(m.replace('constraint failed: ', '') if 'Ma sinh vien' in m else 'Du lieu vi pham rang buoc')


# ---------------- sinh vien ----------------
def _sv_theo_ma(db, ma):
    r = db.execute(SELECT_SV + ' WHERE x.maSinhVien=?', (ma,)).fetchone()
    if r is None:
        raise NotFound('Khong tim thay ban ghi')
    return dict(r)


def _sv_dong(r):
    r['coTaiKhoan'] = bool(r['coTaiKhoan'])
    return r


def danh_sach_sv(db, p):
    """Loc: q (ma/ho ten/email/lop), namTuyenSinh, maLop. Sap xep SQL: sapXep=maso|hoten, thuTu=tang|giam.
    Co `trang` thi tra {items, tong, ...}, khong thi tra danh sach day du."""
    where, args = [], []
    q = (p.get('q') or '').strip()
    if q and q.isdigit() and len(q) <= 4:     # tim theo ma sinh vien: khop dau ma (26 -> ca khoa 2026; 2601 -> dung 1 ma)
        where.append('x.maSoSinhVien LIKE ?'); args.append(q + '%')
    elif q:
        where.append('(x.maSoSinhVien LIKE ? OR x.hoTen LIKE ? OR x.email LIKE ? OR l.tenLop LIKE ? OR l.tenHienThi LIKE ? '
                     'OR a.tenDangNhap LIKE ?)')
        args += [f'%{q}%'] * 6
    if p.get('namTuyenSinh') not in (None, ''):
        where.append('x.namTuyenSinh = ?'); args.append(_int(p['namTuyenSinh'], 'Khoa tuyen sinh'))
    if p.get('maLop') not in (None, ''):
        where.append('x.maLop = ?'); args.append(_int(p['maLop'], 'Lop'))
    chieu = 'DESC' if str(p.get('thuTu', '')).lower() in ('giam', 'desc') else 'ASC'
    cot = 'x.hoTen' if p.get('sapXep') == 'hoten' else 'x.maSoSinhVien'
    sql = SELECT_SV + (' WHERE ' + ' AND '.join(where) if where else '')
    order = f' ORDER BY {cot} {chieu}, x.maSinhVien {chieu}'
    if p.get('trang') in (None, ''):
        return [_sv_dong(dict(r)) for r in db.execute(sql + order, args)]
    trang = max(1, _int(p['trang'], 'Trang'))
    so_dong = min(200, max(1, _int(p.get('soDong') or 25, 'So dong')))
    tong = db.execute('SELECT COUNT(*) FROM (' + sql + ')', args).fetchone()[0]
    ds = db.execute(sql + order + ' LIMIT ? OFFSET ?', args + [so_dong, (trang - 1) * so_dong]).fetchall()
    return {'items': [_sv_dong(dict(r)) for r in ds], 'tong': tong, 'trang': trang, 'soDong': so_dong,
            'tongTrang': max(1, -(-tong // so_dong))}


def tao_sv(db, d):
    ho_ten = dinh_danh.chuan_hoa_ho_ten(d.get('hoTen'))
    if d.get('ngaySinh') in (None, ''):
        raise AppError('Thieu thong tin bat buoc: Ngay sinh (can de tao tai khoan)')
    ngay = dinh_danh.parse_ngay_sinh(d.get('ngaySinh'))
    lop = _lop(db, _int(d.get('maLop'), 'Lop'))
    nam = lop['namTuyenSinh']
    if d.get('namTuyenSinh') not in (None, '') and _int(d['namTuyenSinh'], 'Khoa tuyen sinh') != nam:
        raise AppError(f'Lop da chon thuoc khoa {nam}, khong khop khoa tuyen sinh da nhap')
    _ghi(db)
    try:
        ma_tk, ten_dn = _tai_khoan_moi(db, ho_ten, ngay, SINH_VIEN, d)
        ma_so = cap_ma_sinh_vien(db, nam)
        cur = db.execute('INSERT INTO SinhVien(maSoSinhVien,hoTen,ngaySinh,email,soDienThoai,namTuyenSinh,maLop,maTaiKhoan) '
                         'VALUES (?,?,?,?,?,?,?,?)',
                         (ma_so, ho_ten, ngay.isoformat(), _str(d, 'email'), _str(d, 'soDienThoai', 20), nam,
                          lop['maLop'], ma_tk))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback(); raise _bao_loi_rang_buoc(e)
    except Exception:
        db.rollback(); raise
    return _sv_dong(_sv_theo_ma(db, cur.lastrowid))


def sua_sv(db, ma, d):
    cu = _sv_theo_ma(db, ma)
    ho_ten = dinh_danh.chuan_hoa_ho_ten(d.get('hoTen'))
    ngay = cu['ngaySinh']
    if d.get('ngaySinh') not in (None, ''):
        ngay = dinh_danh.parse_ngay_sinh(d['ngaySinh']).isoformat()
    ma_lop = _int(d.get('maLop') or cu['maLop'], 'Lop')
    lop = _lop(db, ma_lop)
    if lop['namTuyenSinh'] != cu['namTuyenSinh']:
        raise AppError('Khong the chuyen sinh vien sang lop thuoc khoa khac (ma sinh vien gan voi khoa tuyen sinh)')
    try:
        # Ma sinh vien, ten dang nhap va mat khau KHONG doi khi sua thong tin ca nhan.
        db.execute('UPDATE SinhVien SET hoTen=?, ngaySinh=?, email=?, soDienThoai=?, maLop=? WHERE maSinhVien=?',
                   (ho_ten, ngay, _str(d, 'email'), _str(d, 'soDienThoai', 20), ma_lop, ma))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback(); raise _bao_loi_rang_buoc(e)
    return _sv_dong(_sv_theo_ma(db, ma))


def xoa_sv(db, ma):
    cu = db.execute('SELECT maTaiKhoan FROM SinhVien WHERE maSinhVien=?', (ma,)).fetchone()
    if cu is None:
        raise NotFound('Khong tim thay ban ghi')
    try:
        db.execute('DELETE FROM SinhVien WHERE maSinhVien=?', (ma,))
        if cu['maTaiKhoan']:   # khong de lai tai khoan mo coi
            db.execute('DELETE FROM TaiKhoan WHERE maTaiKhoan=? AND vaiTro=?', (cu['maTaiKhoan'], SINH_VIEN))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback(); raise Conflict('Khong the xoa sinh vien nay vi du lieu dang duoc su dung')


# ---------------- giang vien ----------------
def _gv_theo_ma(db, ma):
    r = db.execute(SELECT_GV + ' WHERE x.maGiangVien=?', (ma,)).fetchone()
    if r is None:
        raise NotFound('Khong tim thay ban ghi')
    r = dict(r); r['coTaiKhoan'] = bool(r['coTaiKhoan'])
    return r


def danh_sach_gv(db, q=None):
    sql, args = SELECT_GV, []
    if q and q.strip():
        sql += ' WHERE x.hoTen LIKE ? OR x.email LIKE ? OR k.tenKhoa LIKE ? OR a.tenDangNhap LIKE ?'
        args = [f'%{q.strip()}%'] * 4
    out = []
    for r in db.execute(sql + ' ORDER BY x.hoTen, x.maGiangVien', args):
        r = dict(r); r['coTaiKhoan'] = bool(r['coTaiKhoan']); out.append(r)
    return out


def tao_gv(db, d):
    ho_ten = dinh_danh.chuan_hoa_ho_ten(d.get('hoTen'))
    if d.get('ngaySinh') in (None, ''):
        raise AppError('Thieu thong tin bat buoc: Ngay sinh (can de tao tai khoan)')
    ngay = dinh_danh.parse_ngay_sinh(d.get('ngaySinh'))
    ma_khoa = _int(d.get('maKhoa'), 'Khoa')
    _ghi(db)
    try:
        ma_tk, _ = _tai_khoan_moi(db, ho_ten, ngay, GIANG_VIEN, d)
        cur = db.execute('INSERT INTO GiangVien(hoTen,ngaySinh,email,soDienThoai,maKhoa,maTaiKhoan) VALUES (?,?,?,?,?,?)',
                         (ho_ten, ngay.isoformat(), _str(d, 'email'), _str(d, 'soDienThoai', 20), ma_khoa, ma_tk))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback(); raise _bao_loi_rang_buoc(e)
    except Exception:
        db.rollback(); raise
    return _gv_theo_ma(db, cur.lastrowid)


def sua_gv(db, ma, d):
    cu = _gv_theo_ma(db, ma)
    ho_ten = dinh_danh.chuan_hoa_ho_ten(d.get('hoTen'))
    ngay = cu['ngaySinh']
    if d.get('ngaySinh') not in (None, ''):
        ngay = dinh_danh.parse_ngay_sinh(d['ngaySinh']).isoformat()
    try:
        db.execute('UPDATE GiangVien SET hoTen=?, ngaySinh=?, email=?, soDienThoai=?, maKhoa=? WHERE maGiangVien=?',
                   (ho_ten, ngay, _str(d, 'email'), _str(d, 'soDienThoai', 20), _int(d.get('maKhoa') or cu['maKhoa'], 'Khoa'), ma))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback(); raise _bao_loi_rang_buoc(e)
    return _gv_theo_ma(db, ma)


def xoa_gv(db, ma):
    cu = db.execute('SELECT maTaiKhoan FROM GiangVien WHERE maGiangVien=?', (ma,)).fetchone()
    if cu is None:
        raise NotFound('Khong tim thay ban ghi')
    try:
        db.execute('DELETE FROM GiangVien WHERE maGiangVien=?', (ma,))
        if cu['maTaiKhoan']:
            db.execute('DELETE FROM TaiKhoan WHERE maTaiKhoan=? AND vaiTro=?', (cu['maTaiKhoan'], GIANG_VIEN))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise Conflict('Khong the xoa vi du lieu dang duoc su dung (vi du thoi khoa bieu lien quan)')


# ---------------- cap tai khoan theo quy tac ----------------
def cap_tai_khoan(db, loai, ma, d):
    """Cap tai khoan theo quy tac cho nguoi chua co tai khoan. Voi nguoi da co tai khoan cu (vi du sv1, gv1)
    chi doi sang quy tac moi khi PDT xac nhan ro rang (xacNhanDoi=true); khi do mat khau duoc dat lai."""
    sv = loai == 'sinh-vien'
    r = _sv_theo_ma(db, ma) if sv else _gv_theo_ma(db, ma)
    if not r['ngaySinh']:
        raise AppError('Chua co ngay sinh. Hay cap nhat ngay sinh truoc khi cap tai khoan.')
    vai_tro = SINH_VIEN if sv else GIANG_VIEN
    bang, pk = ('SinhVien', 'maSinhVien') if sv else ('GiangVien', 'maGiangVien')
    if r['coTaiKhoan'] and not d.get('xacNhanDoi'):
        raise Conflict('Da co tai khoan. Muon doi sang ten dang nhap/mat khau theo quy tac, hay xac nhan '
                       '(mat khau cu se bi thay bang mat khau ban dau).')
    _ghi(db)
    try:
        cu = db.execute(f'SELECT maTaiKhoan FROM {bang} WHERE {pk}=?', (ma,)).fetchone()['maTaiKhoan']
        if cu:   # tai khoan cu: doi tai cho (giu maTaiKhoan, trang thai da doc...) bang CUNG ham voi tai khoan moi
            ten, _, goc, n = tai_khoan.thong_tin_theo_quy_tac(db, r['hoTen'], r['ngaySinh'], bo_qua_ma_tk=cu)
            if ten != goc and not d.get('chapNhanHauTo'):
                e = Conflict(f'Tên đăng nhập "{goc}" đã tồn tại (trùng họ tên và ngày sinh). '
                             f'Đề xuất dùng "{ten}" (thêm hậu tố _{n}); mật khẩu ban đầu vẫn theo quy tắc chung.')
                e.goi_y = {'tenDangNhapDeXuat': ten, 'tenDangNhapGoc': goc}
                raise e
            tai_khoan.chuan_hoa_theo_quy_tac(db, cu, r['hoTen'], r['ngaySinh'])
        else:
            ma_tk, _ = _tai_khoan_moi(db, r['hoTen'], r['ngaySinh'], vai_tro, d)
            db.execute(f'UPDATE {bang} SET maTaiKhoan=? WHERE {pk}=?', (ma_tk, ma))
        db.commit()
    except Exception:
        db.rollback(); raise
    return _sv_dong(_sv_theo_ma(db, ma)) if sv else _gv_theo_ma(db, ma)


# ---------------- tong quan khoa tuyen sinh ----------------
def khoa_tuyen_sinh(db):
    rows = db.execute("""SELECT n.nam AS namTuyenSinh,
        (SELECT COUNT(*) FROM Lop WHERE namTuyenSinh=n.nam) AS soLop,
        (SELECT COUNT(*) FROM SinhVien WHERE namTuyenSinh=n.nam) AS soSinhVien,
        COALESCE((SELECT soCuoi FROM BoDemMaSinhVien WHERE namTuyenSinh=n.nam),0) AS soDaCap
        FROM (SELECT namTuyenSinh AS nam FROM Lop WHERE namTuyenSinh IS NOT NULL
              UNION SELECT namTuyenSinh FROM SinhVien WHERE namTuyenSinh IS NOT NULL) n ORDER BY n.nam""").fetchall()
    out = []
    for r in rows:
        r = dict(r); yy = f"{r['namTuyenSinh'] % 100:02d}"
        r['tenKhoa'] = f"Khóa {r['namTuyenSinh']}"
        r['conLai'] = max(0, SO_SV_TOI_DA_MOI_KHOA - r['soDaCap'])
        r['maDaCapDen'] = f"{yy}{r['soDaCap']:02d}" if r['soDaCap'] else '—'
        out.append(r)
    return out
