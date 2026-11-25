"""Kiem thu nang cap CSDL cu (cau truc truoc khi them 4 khoa / thong bao moi / dang nhap theo quy tac)."""
import glob
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from tkb.db import init_db

SCHEMA_CU = """
CREATE TABLE TaiKhoan (maTaiKhoan INTEGER PRIMARY KEY AUTOINCREMENT, tenDangNhap TEXT NOT NULL UNIQUE, matKhau TEXT NOT NULL,
  vaiTro TEXT NOT NULL CHECK (vaiTro IN ('GIANG_VIEN','SINH_VIEN','PHONG_DAO_TAO')));
CREATE TABLE Khoa (maKhoa INTEGER PRIMARY KEY AUTOINCREMENT, tenKhoa TEXT NOT NULL UNIQUE);
CREATE TABLE Lop (maLop INTEGER PRIMARY KEY AUTOINCREMENT, tenLop TEXT NOT NULL UNIQUE, tenHienThi TEXT, khoaHoc TEXT,
  maKhoa INTEGER NOT NULL REFERENCES Khoa(maKhoa));
CREATE TABLE GiangVien (maGiangVien INTEGER PRIMARY KEY AUTOINCREMENT, hoTen TEXT NOT NULL, email TEXT, soDienThoai TEXT,
  maKhoa INTEGER NOT NULL REFERENCES Khoa(maKhoa), maTaiKhoan INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL);
CREATE TABLE SinhVien (maSinhVien INTEGER PRIMARY KEY AUTOINCREMENT, maSoSinhVien TEXT NOT NULL UNIQUE, hoTen TEXT NOT NULL,
  email TEXT, soDienThoai TEXT, maLop INTEGER NOT NULL REFERENCES Lop(maLop),
  maTaiKhoan INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL);
CREATE TABLE MonHoc (maMonHoc INTEGER PRIMARY KEY AUTOINCREMENT, tenMonHoc TEXT NOT NULL UNIQUE, soTinChi INTEGER NOT NULL);
CREATE TABLE PhongHoc (maPhong INTEGER PRIMARY KEY AUTOINCREMENT, tenPhong TEXT NOT NULL UNIQUE, sucChua INTEGER NOT NULL);
CREATE TABLE ThoiKhoaBieu (maTKB INTEGER PRIMARY KEY AUTOINCREMENT, ngayHoc TEXT NOT NULL, tietBatDau INTEGER NOT NULL,
  tietKetThuc INTEGER NOT NULL, hocKy TEXT, namHoc TEXT, maGiangVien INTEGER NOT NULL REFERENCES GiangVien(maGiangVien),
  maMonHoc INTEGER NOT NULL REFERENCES MonHoc(maMonHoc), maLop INTEGER NOT NULL REFERENCES Lop(maLop),
  maPhong INTEGER NOT NULL REFERENCES PhongHoc(maPhong));
CREATE TABLE ThongBao (maThongBao INTEGER PRIMARY KEY AUTOINCREMENT,
  loai TEXT NOT NULL CHECK (loai IN ('NGHI','DAY_BU','DOI_PHONG','CHUNG')), tieuDe TEXT NOT NULL, noiDung TEXT NOT NULL,
  maTKB INTEGER REFERENCES ThoiKhoaBieu(maTKB) ON DELETE SET NULL, maLop INTEGER REFERENCES Lop(maLop) ON DELETE CASCADE,
  maGiangVien INTEGER REFERENCES GiangVien(maGiangVien) ON DELETE CASCADE,
  ngayTao TEXT NOT NULL DEFAULT (datetime('now','localtime')));
"""


class TestNangCapCsdlCu(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.p = os.path.join(self.d, 'tkb.sqlite3')
        c = sqlite3.connect(self.p)
        c.executescript(SCHEMA_CU)
        h = generate_password_hash('sv123')
        c.executemany('INSERT INTO TaiKhoan(tenDangNhap,matKhau,vaiTro) VALUES (?,?,?)',
                      [('pdt', h, 'PHONG_DAO_TAO'), ('gv1', h, 'GIANG_VIEN'), ('sv1', h, 'SINH_VIEN'), ('sv2', h, 'SINH_VIEN'),
                       ('sv3', h, 'SINH_VIEN')])
        c.execute("INSERT INTO Khoa(tenKhoa) VALUES ('CNTT')")
        c.execute("INSERT INTO Lop(tenLop,tenHienThi,khoaHoc,maKhoa) VALUES ('CT2201','CNTT 1','CNTT K22',1)")
        c.execute("INSERT INTO Lop(tenLop,tenHienThi,khoaHoc,maKhoa) VALUES ('CT2301','CNTT 3','CNTT K23',1)")
        c.execute("INSERT INTO Lop(tenLop,khoaHoc,maKhoa) VALUES ('LOPLA',NULL,1)")          # khong suy ra duoc khoa
        c.execute("INSERT INTO GiangVien(hoTen,maKhoa,maTaiKhoan) VALUES ('Nguyen Van An',1,2)")
        c.execute("INSERT INTO MonHoc(tenMonHoc,soTinChi) VALUES ('Web',3)")
        c.execute("INSERT INTO PhongHoc(tenPhong,sucChua) VALUES ('P1',40)")
        c.executemany('INSERT INTO SinhVien(maSoSinhVien,hoTen,maLop,maTaiKhoan) VALUES (?,?,?,?)',
                      [('SV0001', 'A', 1, 3), ('SV0002', 'B', 2, 4), ('SV0003', 'C', 3, 5), ('SV0004', 'D', 1, None)])
        c.execute("INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,maGiangVien,maMonHoc,maLop,maPhong) VALUES ('2026-11-02',1,3,1,1,1,1)")
        c.execute("INSERT INTO ThongBao(loai,tieuDe,noiDung) VALUES ('CHUNG','Nghi le','ND')")
        c.execute("INSERT INTO ThongBao(loai,tieuDe,noiDung,maTKB,maLop,maGiangVien) VALUES ('NGHI','Nghi','ND',1,1,1)")
        c.commit(); c.close()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_nang_cap_giu_du_lieu_doi_ma_va_sao_luu(self):
        init_db(self.p)
        c = sqlite3.connect(self.p); c.row_factory = sqlite3.Row
        self.assertEqual(len(glob.glob(self.p + '.bak-*')), 1)                      # co sao luu truoc khi nang cap
        bak = sqlite3.connect(glob.glob(self.p + '.bak-*')[0])
        self.assertEqual(bak.execute("SELECT maSoSinhVien FROM SinhVien WHERE maSinhVien=1").fetchone()[0], 'SV0001')
        # ma sinh vien: 4 chu so theo khoa cua lop; quan he giu nguyen
        ma = {r['maSinhVien']: r['maSoSinhVien'] for r in c.execute('SELECT * FROM SinhVien')}
        self.assertEqual(ma, {1: '2201', 2: '2301', 3: 'SV0003', 4: '2202'})       # lop khong ro khoa: giu ma cu
        self.assertEqual(c.execute('SELECT maLop, maTaiKhoan FROM SinhVien WHERE maSinhVien=1').fetchone()[:], (1, 3))
        self.assertEqual(c.execute('SELECT count(*) FROM TaiKhoan').fetchone()[0], 5)
        self.assertEqual(c.execute('SELECT count(*) FROM ThoiKhoaBieu').fetchone()[0], 1)
        self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(c.execute("SELECT namTuyenSinh FROM Lop ORDER BY maLop").fetchall()[0][0], 2022)
        self.assertEqual({r[0]: r[1] for r in c.execute('SELECT namTuyenSinh, soCuoi FROM BoDemMaSinhVien')}, {2022: 2, 2023: 1})

    def test_thong_bao_cu_duoc_giu_va_gan_doi_tuong(self):
        init_db(self.p)
        c = sqlite3.connect(self.p); c.row_factory = sqlite3.Row
        r = {x['tieuDe']: x for x in c.execute('SELECT * FROM ThongBao')}
        self.assertEqual((r['Nghi le']['doiTuong'], r['Nghi le']['trangThai']), ('TAT_CA', 'DA_GUI'))
        self.assertEqual((r['Nghi']['doiTuong'], r['Nghi']['maLop'], r['Nghi']['maGiangVien']), ('LOP_VA_GV', 1, 1))
        self.assertIsNotNone(r['Nghi']['thoiGianGui'])
        c.execute("INSERT INTO ThongBao(loai,tieuDe,noiDung) VALUES ('QUAN_TRONG','x','y')")   # loai moi duoc chap nhan

    def test_khoa_ngoai_da_doc_dung_va_danh_dau_doc_duoc_sau_nang_cap(self):
        # loi that da gap tren CSDL cu: doi ten bang ThongBao lam ThongBaoDaDoc tro sang bang da xoa
        init_db(self.p)
        c = sqlite3.connect(self.p)
        sql = c.execute("SELECT sql FROM sqlite_master WHERE name='ThongBaoDaDoc'").fetchone()[0]
        self.assertNotIn('_cu', sql); self.assertNotIn('_moi', sql)
        self.assertEqual(c.execute("SELECT name FROM sqlite_master WHERE name LIKE 'ThongBao%' ORDER BY name").fetchall(),
                         [('ThongBao',), ('ThongBaoDaDoc',)])
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('INSERT INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) VALUES (1,3)')
        self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
        c.execute('DELETE FROM ThongBao WHERE maThongBao=1')                       # xoa thong bao -> xoa luon trang thai doc
        self.assertEqual(c.execute('SELECT count(*) FROM ThongBaoDaDoc').fetchone()[0], 0)

    def test_api_doc_thong_bao_sau_nang_cap(self):
        from app import create_app
        c = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True}).test_client()
        ten, mk = self._tk_quy_tac('SinhVien', 1)
        c.post('/api/dang-nhap', json={'tenDangNhap': ten, 'matKhau': mk})
        self.assertEqual(c.get('/api/thong-bao/so-chua-doc').json['soChuaDoc'], 2)
        self.assertEqual(c.post('/api/thong-bao/1/da-doc').status_code, 200)
        self.assertEqual(c.get('/api/thong-bao/so-chua-doc').json['soChuaDoc'], 1)
        self.assertEqual(c.post('/api/thong-bao/da-doc-tat-ca').json['soChuaDoc'], 0)

    def test_v2_len_v3_dat_lai_mat_khau_ban_dau_chua_doi_sang_quy_tac_moi(self):
        init_db(self.p)
        c = sqlite3.connect(self.p)
        c.execute("UPDATE SinhVien SET hoTen='Nguy\u1ec5n V\u0103n An', ngaySinh='2004-03-15' WHERE maSinhVien=1")
        c.execute("UPDATE SinhVien SET hoTen='Tr\u1ea7n Th\u1ecb B', ngaySinh='2004-01-02' WHERE maSinhVien=2")
        c.execute("UPDATE TaiKhoan SET tenDangNhap='nguyenvanan15032004', phaiDoiMatKhau=1, matKhau=? WHERE maTaiKhoan=3",
                  (generate_password_hash('Nguy\u1ec5n v\u0103n an15032004'),))           # mat khau ban dau theo quy tac cu
        c.execute("UPDATE TaiKhoan SET tenDangNhap='tranthib02012004', phaiDoiMatKhau=0, matKhau=? WHERE maTaiKhoan=4", (generate_password_hash('DaTuDoi123'),))
        c.execute('PRAGMA user_version=2'); c.commit(); c.close()
        init_db(self.p)
        from app import create_app
        cl = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True}).test_client()
        dn = lambda u, m: cl.post('/api/dang-nhap', json={'tenDangNhap': u, 'matKhau': m}).status_code
        self.assertEqual(dn('nguyenvanan15032004', 'Nguyenvanan15032004'), 200)
        self.assertEqual(dn('nguyenvanan15032004', 'Nguy\u1ec5n v\u0103n an15032004'), 401)
        self.assertEqual(dn('tranthib02012004', 'DaTuDoi123'), 200)                           # da tu doi -> giu nguyen

    def test_v3_len_v4_them_nguon_gui_giu_thong_bao_va_trang_thai_doc(self):
        init_db(self.p)
        c = sqlite3.connect(self.p)
        c.execute('PRAGMA foreign_keys=OFF')
        # dua bang ve cau truc v3 (chua co sender_type...) voi du lieu cu
        c.execute('DELETE FROM ThongBaoDaDoc'); c.execute('DROP TABLE ThongBao')
        c.execute("""CREATE TABLE ThongBao (maThongBao INTEGER PRIMARY KEY AUTOINCREMENT,
          loai TEXT NOT NULL CHECK (loai IN ('CHUNG','NGHI','DAY_BU','DOI_PHONG','DOI_LICH','QUAN_TRONG')),
          tieuDe TEXT NOT NULL, noiDung TEXT NOT NULL, maTKB INTEGER, doiTuong TEXT NOT NULL DEFAULT 'TAT_CA',
          maLop INTEGER, maGiangVien INTEGER, maNguoiGui INTEGER, trangThai TEXT NOT NULL DEFAULT 'DA_GUI',
          ngayTao TEXT NOT NULL DEFAULT (datetime('now','localtime')), thoiGianGui TEXT, ngayCapNhat TEXT)""")
        c.execute("INSERT INTO ThongBao(maThongBao,loai,tieuDe,noiDung,doiTuong,thoiGianGui) VALUES (7,'CHUNG','Cu','ND','TAT_CA','2026-11-01 08:00:00')")
        c.execute('INSERT INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) VALUES (7,3)')
        c.execute('PRAGMA user_version=3'); c.commit(); c.close()
        init_db(self.p)
        c = sqlite3.connect(self.p); c.execute('PRAGMA foreign_keys=ON')
        self.assertEqual(c.execute('SELECT maThongBao,sender_type,tenNguoiGui,thoiGianGui FROM ThongBao').fetchall(),
                         [(7, 'PHONG_DAO_TAO', 'Ph\u00f2ng \u0110\u00e0o t\u1ea1o', '2026-11-01 08:00:00')])
        self.assertEqual(c.execute('SELECT count(*) FROM ThongBaoDaDoc WHERE maThongBao=7').fetchone()[0], 1)   # da doc con nguyen
        self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 5)
        c.execute("INSERT INTO ThongBao(loai,tieuDe,noiDung,doiTuong,maLop,sender_type) VALUES ('KIEM_TRA','x','y','LOP',1,'GIANG_VIEN')")

    def test_v4_len_v5_chuan_hoa_tai_khoan_cu_cung_ham_voi_tai_khoan_moi(self):
        from werkzeug.security import check_password_hash
        init_db(self.p)                                   # len v5 lan dau tu CSDL kieu cu
        c = sqlite3.connect(self.p)
        # dua ve trang thai v4: sv/gv cu dung ten + mat khau cu; mot nguoi da dung quy tac va tu doi mat khau
        c.execute('UPDATE SinhVien SET hoTen=?, ngaySinh=? WHERE maSinhVien=2', ('Nguyễn Văn An', '2004-03-15'))
        c.execute("UPDATE TaiKhoan SET tenDangNhap='sv1', matKhau=?, phaiDoiMatKhau=0 WHERE maTaiKhoan=3", (generate_password_hash('sv123'),))
        c.execute("UPDATE SinhVien SET ngaySinh=NULL WHERE maSinhVien=1")
        c.execute("UPDATE TaiKhoan SET tenDangNhap='nguyenvanan15032004', matKhau=?, phaiDoiMatKhau=0 WHERE maTaiKhoan=4", (generate_password_hash('DaTuDoi1'),))
        c.execute("UPDATE TaiKhoan SET tenDangNhap='gv1', matKhau=? WHERE maTaiKhoan=2", (generate_password_hash('gv123'),))
        c.execute('PRAGMA user_version=4'); c.commit(); c.close()
        init_db(self.p)
        c = sqlite3.connect(self.p)
        rows = {r[0]: r for r in c.execute('SELECT t.maTaiKhoan, t.tenDangNhap, t.matKhau, t.phaiDoiMatKhau FROM TaiKhoan t')}
        self.assertEqual(rows[1][1], 'pdt'); self.assertTrue(check_password_hash(rows[1][2], 'sv123'))          # PDT khong dong toi
        ngay = c.execute('SELECT ngaySinh FROM SinhVien WHERE maSinhVien=1').fetchone()[0]
        self.assertTrue(ngay)                                                                                     # ngay sinh tam duoc gan
        self.assertEqual(rows[3][1], 'a' + ngay[8:] + ngay[5:7] + ngay[:4])                                       # a + ddmmyyyy
        self.assertTrue(check_password_hash(rows[3][2], 'A' + ngay[8:] + ngay[5:7] + ngay[:4]))
        self.assertEqual(rows[3][3], 1)
        self.assertEqual(rows[2][1][:12], 'nguyenvanan1')                                                         # giang vien cu
        self.assertEqual((rows[4][1], rows[4][3]), ('nguyenvanan15032004', 0))                                    # da dung quy tac: giu nguyen
        self.assertTrue(check_password_hash(rows[4][2], 'DaTuDoi1'))                                              # ke ca mat khau da tu doi
        self.assertEqual(c.execute("SELECT maTaiKhoan FROM SinhVien WHERE maSinhVien=1").fetchone()[0], 3)       # giu lien ket
        self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
        n = len(glob.glob(self.p + '.bak-*')); init_db(self.p); self.assertEqual(len(glob.glob(self.p + '.bak-*')), n)  # chay lai: khong doi gi

    def test_chay_lai_khong_doi_gi_va_khong_sao_luu_lai(self):
        init_db(self.p); init_db(self.p); init_db(self.p)
        self.assertEqual(len(glob.glob(self.p + '.bak-*')), 1)
        c = sqlite3.connect(self.p)
        self.assertEqual(c.execute("SELECT maSoSinhVien FROM SinhVien WHERE maSinhVien=2").fetchone()[0], '2301')

    def _tk_quy_tac(self, bang, ma):
        """(ten dang nhap, mat khau) theo quy tac cua nguoi co ma `ma` sau nang cap."""
        from tkb.services.dinh_danh import tao_mat_khau
        c = sqlite3.connect(self.p)
        pk = 'maSinhVien' if bang == 'SinhVien' else 'maGiangVien'
        ten, ho, ngay = c.execute(f'SELECT t.tenDangNhap, p.hoTen, p.ngaySinh FROM {bang} p JOIN TaiKhoan t '
                                  f'ON t.maTaiKhoan=p.maTaiKhoan WHERE p.{pk}=?', (ma,)).fetchone()
        return ten, tao_mat_khau(ho, ngay)

    def test_tai_khoan_cu_chuyen_sang_quy_tac_sau_nang_cap_va_seed(self):
        from app import create_app
        app = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True})
        c = app.test_client()
        dn = lambda u, m: c.post('/api/dang-nhap', json={'tenDangNhap': u, 'matKhau': m}).status_code
        self.assertEqual(dn('pdt', 'sv123'), 200)                     # Phong Dao tao: khong thuoc pham vi chuan hoa
        for u in ('gv1', 'sv1', 'sv2', 'sv3'):
            self.assertEqual(dn(u, 'sv123'), 401, u)                  # ten + mat khau cu khong con dung
        ten, mk = self._tk_quy_tac('GiangVien', 1)
        self.assertRegex(ten, r'^nguyenvanan\d{8}$'); self.assertEqual(dn(ten, mk), 200)
        ten, mk = self._tk_quy_tac('SinhVien', 1)
        self.assertRegex(ten, r'^a\d{8}$'); self.assertEqual(dn(ten, mk), 200)
        self.assertTrue(c.get('/api/toi').json['phaiDoiMatKhau'])     # mat khau ban dau -> nhac doi

    def test_ma_moi_tiep_noi_sau_nang_cap(self):
        from app import create_app
        app = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True})
        c = app.test_client(); c.post('/api/dang-nhap', json={'tenDangNhap': 'pdt', 'matKhau': 'sv123'})
        r = c.post('/api/danh-muc/sinh-vien', json={'hoTen': 'Moi Vao', 'ngaySinh': '2004-01-01', 'maLop': 1})
        self.assertEqual((r.status_code, r.json['maSoSinhVien']), (201, '2203'))     # tiep sau 2201, 2202
        self.assertEqual(c.post('/api/danh-muc/sinh-vien', json={'hoTen': 'Lop La', 'ngaySinh': '2004-01-01', 'maLop': 3}).status_code, 400)


if __name__ == '__main__':
    unittest.main()
