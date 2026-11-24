"""Nang cap CSDL cu len cau truc moi (an toan, chay lai nhieu lan khong sao).

- Tu dong sao luu file CSDL truoc khi nang cap (instance/<ten>.bak-<thoi gian>).
- Them cot ngaySinh, namTuyenSinh, phaiDoiMatKhau... KHONG xoa du lieu, KHONG doi mat khau cu.
- Dung lai bang ThongBao (them loai/doi tuong/trang thai) va giu nguyen cac thong bao cu.
- Doi ma sinh vien cu (SV0001) sang dinh dang 4 chu so theo khoa (2401...), giu nguyen quan he.
"""
import os
import re
import shutil
import sqlite3
from datetime import datetime

PHIEN_BAN = 3


def suy_ra_nam_tuyen_sinh(khoa_hoc, ten_lop):
    """'CNTT K23' -> 2023; 'CT2301' -> 2023; khong suy ra duoc -> None."""
    m = re.search(r'\bK\s*(\d{2})\b', str(khoa_hoc or ''), re.I)
    if m:
        return 2000 + int(m[1])
    m = re.search(r'(\d{2})\d{2}$', str(ten_lop or ''))
    if m:
        return 2000 + int(m[1])
    return None


def _cot(con, bang):
    return {r[1] for r in con.execute(f'PRAGMA table_info({bang})')}


def _them_cot(con, bang, ten, kieu):
    if ten not in _cot(con, bang):
        con.execute(f'ALTER TABLE {bang} ADD COLUMN {ten} {kieu}')


def sao_luu(path):
    """Sao luu bang API backup cua SQLite (nhat quan ke ca khi dang mo). Tra ve duong dan."""
    dich = f"{path}.bak-{datetime.now():%Y%m%d-%H%M%S}"
    src, dst = sqlite3.connect(path), sqlite3.connect(dich)
    try:
        src.backup(dst)
    finally:
        dst.close(); src.close()
    return dich


def can_nang_cap(con):
    return con.execute('PRAGMA user_version').fetchone()[0] < PHIEN_BAN


def nang_cap(con, bao_cao=None):
    """con: ket noi isolation_level=None, foreign_keys=OFF. Tra ve dict bao cao."""
    bc = bao_cao if bao_cao is not None else {}
    con.execute('BEGIN IMMEDIATE')
    try:
        phien_ban_cu = con.execute('PRAGMA user_version').fetchone()[0]
        _them_cot(con, 'Lop', 'tenHienThi', 'TEXT')
        if 'maSoSinhVien' not in _cot(con, 'SinhVien'):   # CSDL rat cu
            con.execute('ALTER TABLE SinhVien ADD COLUMN maSoSinhVien TEXT')
            con.execute("UPDATE SinhVien SET maSoSinhVien='SV'||printf('%04d', maSinhVien)")
        for bang, ten, kieu in (
            ('TaiKhoan', 'hoTen', 'TEXT'), ('TaiKhoan', 'ngaySinh', 'TEXT'),
            ('TaiKhoan', 'phaiDoiMatKhau', 'INTEGER NOT NULL DEFAULT 0'),
            ('Lop', 'namTuyenSinh', 'INTEGER'),
            ('GiangVien', 'ngaySinh', 'TEXT'),
            ('SinhVien', 'ngaySinh', 'TEXT'), ('SinhVien', 'namTuyenSinh', 'INTEGER'),
        ):
            _them_cot(con, bang, ten, kieu)

        # Khoa tuyen sinh cua lop (suy ra tu khoaHoc / ten lop), roi cua sinh vien (lay tu lop).
        for ma, kh, ten in con.execute(
                'SELECT maLop, khoaHoc, tenLop FROM Lop WHERE namTuyenSinh IS NULL').fetchall():
            nam = suy_ra_nam_tuyen_sinh(kh, ten)
            if nam:
                con.execute('UPDATE Lop SET namTuyenSinh=? WHERE maLop=?', (nam, ma))
        con.execute('UPDATE SinhVien SET namTuyenSinh=(SELECT namTuyenSinh FROM Lop WHERE Lop.maLop=SinhVien.maLop) '
                    'WHERE namTuyenSinh IS NULL')
        bc['lopChuaXacDinhKhoa'] = [r[0] for r in con.execute('SELECT tenLop FROM Lop WHERE namTuyenSinh IS NULL')]

        _dung_lai_thong_bao(con, bc)
        _doi_ma_sinh_vien(con, bc)
        _rang_buoc(con)
        if phien_ban_cu == 2:
            _mat_khau_quy_tac_moi(con, bc)
        con.execute(f'PRAGMA user_version={PHIEN_BAN}')
        con.execute('COMMIT')
    except Exception:
        con.execute('ROLLBACK')
        raise
    return bc


def _dung_lai_thong_bao(con, bc):
    sql = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ThongBao'").fetchone()
    if sql and 'QUAN_TRONG' in sql[0] and 'doiTuong' in sql[0]:
        return
    # Quy trinh chuan cua SQLite: tao bang moi -> chep du lieu -> xoa bang cu -> doi ten bang moi.
    # (KHONG doi ten bang cu: SQLite se sua khoa ngoai cua ThongBaoDaDoc tro sang bang cu bi xoa.)
    con.execute("""CREATE TABLE ThongBao_moi (
      maThongBao INTEGER PRIMARY KEY AUTOINCREMENT,
      loai TEXT NOT NULL CHECK (loai IN ('CHUNG','NGHI','DAY_BU','DOI_PHONG','DOI_LICH','QUAN_TRONG')),
      tieuDe TEXT NOT NULL, noiDung TEXT NOT NULL,
      maTKB INTEGER REFERENCES ThoiKhoaBieu(maTKB) ON DELETE SET NULL,
      doiTuong TEXT NOT NULL DEFAULT 'TAT_CA'
        CHECK (doiTuong IN ('TAT_CA','TAT_CA_SV','TAT_CA_GV','LOP','GIANG_VIEN','LOP_VA_GV')),
      maLop INTEGER REFERENCES Lop(maLop) ON DELETE CASCADE,
      maGiangVien INTEGER REFERENCES GiangVien(maGiangVien) ON DELETE CASCADE,
      maNguoiGui INTEGER REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL,
      trangThai TEXT NOT NULL DEFAULT 'DA_GUI' CHECK (trangThai IN ('NHAP','DA_GUI')),
      ngayTao TEXT NOT NULL DEFAULT (datetime('now','localtime')),
      thoiGianGui TEXT, ngayCapNhat TEXT,
      CHECK (doiTuong NOT IN ('LOP','LOP_VA_GV') OR maLop IS NOT NULL),
      CHECK (doiTuong NOT IN ('GIANG_VIEN','LOP_VA_GV') OR maGiangVien IS NOT NULL))""")
    con.execute("""INSERT INTO ThongBao_moi(maThongBao,loai,tieuDe,noiDung,maTKB,doiTuong,maLop,maGiangVien,
                                         trangThai,ngayTao,thoiGianGui)
        SELECT maThongBao,loai,tieuDe,noiDung,maTKB,
               CASE WHEN maLop IS NOT NULL AND maGiangVien IS NOT NULL THEN 'LOP_VA_GV'
                    WHEN maLop IS NOT NULL THEN 'LOP'
                    WHEN maGiangVien IS NOT NULL THEN 'GIANG_VIEN' ELSE 'TAT_CA' END,
               maLop,maGiangVien,'DA_GUI',ngayTao,ngayTao FROM ThongBao""")
    bc['thongBaoDaChuyen'] = con.execute('SELECT COUNT(*) FROM ThongBao_moi').fetchone()[0]
    con.execute('DROP TABLE ThongBao')
    con.execute('ALTER TABLE ThongBao_moi RENAME TO ThongBao')
    con.execute('CREATE INDEX IF NOT EXISTS idx_thongbao_lop ON ThongBao(maLop, ngayTao)')
    con.execute('CREATE INDEX IF NOT EXISTS idx_thongbao_gv ON ThongBao(maGiangVien, ngayTao)')


def _doi_ma_sinh_vien(con, bc):
    """SV0001 -> 2201...: nam = khoa cua lop, so thu tu tiep sau ma 4 chu so da co trong khoa."""
    dung = re.compile(r'^\d{4}$')
    ma_da_co = {}
    for ma, nam in con.execute('SELECT maSoSinhVien, namTuyenSinh FROM SinhVien'):
        if nam and dung.match(ma or '') and int(ma[:2]) == nam % 100:
            ma_da_co[nam] = max(ma_da_co.get(nam, 0), int(ma[2:]))
    da_doi, giu_lai = 0, []
    for ma_sv, ma_so, nam in con.execute(
            'SELECT maSinhVien, maSoSinhVien, namTuyenSinh FROM SinhVien ORDER BY maSinhVien').fetchall():
        if dung.match(ma_so or '') and nam and int(ma_so[:2]) == nam % 100 and int(ma_so[2:]) >= 1:
            continue
        stt = ma_da_co.get(nam, 0) + 1 if nam else 100
        if not nam or stt > 99:
            giu_lai.append(ma_so)   # khong the cap ma dung dinh dang: giu ma cu, bao cao
            continue
        ma_da_co[nam] = stt
        con.execute('UPDATE SinhVien SET maSoSinhVien=? WHERE maSinhVien=?', (f'{nam % 100:02d}{stt:02d}', ma_sv))
        da_doi += 1
    bc['maSinhVienDaDoi'] = da_doi
    bc['maSinhVienGiuNguyen'] = giu_lai
    # Bo dem: khong thap hon so thu tu lon nhat dang ton tai.
    for nam, so in ma_da_co.items():
        con.execute('INSERT INTO BoDemMaSinhVien(namTuyenSinh, soCuoi) VALUES (?,?) '
                    'ON CONFLICT(namTuyenSinh) DO UPDATE SET soCuoi=MAX(soCuoi, excluded.soCuoi)', (nam, so))


def _rang_buoc(con):
    con.execute('CREATE INDEX IF NOT EXISTS idx_sinhvien_nam ON SinhVien(namTuyenSinh, maSoSinhVien)')
    con.execute('CREATE INDEX IF NOT EXISTS idx_sinhvien_lop ON SinhVien(maLop)')
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_sinhvien_maso ON SinhVien(maSoSinhVien)')
    dk = ("NEW.maSoSinhVien NOT GLOB '[0-9][0-9][0-9][0-9]' OR NEW.maSoSinhVien GLOB '*00' "
          "OR (NEW.namTuyenSinh IS NOT NULL AND substr(NEW.maSoSinhVien,1,2) <> printf('%02d', NEW.namTuyenSinh % 100))")
    msg = "RAISE(ABORT, 'Ma sinh vien sai dinh dang (YYNN: 2 so cuoi nam tuyen sinh + so thu tu 01-99)')"
    con.execute('DROP TRIGGER IF EXISTS trg_sv_ma_insert')
    con.execute('DROP TRIGGER IF EXISTS trg_sv_ma_update')
    con.execute(f'CREATE TRIGGER trg_sv_ma_insert BEFORE INSERT ON SinhVien WHEN {dk} BEGIN SELECT {msg}; END')
    con.execute(f'CREATE TRIGGER trg_sv_ma_update BEFORE UPDATE OF maSoSinhVien ON SinhVien WHEN {dk} BEGIN SELECT {msg}; END')


def _mat_khau_quy_tac_moi(con, bc):
    """v2 -> v3: mat khau ban dau doi sang dang khong dau, khong cach (Nguyenvanan15032004).
    CHI dat lai tai khoan con dung mat khau ban dau (phaiDoiMatKhau=1, chua tu doi)."""
    from werkzeug.security import generate_password_hash
    from .services import dinh_danh
    nguon = con.execute("""SELECT t.maTaiKhoan, s.hoTen, s.ngaySinh FROM TaiKhoan t JOIN SinhVien s ON s.maTaiKhoan=t.maTaiKhoan
                           WHERE t.phaiDoiMatKhau=1 AND s.ngaySinh IS NOT NULL
                           UNION ALL SELECT t.maTaiKhoan, g.hoTen, g.ngaySinh FROM TaiKhoan t JOIN GiangVien g ON g.maTaiKhoan=t.maTaiKhoan
                           WHERE t.phaiDoiMatKhau=1 AND g.ngaySinh IS NOT NULL
                           UNION ALL SELECT maTaiKhoan, hoTen, ngaySinh FROM TaiKhoan
                           WHERE phaiDoiMatKhau=1 AND hoTen IS NOT NULL AND ngaySinh IS NOT NULL""").fetchall()
    for ma, ho_ten, ngay in nguon:
        mk = dinh_danh.tao_mat_khau(ho_ten, ngay)
        con.execute('UPDATE TaiKhoan SET matKhau=? WHERE maTaiKhoan=?', (generate_password_hash(mk), ma))
    bc['matKhauDatLaiTheoQuyTacMoi'] = len(nguon)
