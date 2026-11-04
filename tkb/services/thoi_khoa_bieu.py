"""Dich vu nghiep vu thoi khoa bieu (ThoiKhoaBieuService trong bieu do tuan tu)."""
from datetime import date, timedelta
import sqlite3
from ..config import GIANG_VIEN, SINH_VIEN, PHONG_DAO_TAO, SO_TIET
from ..errors import AppError, Forbidden, NotFound, Conflict

SELECT = """
SELECT t.maTKB, t.ngayHoc, t.tietBatDau, t.tietKetThuc, t.hocKy, t.namHoc,
       t.maGiangVien, g.hoTen AS tenGiangVien,
       t.maMonHoc, m.tenMonHoc, m.soTinChi,
       t.maLop, l.tenLop, t.maPhong, p.tenPhong
FROM ThoiKhoaBieu t
JOIN GiangVien g ON g.maGiangVien = t.maGiangVien
JOIN MonHoc m    ON m.maMonHoc    = t.maMonHoc
JOIN Lop l       ON l.maLop       = t.maLop
JOIN PhongHoc p  ON p.maPhong     = t.maPhong
"""


def parse_ngay(s, ten='ngay'):
    try:
        return date.fromisoformat(str(s))
    except (ValueError, TypeError):
        raise AppError(f'{ten.capitalize()} khong hop le (dinh dang YYYY-MM-DD)')


def khoang_tuan(d):
    thu_hai = d - timedelta(days=d.weekday())
    return thu_hai, thu_hai + timedelta(days=6)


def _int(v, ten):
    try:
        return int(v)
    except (ValueError, TypeError):
        raise AppError(f'{ten} khong hop le')


def _gioi_han_quyen(user, where, args, p):
    """BR-06: giang vien chi xem lich cua minh, sinh vien chi xem lich lop minh."""
    if user['vaiTro'] == GIANG_VIEN:
        if p.get('maGiangVien') not in (None, '') and _int(p['maGiangVien'], 'Ma giang vien') != user.get('maGiangVien'):
            raise Forbidden('Ban chi duoc xem lich giang day cua chinh minh')
        where.append('t.maGiangVien = ?'); args.append(user.get('maGiangVien', -1))
    elif user['vaiTro'] == SINH_VIEN:
        if p.get('maLop') not in (None, '') and _int(p['maLop'], 'Ma lop') != user.get('maLop'):
            raise Forbidden('Ban chi duoc xem thoi khoa bieu cua lop minh')
        where.append('t.maLop = ?'); args.append(user.get('maLop', -1))


def danh_sach(db, user, p):
    """Xem theo tuan/ngay/lop/mon va tim kiem, loc (FR-05..FR-10, FR-12, FR-13)."""
    where, args = [], []
    _gioi_han_quyen(user, where, args, p)
    if p.get('tuan'):
        dau, cuoi = khoang_tuan(parse_ngay(p['tuan'], 'ngay trong tuan'))
        where.append('t.ngayHoc BETWEEN ? AND ?'); args += [dau.isoformat(), cuoi.isoformat()]
    if p.get('ngay'):
        where.append('t.ngayHoc = ?'); args.append(parse_ngay(p['ngay']).isoformat())
    if p.get('tuNgay'):
        where.append('t.ngayHoc >= ?'); args.append(parse_ngay(p['tuNgay'], 'tu ngay').isoformat())
    if p.get('denNgay'):
        where.append('t.ngayHoc <= ?'); args.append(parse_ngay(p['denNgay'], 'den ngay').isoformat())
    for key, col, ten in (('maLop', 't.maLop', 'Ma lop'), ('maMonHoc', 't.maMonHoc', 'Ma mon'),
                          ('maGiangVien', 't.maGiangVien', 'Ma giang vien'), ('maPhong', 't.maPhong', 'Ma phong')):
        if p.get(key) not in (None, ''):
            where.append(f'{col} = ?'); args.append(_int(p[key], ten))
    q = (p.get('q') or '').strip()
    if q:
        like = f'%{q}%'
        where.append('(m.tenMonHoc LIKE ? OR g.hoTen LIKE ? OR l.tenLop LIKE ? OR p.tenPhong LIKE ?)')
        args += [like] * 4
    sql = SELECT + (' WHERE ' + ' AND '.join(where) if where else '') + ' ORDER BY t.ngayHoc, t.tietBatDau, t.maTKB'
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def chi_tiet(db, user, ma_tkb):
    """FR-11. Tra 404 neu khong ton tai, 403 neu ngoai pham vi cua nguoi dung."""
    r = db.execute(SELECT + ' WHERE t.maTKB = ?', (ma_tkb,)).fetchone()
    if r is None:
        raise NotFound('Buoi hoc khong ton tai hoac da bi xoa')
    r = dict(r)
    if user['vaiTro'] == GIANG_VIEN and r['maGiangVien'] != user.get('maGiangVien'):
        raise Forbidden('Ban khong co quyen xem buoi hoc nay')
    if user['vaiTro'] == SINH_VIEN and r['maLop'] != user.get('maLop'):
        raise Forbidden('Ban khong co quyen xem buoi hoc nay')
    return r


# ---------------- Phong dao tao: tao/sua/xoa (FR-16) ----------------
def _chuan_hoa(db, d):
    ngay = parse_ngay(d.get('ngayHoc'), 'ngay hoc').isoformat()
    bd, kt = _int(d.get('tietBatDau'), 'Tiet bat dau'), _int(d.get('tietKetThuc'), 'Tiet ket thuc')
    if not (1 <= bd <= SO_TIET and 1 <= kt <= SO_TIET):
        raise AppError(f'Tiet hoc phai nam trong khoang 1 den {SO_TIET}')
    if bd > kt:
        raise AppError('Tiet bat dau khong duoc sau tiet ket thuc')
    out = {'ngayHoc': ngay, 'tietBatDau': bd, 'tietKetThuc': kt,
           'hocKy': (d.get('hocKy') or '').strip() or None, 'namHoc': (d.get('namHoc') or '').strip() or None}
    for key, bang, ten in (('maGiangVien', 'GiangVien', 'Giang vien'), ('maMonHoc', 'MonHoc', 'Mon hoc'),
                           ('maLop', 'Lop', 'Lop'), ('maPhong', 'PhongHoc', 'Phong hoc')):
        v = _int(d.get(key), ten)
        if db.execute(f'SELECT 1 FROM {bang} WHERE {key}=?', (v,)).fetchone() is None:
            raise AppError(f'{ten} khong ton tai')
        out[key] = v
    return out


def kiem_tra_trung_lich(db, v, bo_qua=None):
    """VR-04: khong trung giang vien, lop hoac phong cung ngay va khoang tiet giao nhau."""
    rows = db.execute(SELECT + ' WHERE t.ngayHoc=? AND t.tietBatDau<=? AND t.tietKetThuc>=? '
                               'AND (t.maGiangVien=? OR t.maLop=? OR t.maPhong=?) AND t.maTKB != ?',
                      (v['ngayHoc'], v['tietKetThuc'], v['tietBatDau'], v['maGiangVien'], v['maLop'], v['maPhong'],
                       bo_qua or -1)).fetchall()
    loi = []
    for r in rows:
        if r['maGiangVien'] == v['maGiangVien']:
            loi.append(f"Giang vien {r['tenGiangVien']} da co lich (tiet {r['tietBatDau']}-{r['tietKetThuc']}, lop {r['tenLop']})")
        if r['maLop'] == v['maLop']:
            loi.append(f"Lop {r['tenLop']} da co lich (tiet {r['tietBatDau']}-{r['tietKetThuc']}, mon {r['tenMonHoc']})")
        if r['maPhong'] == v['maPhong']:
            loi.append(f"Phong {r['tenPhong']} da duoc su dung (tiet {r['tietBatDau']}-{r['tietKetThuc']}, lop {r['tenLop']})")
    if loi:
        raise Conflict('Trung lich: ' + '; '.join(dict.fromkeys(loi)))


def tao(db, d):
    v = _chuan_hoa(db, d)
    kiem_tra_trung_lich(db, v)
    cur = db.execute('INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,hocKy,namHoc,maGiangVien,maMonHoc,maLop,maPhong) '
                     'VALUES (:ngayHoc,:tietBatDau,:tietKetThuc,:hocKy,:namHoc,:maGiangVien,:maMonHoc,:maLop,:maPhong)', v)
    db.commit()
    return dict(db.execute(SELECT + ' WHERE t.maTKB=?', (cur.lastrowid,)).fetchone())


def sua(db, ma_tkb, d):
    if db.execute('SELECT 1 FROM ThoiKhoaBieu WHERE maTKB=?', (ma_tkb,)).fetchone() is None:
        raise NotFound('Buoi hoc khong ton tai')
    v = _chuan_hoa(db, d)
    kiem_tra_trung_lich(db, v, bo_qua=ma_tkb)
    v['maTKB'] = ma_tkb
    db.execute('UPDATE ThoiKhoaBieu SET ngayHoc=:ngayHoc,tietBatDau=:tietBatDau,tietKetThuc=:tietKetThuc,hocKy=:hocKy,'
               'namHoc=:namHoc,maGiangVien=:maGiangVien,maMonHoc=:maMonHoc,maLop=:maLop,maPhong=:maPhong WHERE maTKB=:maTKB', v)
    db.commit()
    return dict(db.execute(SELECT + ' WHERE t.maTKB=?', (ma_tkb,)).fetchone())


def xoa(db, ma_tkb):
    cur = db.execute('DELETE FROM ThoiKhoaBieu WHERE maTKB=?', (ma_tkb,))
    if cur.rowcount == 0:
        raise NotFound('Buoi hoc khong ton tai')
    db.commit()


def thong_ke(db):
    """FR-24 (muc co ban): so buoi hoc theo giang vien, phong, lop."""
    def q(sql):
        return [dict(r) for r in db.execute(sql).fetchall()]
    return {
        'tongSoBuoi': db.execute('SELECT COUNT(*) FROM ThoiKhoaBieu').fetchone()[0],
        'theoGiangVien': q('SELECT g.hoTen AS ten, COUNT(t.maTKB) AS soBuoi FROM GiangVien g LEFT JOIN ThoiKhoaBieu t '
                           'ON t.maGiangVien=g.maGiangVien GROUP BY g.maGiangVien ORDER BY soBuoi DESC, ten'),
        'theoPhong': q('SELECT p.tenPhong AS ten, COUNT(t.maTKB) AS soBuoi FROM PhongHoc p LEFT JOIN ThoiKhoaBieu t '
                       'ON t.maPhong=p.maPhong GROUP BY p.maPhong ORDER BY soBuoi DESC, ten'),
        'theoLop': q('SELECT l.tenLop AS ten, COUNT(t.maTKB) AS soBuoi FROM Lop l LEFT JOIN ThoiKhoaBieu t '
                     'ON t.maLop=l.maLop GROUP BY l.maLop ORDER BY soBuoi DESC, ten'),
        'theoKhoa': q('SELECT k.tenKhoa AS ten, COUNT(DISTINCT g.maGiangVien) AS soGiangVien '
                      'FROM Khoa k LEFT JOIN GiangVien g ON g.maKhoa=k.maKhoa '
                      'GROUP BY k.maKhoa ORDER BY soGiangVien DESC, ten'),
        'theoMonHoc': q('SELECT m.tenMonHoc AS ten, COUNT(t.maTKB) AS soBuoi FROM MonHoc m '
                        'LEFT JOIN ThoiKhoaBieu t ON t.maMonHoc=m.maMonHoc '
                        'GROUP BY m.maMonHoc ORDER BY soBuoi DESC, ten'),
    }
