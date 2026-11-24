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
        c.post('/api/dang-nhap', json={'tenDangNhap': 'sv1', 'matKhau': 'sv123'})
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
        c.execute("UPDATE TaiKhoan SET phaiDoiMatKhau=0, matKhau=? WHERE maTaiKhoan=4", (generate_password_hash('DaTuDoi123'),))
        c.execute('PRAGMA user_version=2'); c.commit(); c.close()
        init_db(self.p)
        from app import create_app
        cl = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True}).test_client()
        dn = lambda u, m: cl.post('/api/dang-nhap', json={'tenDangNhap': u, 'matKhau': m}).status_code
        self.assertEqual(dn('nguyenvanan15032004', 'Nguyenvanan15032004'), 200)
        self.assertEqual(dn('nguyenvanan15032004', 'Nguy\u1ec5n v\u0103n an15032004'), 401)
        self.assertEqual(dn('sv2', 'DaTuDoi123'), 200)                                     # da tu doi -> giu nguyen

    def test_chay_lai_khong_doi_gi_va_khong_sao_luu_lai(self):
        init_db(self.p); init_db(self.p); init_db(self.p)
        self.assertEqual(len(glob.glob(self.p + '.bak-*')), 1)
        c = sqlite3.connect(self.p)
        self.assertEqual(c.execute("SELECT maSoSinhVien FROM SinhVien WHERE maSinhVien=2").fetchone()[0], '2301')

    def test_tai_khoan_cu_dang_nhap_duoc_sau_nang_cap_va_seed(self):
        from app import create_app
        app = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True})
        c = app.test_client()
        for ten in ('pdt', 'gv1', 'sv1'):
            self.assertEqual(c.post('/api/dang-nhap', json={'tenDangNhap': ten, 'matKhau': 'sv123'}).status_code, 200, ten)
        self.assertFalse(c.get('/api/toi').json['phaiDoiMatKhau'])      # tai khoan cu khong bi ep doi mat khau

    def test_ma_moi_tiep_noi_sau_nang_cap(self):
        from app import create_app
        app = create_app({'DATABASE': self.p, 'SEED_DEMO': False, 'TESTING': True})
        c = app.test_client(); c.post('/api/dang-nhap', json={'tenDangNhap': 'pdt', 'matKhau': 'sv123'})
        r = c.post('/api/danh-muc/sinh-vien', json={'hoTen': 'Moi Vao', 'ngaySinh': '2004-01-01', 'maLop': 1})
        self.assertEqual((r.status_code, r.json['maSoSinhVien']), (201, '2203'))     # tiep sau 2201, 2202
        self.assertEqual(c.post('/api/danh-muc/sinh-vien', json={'hoTen': 'Lop La', 'ngaySinh': '2004-01-01', 'maLop': 3}).status_code, 400)


if __name__ == '__main__':
    unittest.main()
