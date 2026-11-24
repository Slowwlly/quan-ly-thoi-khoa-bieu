"""Kiem thu tu dong cho cac test case TC-xx trong Chuong 5 cua bao cao.
Chay:  python -m unittest -v
"""
import os
import shutil
import tempfile
import unittest
from datetime import date

from app import create_app

HOM_NAY = date(2026, 11, 4)          # Thu tu; tuan chua ngay nay bat dau 2026-11-02
TUAN = '2026-11-02'


MAU = {}


def setUpModule():
    # Tao CSDL mau mot lan (bam mat khau kha cham) roi sao chep cho tung test.
    d = tempfile.mkdtemp()
    MAU['path'] = os.path.join(d, 'mau.sqlite3')
    create_app({'DATABASE': MAU['path'], 'SEED_TODAY': HOM_NAY, 'TESTING': True})


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        db = os.path.join(self.tmp, 't.sqlite3')
        shutil.copy(MAU['path'], db)
        self.app = create_app({'DATABASE': db, 'SEED_TODAY': HOM_NAY, 'TESTING': True})
        self.c = self.app.test_client()

    def login(self, ten, mk, client=None):
        c = client or self.c
        return c.post('/api/dang-nhap', json={'tenDangNhap': ten, 'matKhau': mk})

    def as_user(self, ten, mk):
        c = self.app.test_client()
        self.assertEqual(self.login(ten, mk, c).status_code, 200)
        return c


class TestDangNhap(BaseTest):
    def test_tc01_giang_vien_hop_le(self):
        r = self.login('gv1', 'gv123'); self.assertEqual(r.status_code, 200); self.assertEqual(r.json['vaiTro'], 'GIANG_VIEN')

    def test_tc02_sinh_vien_hop_le(self):
        self.assertEqual(self.login('sv1', 'sv123').json['vaiTro'], 'SINH_VIEN')

    def test_tc03_phong_dao_tao_hop_le(self):
        self.assertEqual(self.login('pdt', 'pdt123').json['vaiTro'], 'PHONG_DAO_TAO')

    def test_tc04_sai_mat_khau(self):
        self.assertEqual(self.login('gv1', 'sai').status_code, 401)

    def test_tc05_tai_khoan_khong_ton_tai(self):
        r = self.login('khong_co', 'abc123'); self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json['loi'], self.login('gv1', 'sai').json['loi'])  # khong lo tai khoan co ton tai hay khong

    def test_tc06_bo_trong(self):
        self.assertEqual(self.login('', '').status_code, 400)

    def test_tc20_dang_xuat(self):
        self.login('sv1', 'sv123')
        self.assertEqual(self.c.get('/api/toi').status_code, 200)
        self.c.post('/api/dang-xuat')
        self.assertEqual(self.c.get('/api/toi').status_code, 401)

    def test_chua_dang_nhap_bi_tu_choi(self):
        self.assertEqual(self.c.get('/api/tkb').status_code, 401)

    def test_mat_khau_luu_dang_bam(self):
        import sqlite3
        con = sqlite3.connect(self.app.config['DATABASE'])
        mk = con.execute("SELECT matKhau FROM TaiKhoan WHERE tenDangNhap='sv1'").fetchone()[0]
        self.assertNotEqual(mk, 'sv123'); self.assertNotIn('sv123', mk)

    def test_doi_mat_khau(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(c.post('/api/doi-mat-khau', json={'matKhauCu': 'sai', 'matKhauMoi': 'moi12345'}).status_code, 400)
        self.assertEqual(c.post('/api/doi-mat-khau', json={'matKhauCu': 'sv123', 'matKhauMoi': '123'}).status_code, 400)
        self.assertEqual(c.post('/api/doi-mat-khau', json={'matKhauCu': 'sv123', 'matKhauMoi': 'moi12345'}).status_code, 200)
        self.assertEqual(self.login('sv1', 'sv123').status_code, 401)
        self.assertEqual(self.login('sv1', 'moi12345').status_code, 200)


class TestXemThoiKhoaBieu(BaseTest):
    def test_tc07_sinh_vien_xem_lich_cua_minh(self):
        c = self.as_user('sv1', 'sv123')
        ds = c.get(f'/api/tkb?tuan={TUAN}').json
        self.assertEqual(len(ds), 4)
        self.assertTrue(all(x['tenLop'] == 'CNTT 1' for x in ds))

    def test_tc08_giang_vien_xem_lich_giang_day(self):
        c = self.as_user('gv1', 'gv123')
        ds = c.get(f'/api/tkb?tuan={TUAN}').json
        self.assertTrue(ds); self.assertTrue(all(x['tenGiangVien'] == 'Nguyen Van An' for x in ds))
        for k in ('ngayHoc', 'tietBatDau', 'tenMonHoc', 'tenLop', 'tenPhong'):
            self.assertIn(k, ds[0])

    def test_tc09_xem_theo_ngay(self):
        ds = self.as_user('sv1', 'sv123').get('/api/tkb?ngay=2026-11-02').json
        self.assertEqual([x['ngayHoc'] for x in ds], ['2026-11-02']); self.assertEqual(ds[0]['tenMonHoc'], 'Ky nghe phan mem')

    def test_tc10_chuyen_tuan(self):
        c = self.as_user('sv1', 'sv123')
        t1 = c.get('/api/tkb?tuan=2026-11-02').json; t2 = c.get('/api/tkb?tuan=2026-11-09').json
        self.assertTrue(t1 and t2); self.assertNotEqual({x['maTKB'] for x in t1}, {x['maTKB'] for x in t2})
        self.assertTrue(all('2026-11-09' <= x['ngayHoc'] <= '2026-11-15' for x in t2))

    def test_tc11_xem_theo_ma_lop_cua_pdt(self):
        c = self.as_user('pdt', 'pdt123')
        ds = c.get(f'/api/tkb?tuan={TUAN}&maLop=3').json
        self.assertTrue(ds); self.assertTrue(all(x['maLop'] == 3 for x in ds))

    def test_tc12_tim_kiem_co_ket_qua(self):
        ds = self.as_user('sv1', 'sv123').get('/api/tkb?q=Web').json
        self.assertTrue(ds); self.assertTrue(all(x['tenMonHoc'] == 'Lap trinh Web' for x in ds))

    def test_tc13_tim_kiem_khong_co_ket_qua(self):
        r = self.as_user('sv1', 'sv123').get('/api/tkb?q=khongtontaixyz'); self.assertEqual(r.status_code, 200); self.assertEqual(r.json, [])

    def test_tc14_chi_tiet_buoi_hoc(self):
        c = self.as_user('sv1', 'sv123')
        ma = c.get('/api/tkb?ngay=2026-11-02').json[0]['maTKB']
        r = c.get(f'/api/tkb/{ma}')
        self.assertEqual(r.status_code, 200)
        for k in ('ngayHoc', 'tietBatDau', 'tietKetThuc', 'tenMonHoc', 'tenPhong', 'tenLop', 'tenGiangVien'):
            self.assertIn(k, r.json)

    def test_chi_tiet_khong_ton_tai(self):
        self.assertEqual(self.as_user('sv1', 'sv123').get('/api/tkb/999999').status_code, 404)

    def test_tc15_tuan_khong_co_lich(self):
        r = self.as_user('sv1', 'sv123').get('/api/tkb?tuan=2030-01-07'); self.assertEqual(r.json, [])

    def test_ngay_khong_hop_le(self):
        self.assertEqual(self.as_user('sv1', 'sv123').get('/api/tkb?ngay=31-12-2026').status_code, 400)


class TestPhanQuyen(BaseTest):
    def test_tc18_sinh_vien_khong_duoc_tao_tkb(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(c.post('/api/tkb', json={}).status_code, 403)
        self.assertEqual(c.delete('/api/tkb/1').status_code, 403)
        self.assertEqual(c.get('/api/danh-muc/sinh-vien').status_code, 403)
        self.assertEqual(c.get('/api/thong-ke').status_code, 403)

    def test_tc19_giang_vien_khong_xem_lich_nguoi_khac(self):
        c = self.as_user('gv1', 'gv123')
        self.assertEqual(c.get('/api/tkb?maGiangVien=2').status_code, 403)
        ma_gv2 = self.as_user('pdt', 'pdt123').get('/api/tkb?maGiangVien=2').json[0]['maTKB']
        self.assertEqual(c.get(f'/api/tkb/{ma_gv2}').status_code, 403)

    def test_sinh_vien_khong_xem_lop_khac(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(c.get('/api/tkb?maLop=3').status_code, 403)
        ma_lop3 = self.as_user('pdt', 'pdt123').get('/api/tkb?maLop=3').json[0]['maTKB']
        self.assertEqual(c.get(f'/api/tkb/{ma_lop3}').status_code, 403)


class TestTaoThoiKhoaBieu(BaseTest):
    def ds(self):
        c = self.as_user('pdt', 'pdt123')
        return c, {x['tenGiangVien']: x['maGiangVien'] for x in c.get('/api/tkb?ngay=2026-11-02').json}

    def body(self, **kw):
        b = {'ngayHoc': '2026-11-03', 'tietBatDau': 9, 'tietKetThuc': 10, 'hocKy': 'HK1', 'namHoc': '2026-2027',
             'maGiangVien': 1, 'maMonHoc': 1, 'maLop': 1, 'maPhong': 4}
        b.update(kw); return b

    def test_tc16_tao_hop_le(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/tkb', json=self.body())
        self.assertEqual(r.status_code, 201); self.assertTrue(r.json['tenPhong'].endswith('P301'))
        self.assertIn(r.json['maTKB'], [x['maTKB'] for x in c.get('/api/tkb?ngay=2026-11-03').json])

    def test_tc17_trung_phong(self):
        c = self.as_user('pdt', 'pdt123')   # P101 da co Lop CT2201 vao Thu hai 2026-11-02 tiet 1-3
        r = c.post('/api/tkb', json=self.body(ngayHoc='2026-11-02', tietBatDau=2, tietKetThuc=4, maGiangVien=4, maLop=3, maPhong=1))
        self.assertEqual(r.status_code, 409); self.assertIn('Phong', r.json['loi'])

    def test_trung_giang_vien(self):
        c = self.as_user('pdt', 'pdt123')   # gv1 (ma 1) day tiet 1-3 Thu hai
        r = c.post('/api/tkb', json=self.body(ngayHoc='2026-11-02', tietBatDau=3, tietKetThuc=3, maLop=3, maPhong=4))
        self.assertEqual(r.status_code, 409); self.assertIn('Giang vien', r.json['loi'])

    def test_trung_lop(self):
        c = self.as_user('pdt', 'pdt123')   # CT2201 (ma 1) co tiet 1-3 Thu hai
        r = c.post('/api/tkb', json=self.body(ngayHoc='2026-11-02', tietBatDau=1, tietKetThuc=1, maGiangVien=4, maPhong=4))
        self.assertEqual(r.status_code, 409); self.assertIn('Lop', r.json['loi'])

    def test_lien_ke_khong_bi_coi_la_trung(self):
        c = self.as_user('pdt', 'pdt123')   # tiet 4 ngay sau tiet 3: hop le
        self.assertEqual(c.post('/api/tkb', json=self.body(ngayHoc='2026-11-02', tietBatDau=4, tietKetThuc=5)).status_code, 201)

    def test_du_lieu_khong_hop_le(self):
        c = self.as_user('pdt', 'pdt123')
        for kw in ({'ngayHoc': 'abc'}, {'tietBatDau': 5, 'tietKetThuc': 2}, {'tietKetThuc': 99}, {'maPhong': 999}, {'maLop': ''}):
            self.assertEqual(c.post('/api/tkb', json=self.body(**kw)).status_code, 400, kw)

    def test_sua_khong_trung_voi_chinh_no(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/tkb', json=self.body()); ma = r.json['maTKB']
        self.assertEqual(c.put(f'/api/tkb/{ma}', json=self.body(tietKetThuc=9)).status_code, 200)

    def test_xoa(self):
        c = self.as_user('pdt', 'pdt123')
        ma = c.post('/api/tkb', json=self.body()).json['maTKB']
        self.assertEqual(c.delete(f'/api/tkb/{ma}').status_code, 200)
        self.assertEqual(c.delete(f'/api/tkb/{ma}').status_code, 404)


class TestDanhMuc(BaseTest):
    def test_crud_khoa(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/danh-muc/khoa', json={'tenKhoa': 'Ngoai ngu'}); self.assertEqual(r.status_code, 201)
        ma = r.json['maKhoa']
        self.assertEqual(c.put(f'/api/danh-muc/khoa/{ma}', json={'tenKhoa': 'Ngoai ngu 2'}).json['tenKhoa'], 'Ngoai ngu 2')
        self.assertEqual(c.post('/api/danh-muc/khoa', json={'tenKhoa': 'Ngoai ngu 2'}).status_code, 409)
        self.assertEqual(c.delete(f'/api/danh-muc/khoa/{ma}').status_code, 200)

    def test_khong_xoa_khi_dang_duoc_su_dung(self):
        c = self.as_user('pdt', 'pdt123')
        self.assertEqual(c.delete('/api/danh-muc/khoa/1').status_code, 409)
        self.assertEqual(c.delete('/api/danh-muc/phong-hoc/1').status_code, 409)

    def test_thieu_truong_bat_buoc(self):
        c = self.as_user('pdt', 'pdt123')
        self.assertEqual(c.post('/api/danh-muc/mon-hoc', json={'tenMonHoc': 'X'}).status_code, 400)

    def test_tao_giang_vien_tai_khoan_theo_quy_tac(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/danh-muc/giang-vien', json={'hoTen': 'Mau Thu', 'ngaySinh': '1990-01-05', 'maKhoa': 1})
        self.assertEqual(r.status_code, 201); self.assertEqual(r.json['tenDangNhap'], 'mauthu05011990')
        self.assertEqual(self.login('mauthu05011990', 'Mauthu05011990').json['vaiTro'], 'GIANG_VIEN')
        self.assertEqual(c.post('/api/danh-muc/giang-vien', json={'hoTen': 'Khong Ngay', 'maKhoa': 1}).status_code, 400)

    def test_tao_sinh_vien_ma_tu_sinh_va_ten_lop_de_doc(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/danh-muc/sinh-vien', json={'maSoSinhVien': 'TUNHAP', 'hoTen': 'Sinh Vien Kiem Thu',
                                                     'ngaySinh': '2004-02-03', 'maLop': 1})
        self.assertEqual(r.status_code, 201)
        self.assertRegex(r.json['maSoSinhVien'], r'^22\d\d$')      # lop 1 thuoc khoa 2022; ma nhap tay bi bo qua
        self.assertEqual(r.json['tenLop'], 'CNTT 1'); self.assertEqual(r.json['namTuyenSinh'], 2022)

    def test_danh_muc_tim_kiem_va_loc_cho_moi_nguoi(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(c.get('/api/danh-muc/lop').status_code, 200)
        self.assertEqual(len(self.as_user('pdt', 'pdt123').get('/api/danh-muc/sinh-vien?q=Hoang Van Em').json), 1)

    def test_thong_ke(self):
        r = self.as_user('pdt', 'pdt123').get('/api/thong-ke')
        self.assertEqual(r.status_code, 200); self.assertGreater(r.json['tongSoBuoi'], 0)


class TestNhapExcel(BaseTest):
    """Nhap hang loat sinh vien / buoi hoc tu file Excel."""

    @staticmethod
    def _xlsx(rows):
        import io
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active
        for r in rows:
            ws.append(r)
        b = io.BytesIO(); wb.save(b); b.seek(0)
        return b

    def _up(self, c, loai, rows):
        return c.post(f'/api/nhap-excel/{loai}', data={'file': (self._xlsx(rows), 'f.xlsx')},
                      content_type='multipart/form-data')

    def test_nhap_sinh_vien_hop_le_va_dong_loi(self):
        c = self.as_user('pdt', 'pdt123')
        tieu = ['H\u1ecd t\u00ean', 'Ng\u00e0y sinh', 'L\u1edbp']
        r = self._up(c, 'sinh-vien', [
            tieu,
            ['Nguyen A', '15/03/2004', 'CNTT 1'],
            ['Nguyen B', '2004-03-15', 'Lop khong co'],
            ['Nguyen A', '15/03/2004', 'CNTT 1'],      # trung ho ten + ngay sinh -> khong ghi de tai khoan
        ])
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json['thanhCong'], r.json['thatBai']), (1, 2))
        self.assertEqual(sorted(x['dong'] for x in r.json['chiTietLoi']), [3, 4])
        self.assertEqual(self.login('nguyena15032004', 'Nguyena15032004', self.app.test_client()).status_code, 200)

    def test_nhap_buoi_hoc_kiem_tra_trung_lich(self):
        c = self.as_user('pdt', 'pdt123')
        tieu_de = ['Ng\u00e0y h\u1ecdc', 'Ti\u1ebft b\u1eaft \u0111\u1ea7u', 'Ti\u1ebft k\u1ebft th\u00fac', 'M\u00f4n h\u1ecdc',
                   'Gi\u1ea3ng vi\u00ean', 'L\u1edbp', 'Ph\u00f2ng']
        lop = c.get('/api/danh-muc/lop').json[0]['tenLop']
        mon = c.get('/api/danh-muc/mon-hoc').json[0]['tenMonHoc']
        gv = c.get('/api/danh-muc/giang-vien').json[0]['hoTen']
        p1, p2 = [x['tenPhong'] for x in c.get('/api/danh-muc/phong-hoc').json[:2]]
        r = self._up(c, 'tkb', [tieu_de,
                                ['01/03/2027', 1, 3, mon, gv, lop, p1],
                                ['01/03/2027', 2, 4, mon, gv, lop, p2]])  # trung giang vien + lop voi dong tren
        self.assertEqual((r.json['thanhCong'], r.json['thatBai']), (1, 1))
        self.assertIn('Trung lich', r.json['chiTietLoi'][0]['noiDung'])

    def test_file_thieu_cot_hoac_sai_dinh_dang(self):
        c = self.as_user('pdt', 'pdt123')
        self.assertEqual(self._up(c, 'sinh-vien', [['H\u1ecd t\u00ean'], ['x']]).status_code, 400)  # thieu cot Ngay sinh, Lop
        r = c.post('/api/nhap-excel/khoa', data={'file': (self._xlsx([['a']]), 'f.txt')},
                   content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    def test_chi_phong_dao_tao_duoc_nhap_va_tai_mau(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(self._up(c, 'khoa', [['T\u00ean khoa'], ['Khoa moi']]).status_code, 403)
        self.assertEqual(c.get('/api/nhap-excel/khoa/mau').status_code, 403)
        self.assertEqual(self.as_user('pdt', 'pdt123').get('/api/nhap-excel/sinh-vien/mau').status_code, 200)


class TestXoaThongBao(BaseTest):
    def _tao(self, c):
        c.post('/api/thong-bao/chung', json={'tieuDe': 'Nghi le', 'noiDung': 'Nghi hoc'})
        return c.get('/api/thong-bao').json[0]['maThongBao']

    def test_pdt_xoa_thong_bao(self):
        c = self.as_user('pdt', 'pdt123')
        ma = self._tao(c)
        self.assertEqual(c.delete(f'/api/thong-bao/{ma}').status_code, 200)
        self.assertNotIn(ma, [n['maThongBao'] for n in c.get('/api/thong-bao').json])
        self.assertEqual(c.delete(f'/api/thong-bao/{ma}').status_code, 404)

    def test_sinh_vien_va_giang_vien_khong_duoc_xoa(self):
        ma = self._tao(self.as_user('pdt', 'pdt123'))
        for ten, mk in (('sv1', 'sv123'), ('gv1', 'gv123')):
            self.assertEqual(self.as_user(ten, mk).delete(f'/api/thong-bao/{ma}').status_code, 403)
        self.assertEqual(self.app.test_client().delete(f'/api/thong-bao/{ma}').status_code, 401)


# =====================================================================
# Cac chuc nang bo sung: xuat TKB, thong bao, ma sinh vien, dang nhap theo quy tac
# =====================================================================
import io
import sqlite3
import threading

SV_AN = ('nguyenvanan15032004', 'Nguyenvanan15032004')            # SV mau khoa 2024, lop CNTT 1 - K24
GV_NAM = ('lehoangnam12051985', 'Lehoangnam12051985')
PDT_ANH = ('tranthiminhanh08092003', 'Tranthiminhanh08092003')


class TestQuyTacTaiKhoan(unittest.TestCase):
    def test_ten_dang_nhap_va_mat_khau_theo_vi_du(self):
        from tkb.services.dinh_danh import tao_ten_dang_nhap as tdn, tao_mat_khau as mk
        self.assertEqual(tdn('Nguy\u1ec5n V\u0103n An', '2004-03-15'), 'nguyenvanan15032004')
        self.assertEqual(mk('Nguy\u1ec5n V\u0103n An', '15/03/2004'), 'Nguyenvanan15032004')
        self.assertEqual(tdn('Tr\u1ea7n Th\u1ecb Minh Anh', '2003-09-08'), 'tranthiminhanh08092003')
        self.assertEqual(mk('Tr\u1ea7n Th\u1ecb Minh Anh', '2003-09-08'), 'Tranthiminhanh08092003')

    def test_giu_so_0_dau_chu_d_va_khoang_trang_thua(self):
        from tkb.services.dinh_danh import tao_ten_dang_nhap as tdn, tao_mat_khau as mk
        self.assertEqual(tdn('  \u0110\u1ed7   \u0110\u1ee9c \u0110\u1ea1t ', '2005-01-02'), 'doducdat02012005')
        self.assertEqual(mk('\u0110\u1ed7 \u0110\u1ee9c  \u0110\u1ea1t', '2005-01-02'), 'Doducdat02012005')

    def test_ngay_sinh_khong_hop_le(self):
        from tkb.errors import AppError
        from tkb.services.dinh_danh import parse_ngay_sinh
        for v in ('', 'abc', '2004-02-30', '31/02/2004', '2999-01-01', '1800-01-01'):
            with self.assertRaises(AppError, msg=v):
                parse_ngay_sinh(v)


class TestDangNhapBaVaiTro(BaseTest):
    def test_ba_vai_tro_dang_nhap_bang_tai_khoan_quy_tac(self):
        for (ten, mk), vt in ((SV_AN, 'SINH_VIEN'), (GV_NAM, 'GIANG_VIEN'), (PDT_ANH, 'PHONG_DAO_TAO')):
            r = self.login(ten, mk, self.app.test_client())
            self.assertEqual((r.status_code, r.json['vaiTro']), (200, vt), ten)
            self.assertTrue(r.json['phaiDoiMatKhau'])

    def test_khong_gui_vai_tro_van_tu_nhan_dien_va_khong_doi_duoc_vai_tro(self):
        c = self.app.test_client()
        r = c.post('/api/dang-nhap', json={'tenDangNhap': SV_AN[0], 'matKhau': SV_AN[1], 'vaiTro': 'PHONG_DAO_TAO'})
        self.assertEqual(r.json['vaiTro'], 'SINH_VIEN')
        self.assertEqual(c.get('/api/toi').json['vaiTro'], 'SINH_VIEN')
        self.assertEqual(c.get('/api/danh-muc/sinh-vien').status_code, 403)
        self.assertEqual(c.post('/api/thong-bao', json={'tieuDe': 'x', 'noiDung': 'y'}).status_code, 403)

    def test_sai_mat_khau_sai_quy_tac_va_tai_khoan_khong_ton_tai(self):
        c = self.app.test_client()
        for sai in ('NguyenVanAn15032004',        # viet hoa tung chu
                    'nguyenvanan15032004',        # khong viet hoa chu dau
                    'Nguyen van an15032004',      # con khoang trang
                    'Nguy\u1ec5n v\u0103n an15032004',   # con dau (quy tac cu)
                    'Nguyenvanan', 'Nguyenvanan1503'):
            self.assertEqual(self.login(SV_AN[0], sai, c).status_code, 401, sai)
        self.assertEqual(self.login('khongco15032004', 'x1234567', c).status_code, 401)

    def test_ngay_sinh_so_0_dau(self):
        c = self.as_user(*('pdt', 'pdt123'))
        r = c.post('/api/danh-muc/sinh-vien', json={'hoTen': 'Le Thi Be', 'ngaySinh': '2005-03-08', 'maLop': 1})
        self.assertEqual(r.json['tenDangNhap'], 'lethibe08032005')
        self.assertEqual(self.login('lethibe08032005', 'Lethibe08032005', self.app.test_client()).status_code, 200)

    def test_mat_khau_luu_hash_va_khong_lo_ra_api(self):
        con = sqlite3.connect(self.app.config['DATABASE'])
        for ten, mk in (SV_AN, GV_NAM, PDT_ANH):
            h = con.execute('SELECT matKhau FROM TaiKhoan WHERE tenDangNhap=?', (ten,)).fetchone()[0]
            self.assertNotIn(mk, h); self.assertTrue(h.startswith(('scrypt:', 'pbkdf2:')))
        c = self.as_user(*SV_AN)
        for url in ('/api/toi', '/api/tkb', '/api/thong-bao'):
            self.assertNotIn('matKhau', c.get(url).get_data(as_text=True)); 
        pdt = self.as_user('pdt', 'pdt123')
        for ten in ('sinh-vien', 'giang-vien'):
            t = pdt.get(f'/api/danh-muc/{ten}').get_data(as_text=True)
            self.assertNotIn('matKhau', t); self.assertNotIn('scrypt', t)

    def test_tai_khoan_trung_duoc_phat_hien_khong_ghi_de(self):
        c = self.as_user('pdt', 'pdt123')
        du_lieu = {'hoTen': 'Nguy\u1ec5n V\u0103n An', 'ngaySinh': '15/03/2004', 'maLop': 1}
        r = c.post('/api/danh-muc/sinh-vien', json=du_lieu)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json['goiY']['tenDangNhapDeXuat'], 'nguyenvanan15032004_2')
        self.assertIn('hau to', r.json['loi'].replace('hậu tố', 'hau to'))
        # tai khoan cu van dang nhap duoc bang mat khau cu, khong bi ghi de
        self.assertEqual(self.login(*SV_AN, self.app.test_client()).status_code, 200)
        ok = c.post('/api/danh-muc/sinh-vien', json={**du_lieu, 'chapNhanHauTo': True})
        self.assertEqual((ok.status_code, ok.json['tenDangNhap']), (201, 'nguyenvanan15032004_2'))
        self.assertEqual(self.login('nguyenvanan15032004_2', SV_AN[1], self.app.test_client()).status_code, 200)

    def test_dang_xuat_va_chan_trang_noi_bo(self):
        c = self.as_user(*GV_NAM)
        self.assertEqual(c.get('/api/tkb').status_code, 200)
        c.post('/api/dang-xuat')
        for url in ('/api/tkb', '/api/thong-bao', '/api/tkb/xuat?dinhDang=pdf', '/api/danh-muc/lop'):
            self.assertEqual(c.get(url).status_code, 401, url)

    def test_doi_mat_khau_day_du(self):
        c = self.as_user(*SV_AN)
        self.assertTrue(c.get('/api/toi').json['phaiDoiMatKhau'])
        ds = lambda **k: c.post('/api/doi-mat-khau', json=k).status_code
        self.assertEqual(ds(matKhauCu='sai', matKhauMoi='Moi12345', matKhauXacNhan='Moi12345'), 400)
        self.assertEqual(ds(matKhauCu=SV_AN[1], matKhauMoi='Moi12345', matKhauXacNhan='Khac12345'), 400)
        self.assertEqual(ds(matKhauCu=SV_AN[1], matKhauMoi='123', matKhauXacNhan='123'), 400)
        self.assertEqual(ds(matKhauCu=SV_AN[1], matKhauMoi=SV_AN[1], matKhauXacNhan=SV_AN[1]), 400)
        self.assertEqual(ds(matKhauCu=SV_AN[1], matKhauMoi='Moi12345', matKhauXacNhan='Moi12345'), 200)
        self.assertFalse(c.get('/api/toi').json['phaiDoiMatKhau'])
        self.assertEqual(self.login(SV_AN[0], SV_AN[1], self.app.test_client()).status_code, 401)
        self.assertEqual(self.login(SV_AN[0], 'Moi12345', self.app.test_client()).status_code, 200)

    def test_khoi_dong_lai_khong_dat_lai_mat_khau(self):
        self.as_user(*SV_AN).post('/api/doi-mat-khau', json={'matKhauCu': SV_AN[1], 'matKhauMoi': 'Moi12345'})
        app2 = create_app({'DATABASE': self.app.config['DATABASE'], 'SEED_TODAY': HOM_NAY, 'TESTING': True})
        c = app2.test_client()
        self.assertEqual(c.post('/api/dang-nhap', json={'tenDangNhap': SV_AN[0], 'matKhau': 'Moi12345'}).status_code, 200)
        self.assertEqual(c.post('/api/dang-nhap', json={'tenDangNhap': 'sv1', 'matKhau': 'sv123'}).status_code, 200)

    def test_tai_khoan_cu_khong_co_ngay_sinh_giu_nguyen_va_xu_ly_rieng(self):
        pdt = self.as_user('pdt', 'pdt123')
        sv1 = [x for x in pdt.get('/api/danh-muc/sinh-vien?q=Hoang Van Em').json][0]
        self.assertIsNone(sv1['ngaySinh']); self.assertEqual(sv1['tenDangNhap'], 'sv1')
        self.assertEqual(pdt.post(f"/api/danh-muc/sinh-vien/{sv1['maSinhVien']}/cap-tai-khoan", json={}).status_code, 400)
        pdt.put(f"/api/danh-muc/sinh-vien/{sv1['maSinhVien']}", json={'hoTen': sv1['hoTen'], 'maLop': sv1['maLop'], 'ngaySinh': '2003-04-05'})
        self.assertEqual(self.login('sv1', 'sv123', self.app.test_client()).status_code, 200)   # them ngay sinh khong doi mat khau
        r = pdt.post(f"/api/danh-muc/sinh-vien/{sv1['maSinhVien']}/cap-tai-khoan", json={})
        self.assertEqual(r.status_code, 409)                                                    # can xac nhan ro rang
        r = pdt.post(f"/api/danh-muc/sinh-vien/{sv1['maSinhVien']}/cap-tai-khoan", json={'xacNhanDoi': True})
        self.assertEqual(r.json['tenDangNhap'], 'hoangvanem05042003')
        self.assertEqual(self.login('sv1', 'sv123', self.app.test_client()).status_code, 401)
        self.assertEqual(self.login('hoangvanem05042003', 'Hoangvanem05042003', self.app.test_client()).status_code, 200)

    def test_xoa_sinh_vien_xoa_ca_tai_khoan(self):
        pdt = self.as_user('pdt', 'pdt123')
        sv = pdt.get('/api/danh-muc/sinh-vien?q=nguyenvanan15032004').json[0]
        self.assertEqual(pdt.delete(f"/api/danh-muc/sinh-vien/{sv['maSinhVien']}").status_code, 200)
        self.assertEqual(self.login(*SV_AN, self.app.test_client()).status_code, 401)


class TestMaSinhVienVaDanhSach(BaseTest):
    def sv(self, c, **kw):
        n = getattr(self, '_n', 0) + 1; self._n = n
        d = {'hoTen': f'Sinh Vien Moi{chr(96 + n % 26 + 1)}{chr(96 + n // 26 + 1)}', 'ngaySinh': '2005-06-07', 'maLop': 1}
        d.update(kw); return c.post('/api/danh-muc/sinh-vien', json=d)

    def lop_khoa(self, c, nam):
        return [x for x in c.get('/api/danh-muc/lop').json if x['namTuyenSinh'] == nam][0]['maLop']

    def test_du_4_khoa_va_ma_dung_dinh_dang(self):
        c = self.as_user('pdt', 'pdt123')
        ds = c.get('/api/danh-muc/sinh-vien').json
        theo = {}
        for x in ds:
            theo.setdefault(x['namTuyenSinh'], []).append(x['maSoSinhVien'])
        for nam in (2024, 2025, 2026, 2027):
            self.assertGreaterEqual(len(theo[nam]), 40, nam)
            self.assertTrue(all(m.startswith(str(nam)[2:]) for m in theo[nam]))
        self.assertTrue(all(len(x['maSoSinhVien']) == 4 and x['maSoSinhVien'].isdigit() for x in ds))
        self.assertEqual(len({x['maSoSinhVien'] for x in ds}), len(ds))
        self.assertTrue(all(x['maLop'] and x['tenLop'] and x['tenDangNhap'] for x in ds if x['namTuyenSinh'] >= 2024))
        self.assertGreaterEqual(len({x['maLop'] for x in ds if x['namTuyenSinh'] == 2024}), 4)

    def test_ma_ke_tiep_khong_doi_khi_sua_va_khong_cap_lai_khi_xoa(self):
        c = self.as_user('pdt', 'pdt123'); lop = self.lop_khoa(c, 2025)
        cuoi = max(x['maSoSinhVien'] for x in c.get('/api/danh-muc/sinh-vien?namTuyenSinh=2025').json)
        a = self.sv(c, maLop=lop).json; b = self.sv(c, maLop=lop).json
        self.assertEqual((a['maSoSinhVien'], b['maSoSinhVien']), (str(int(cuoi) + 1), str(int(cuoi) + 2)))
        self.assertEqual(c.put(f"/api/danh-muc/sinh-vien/{a['maSinhVien']}",
                               json={'hoTen': 'Doi Ten Moi', 'maLop': lop, 'maSoSinhVien': '9999'}).json['maSoSinhVien'], a['maSoSinhVien'])
        c.delete(f"/api/danh-muc/sinh-vien/{b['maSinhVien']}")           # xoa ma lon nhat
        self.assertEqual(c.get(f"/api/danh-muc/sinh-vien?q={a['maSoSinhVien']}").json[0]['maSoSinhVien'], a['maSoSinhVien'])
        moi = self.sv(c, maLop=lop).json
        self.assertEqual(moi['maSoSinhVien'], str(int(cuoi) + 3))         # khong dung lai ma da xoa

    def test_khong_chuyen_sang_lop_khac_khoa(self):
        c = self.as_user('pdt', 'pdt123')
        sv = self.sv(c, maLop=self.lop_khoa(c, 2025)).json
        r = c.put(f"/api/danh-muc/sinh-vien/{sv['maSinhVien']}", json={'hoTen': sv['hoTen'], 'maLop': self.lop_khoa(c, 2026)})
        self.assertEqual(r.status_code, 400)

    def test_ma_khong_trung_khi_nhieu_nguoi_them_cung_luc(self):
        lop, ket_qua, loi = 1, [], []
        def chay(i):
            c = self.as_user('pdt', 'pdt123')
            r = c.post('/api/danh-muc/sinh-vien', json={'hoTen': f'Song Song Nguoi{chr(97 + i)}', 'ngaySinh': '2005-01-01', 'maLop': lop})
            (ket_qua if r.status_code == 201 else loi).append(r.json.get('maSoSinhVien') or r.json)
        luong = [threading.Thread(target=chay, args=(i,)) for i in range(8)]
        [t.start() for t in luong]; [t.join() for t in luong]
        self.assertEqual(loi, []); self.assertEqual(len(set(ket_qua)), 8)
        so = sorted(int(m) for m in ket_qua)
        self.assertEqual(so, list(range(so[0], so[0] + 8)))

    def test_vuot_99_sinh_vien_bao_loi_va_de_xuat(self):
        c = self.as_user('pdt', 'pdt123'); lop = self.lop_khoa(c, 2024)
        con = sqlite3.connect(self.app.config['DATABASE'])
        con.execute('UPDATE BoDemMaSinhVien SET soCuoi=98 WHERE namTuyenSinh=2024'); con.commit()
        self.assertEqual(self.sv(c, maLop=lop).json['maSoSinhVien'], '2499')
        r = self.sv(c, maLop=lop)
        self.assertEqual(r.status_code, 409); self.assertIn('5 chu so', r.json['loi'])
        self.assertEqual(len([x for x in c.get('/api/danh-muc/sinh-vien').json if x['maSoSinhVien'].startswith('24') and len(x['maSoSinhVien']) != 4]), 0)

    def test_csdl_tu_choi_ma_sai_dinh_dang(self):
        con = sqlite3.connect(self.app.config['DATABASE'])
        for ma in ('SV0001X', '240', '24001', '2400', '2501'):    # 2501 khong khop khoa 2024
            with self.assertRaises(sqlite3.IntegrityError, msg=ma):
                con.execute("INSERT INTO SinhVien(maSoSinhVien,hoTen,maLop,namTuyenSinh) VALUES (?, 'X', 1, 2024)", (ma,))
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("INSERT INTO SinhVien(maSoSinhVien,hoTen,maLop,namTuyenSinh) VALUES ('2401', 'Trung', 1, 2024)")

    def test_sap_xep_mac_dinh_tang_dan_va_giam_dan(self):
        c = self.as_user('pdt', 'pdt123')
        ma = [x['maSoSinhVien'] for x in c.get('/api/danh-muc/sinh-vien').json]
        self.assertEqual(ma, sorted(ma)); self.assertEqual(ma[:3], ['2201', '2202', '2203'])
        self.assertEqual(ma[ma.index('2401') - 1][:2], '23')
        giam = [x['maSoSinhVien'] for x in c.get('/api/danh-muc/sinh-vien?thuTu=giam').json]
        self.assertEqual(giam, sorted(ma, reverse=True))

    def test_loc_tim_kiem_ket_hop_va_phan_trang_giu_thu_tu(self):
        c = self.as_user('pdt', 'pdt123')
        lop2025 = [x for x in c.get('/api/danh-muc/lop').json if x['namTuyenSinh'] == 2025][0]
        ds = c.get(f"/api/danh-muc/sinh-vien?namTuyenSinh=2025&maLop={lop2025['maLop']}&thuTu=giam").json
        self.assertTrue(ds); self.assertTrue(all(x['namTuyenSinh'] == 2025 and x['maLop'] == lop2025['maLop'] for x in ds))
        self.assertEqual([x['maSoSinhVien'] for x in ds], sorted((x['maSoSinhVien'] for x in ds), reverse=True))
        self.assertEqual(c.get(f"/api/danh-muc/sinh-vien?namTuyenSinh=2024&maLop={lop2025['maLop']}").json, [])   # loc ket hop
        tk = c.get('/api/danh-muc/sinh-vien?q=2601').json
        self.assertEqual([x['maSoSinhVien'] for x in tk], ['2601'])
        self.assertTrue(all(x['maSoSinhVien'].startswith('26') for x in c.get('/api/danh-muc/sinh-vien?q=26').json))
        # phan trang: ghep cac trang = toan bo danh sach, dung thu tu
        tat_ca = [x['maSoSinhVien'] for x in c.get('/api/danh-muc/sinh-vien?namTuyenSinh=2026').json]
        gop, trang = [], 1
        while True:
            r = c.get(f'/api/danh-muc/sinh-vien?namTuyenSinh=2026&trang={trang}&soDong=20').json
            gop += [x['maSoSinhVien'] for x in r['items']]
            if trang >= r['tongTrang']:
                break
            trang += 1
        self.assertEqual(gop, tat_ca); self.assertEqual(r['tong'], len(tat_ca))

    def test_tong_quan_khoa_tuyen_sinh_chi_pdt(self):
        r = self.as_user('pdt', 'pdt123').get('/api/danh-muc/khoa-tuyen-sinh').json
        self.assertEqual([x['namTuyenSinh'] for x in r][-4:], [2024, 2025, 2026, 2027])
        self.assertEqual(self.as_user(*SV_AN).get('/api/danh-muc/khoa-tuyen-sinh').status_code, 403)


class TestXuatThoiKhoaBieu(BaseTest):
    def text_pdf(self, data):
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(data))
        return r, '\n'.join(p.extract_text() for p in r.pages)

    def rows_xlsx(self, data):
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(data)).active
        return [[c for c in row] for row in ws.iter_rows(values_only=True)]

    def test_sinh_vien_xuat_pdf_a4_ngang_tieng_viet(self):
        c = self.as_user(*SV_AN)
        r = c.get(f'/api/tkb/xuat?dinhDang=pdf&tuan={TUAN}')
        self.assertEqual((r.status_code, r.mimetype), (200, 'application/pdf'))
        self.assertIn('attachment', r.headers['Content-Disposition'])
        pdf, txt = self.text_pdf(r.data)
        w, h = float(pdf.pages[0].mediabox.width), float(pdf.pages[0].mediabox.height)
        self.assertAlmostEqual(w, 841.89, delta=1); self.assertAlmostEqual(h, 595.28, delta=1)     # A4 ngang
        for t in ('TH\u1edcI KH\u00d3A BI\u1ec2U SINH VI\u00caN', 'Nguy\u1ec5n V\u0103n An', 'CNTT 1 - K24', 'Kh\u00f3a 2024',
                  '02/11/2026', '08/11/2026', 'Gi\u1ea3ng vi\u00ean', 'Ph\u00f2ng h\u1ecdc', 'Th\u1ee9 2'):
            self.assertIn(t, txt)

    def test_sinh_vien_xuat_excel_dung_lop_cua_minh(self):
        c = self.as_user(*SV_AN)
        r = c.get(f'/api/tkb/xuat?dinhDang=xlsx&tuan={TUAN}')
        self.assertEqual(r.status_code, 200); self.assertTrue(r.data[:2] == b'PK')
        rows = self.rows_xlsx(r.data)
        phang = ' | '.join(str(x) for row in rows for x in row if x)
        self.assertIn('Nguy\u1ec5n V\u0103n An', phang); self.assertIn('2401', phang)
        dau = [i for i, row in enumerate(rows) if row[0] == 'Th\u1ee9']
        self.assertEqual(rows[dau[0]][:8], ['Th\u1ee9', 'Ng\u00e0y h\u1ecdc', 'Ti\u1ebft', 'Gi\u1edd h\u1ecdc', 'M\u00f4n h\u1ecdc', 'Gi\u1ea3ng vi\u00ean', 'Ph\u00f2ng h\u1ecdc', 'Ghi ch\u00fa'])
        du = [row for row in rows[dau[0] + 1:] if row[1] and '/' in str(row[1])]
        api = c.get(f'/api/tkb?tuNgay=2026-11-02&denNgay=2026-11-08').json
        self.assertEqual(len(du), len(api)); self.assertTrue(du)
        self.assertEqual(sorted(x[4] for x in du), sorted(x['tenMonHoc'] for x in api))

    def test_giang_vien_xuat_pdf_va_excel_chi_lich_cua_minh(self):
        c = self.as_user(*GV_NAM)
        mine = c.get('/api/tkb?tuNgay=2026-11-02&denNgay=2026-11-08').json
        self.assertTrue(mine)
        _, txt = self.text_pdf(c.get(f'/api/tkb/xuat?dinhDang=pdf&tuan={TUAN}').data)
        self.assertIn('L\u1ecbch gi\u1ea3ng d\u1ea1y'.upper(), txt.upper()); self.assertIn('L\u00ea Ho\u00e0ng Nam', txt)
        rows = self.rows_xlsx(c.get(f'/api/tkb/xuat?dinhDang=xlsx&tuan={TUAN}').data)
        dau = [i for i, row in enumerate(rows) if row[0] == 'Th\u1ee9'][0]
        self.assertEqual(rows[dau][5], 'L\u1edbp')
        du = [row for row in rows[dau + 1:] if row[1] and '/' in str(row[1])]
        self.assertEqual(sorted((x[1], x[4], x[5]) for x in du),
                         sorted((x['ngayHoc'][8:] + '/' + x['ngayHoc'][5:7] + '/' + x['ngayHoc'][:4], x['tenMonHoc'], x['tenLop']) for x in mine))

    def test_khong_xuat_duoc_du_lieu_nguoi_khac(self):
        sv, gv = self.as_user(*SV_AN), self.as_user(*GV_NAM)
        for f in ('pdf', 'xlsx'):
            self.assertEqual(sv.get(f'/api/tkb/xuat?dinhDang={f}&maLop=3').status_code, 403)
            self.assertEqual(gv.get(f'/api/tkb/xuat?dinhDang={f}&maGiangVien=1').status_code, 403)
        # sinh vien 1 (lop khac) xuat ra du lieu khac sinh vien mau
        sv1 = self.as_user('sv1', 'sv123')
        a = self.rows_xlsx(sv1.get(f'/api/tkb/xuat?dinhDang=xlsx&tuan={TUAN}').data)
        self.assertIn('CNTT 1', ' '.join(str(x) for row in a for x in row if x)); self.assertNotIn('CNTT 1 - K24', ' '.join(str(x) for row in a for x in row if x))

    def test_phan_quyen_xuat(self):
        self.assertEqual(self.app.test_client().get('/api/tkb/xuat?dinhDang=pdf').status_code, 401)
        self.assertEqual(self.as_user('pdt', 'pdt123').get('/api/tkb/xuat?dinhDang=pdf').status_code, 403)
        c = self.as_user(*SV_AN)
        self.assertEqual(c.get('/api/tkb/xuat?dinhDang=doc').status_code, 400)
        self.assertEqual(c.get('/api/tkb/xuat?dinhDang=pdf&tuNgay=2026-11-09&denNgay=2026-11-02').status_code, 400)
        self.assertEqual(c.get('/api/tkb/xuat?dinhDang=pdf&tuNgay=2020-01-01&denNgay=2026-11-02').status_code, 400)
        self.assertEqual(c.get('/api/tkb/xuat?dinhDang=pdf&tuan=abc').status_code, 400)

    def test_tuan_trong_van_xuat_duoc_va_sv_gv_khong_sua_duoc_tkb(self):
        c = self.as_user(*SV_AN)
        r = c.get('/api/tkb/xuat?dinhDang=pdf&tuan=2030-01-07')
        self.assertEqual(r.status_code, 200); self.assertIn('Kh\u00f4ng c\u00f3 bu\u1ed5i h\u1ecdc', self.text_pdf(r.data)[1])
        for cl in (c, self.as_user(*GV_NAM)):
            self.assertEqual(cl.post('/api/tkb', json={}).status_code, 403)
            self.assertEqual(cl.put('/api/tkb/1', json={}).status_code, 403)
            self.assertEqual(cl.delete('/api/tkb/1').status_code, 403)

    def test_cell_bat_dau_bang_dau_bang_khong_thanh_cong_thuc(self):
        from tkb.services import xuat_tkb
        dl = dict(vaiTro='SINH_VIEN', tieuDe='T', thongTin=[('A', '=1+1')], cot=['a'] * 8, dong=[['=cmd'] + [''] * 7],
                  tuNgay=None, denNgay=None)
        from openpyxl import load_workbook
        ws = load_workbook(xuat_tkb.tao_xlsx(dl)).active
        self.assertEqual(ws['B4'].data_type, 's')


class TestThongBaoPhongDaoTao(BaseTest):
    def pdt(self):
        return self.as_user('pdt', 'pdt123')

    def gui(self, c, **kw):
        d = {'tieuDe': 'Tieu de', 'noiDung': 'Noi dung', 'loai': 'CHUNG', 'doiTuong': 'TAT_CA_SV'}
        d.update(kw); return c.post('/api/thong-bao', json=d)

    def ids(self, c, **q):
        return {n['maThongBao'] for n in c.get('/api/thong-bao', query_string=q).json}

    def test_tao_day_du_truong_va_6_loai(self):
        c = self.pdt()
        for loai in ('CHUNG', 'NGHI', 'DAY_BU', 'DOI_PHONG', 'DOI_LICH', 'QUAN_TRONG'):
            r = self.gui(c, loai=loai); self.assertEqual(r.status_code, 201, loai)
        n = r.json
        for k in ('maThongBao', 'tieuDe', 'noiDung', 'loai', 'tenLoai', 'nguoiGui', 'ngayTao', 'thoiGianGui', 'tenDoiTuong', 'trangThai'):
            self.assertIn(k, n)
        self.assertEqual((n['trangThai'], n['nguoiGui']), ('DA_GUI', 'Ph\u00f2ng \u0110\u00e0o t\u1ea1o'))
        self.assertEqual(self.gui(c, loai='LA').status_code, 400)
        self.assertEqual(self.gui(c, doiTuong='LOP').status_code, 400)            # thieu lop
        self.assertEqual(self.gui(c, doiTuong='GIANG_VIEN', maGiangVien=9999).status_code, 400)
        self.assertEqual(self.gui(c, tieuDe=' ').status_code, 400)

    def test_dung_doi_tuong_nhan(self):
        c = self.pdt()
        lop_an = self.as_user(*SV_AN).get('/api/toi').json['maLop']
        gv_nam = self.as_user(*GV_NAM).get('/api/toi').json['maGiangVien']
        n_sv = self.gui(c, doiTuong='TAT_CA_SV').json['maThongBao']
        n_gv = self.gui(c, doiTuong='TAT_CA_GV').json['maThongBao']
        n_lop = self.gui(c, doiTuong='LOP', maLop=lop_an).json['maThongBao']
        n_lop3 = self.gui(c, doiTuong='LOP', maLop=3).json['maThongBao']
        n_gv1 = self.gui(c, doiTuong='GIANG_VIEN', maGiangVien=gv_nam).json['maThongBao']
        n_gv2 = self.gui(c, doiTuong='GIANG_VIEN', maGiangVien=1).json['maThongBao']
        sv, sv_khac, gv, gv_khac = (self.as_user(*SV_AN), self.as_user('sv5', 'sv123'), self.as_user(*GV_NAM), self.as_user('gv1', 'gv123'))
        self.assertEqual(self.ids(sv) & {n_sv, n_gv, n_lop, n_lop3, n_gv1, n_gv2}, {n_sv, n_lop})
        self.assertEqual(self.ids(sv_khac) & {n_sv, n_gv, n_lop, n_lop3, n_gv1, n_gv2}, {n_sv, n_lop3})   # sv5 thuoc lop 3
        self.assertEqual(self.ids(gv) & {n_sv, n_gv, n_lop, n_lop3, n_gv1, n_gv2}, {n_gv, n_gv1})
        self.assertEqual(self.ids(gv_khac) & {n_sv, n_gv, n_lop, n_lop3, n_gv1, n_gv2}, {n_gv, n_gv2})
        # truy cap truc tiep thong bao cua doi tuong khac -> 403
        self.assertEqual(sv.get(f'/api/thong-bao/{n_gv}').status_code, 403)
        self.assertEqual(sv.get(f'/api/thong-bao/{n_lop3}').status_code, 403)
        self.assertEqual(gv.get(f'/api/thong-bao/{n_sv}').status_code, 403)
        self.assertEqual(gv.get(f'/api/thong-bao/{n_gv2}').status_code, 403)
        self.assertEqual(sv.get(f'/api/thong-bao/{n_sv}').status_code, 200)
        self.assertEqual(sv.get('/api/thong-bao/999999').status_code, 404)
        self.assertEqual(sv.post(f'/api/thong-bao/{n_gv}/da-doc').status_code, 403)

    def test_da_doc_chua_doc_va_dem(self):
        c = self.pdt(); sv = self.as_user(*SV_AN)
        dau = sv.get('/api/thong-bao/so-chua-doc').json['soChuaDoc']
        a = self.gui(c).json['maThongBao']; b = self.gui(c, doiTuong='LOP', maLop=sv.get('/api/toi').json['maLop']).json['maThongBao']
        self.gui(c, doiTuong='TAT_CA_GV')
        self.assertEqual(sv.get('/api/thong-bao/so-chua-doc').json['soChuaDoc'], dau + 2)
        ds = {n['maThongBao']: n for n in sv.get('/api/thong-bao').json}
        self.assertFalse(ds[a]['daDoc']); self.assertFalse(ds[b]['daDoc'])
        self.assertEqual(sv.post(f'/api/thong-bao/{a}/da-doc').json['soChuaDoc'], dau + 1)
        self.assertEqual(sv.post(f'/api/thong-bao/{a}/da-doc').json['soChuaDoc'], dau + 1)         # lap lai khong sao
        self.assertTrue({n['maThongBao']: n for n in sv.get('/api/thong-bao').json}[a]['daDoc'])
        self.assertEqual(self.ids(sv, chuaDoc=1) & {a, b}, {b})
        # trang thai doc la rieng tung nguoi
        self.assertFalse({n['maThongBao']: n for n in self.as_user('sv5', 'sv123').get('/api/thong-bao').json}[a]['daDoc'])
        self.assertEqual(sv.post('/api/thong-bao/da-doc-tat-ca').json['soChuaDoc'], 0)
        self.assertEqual(sv.get('/api/thong-bao/so-chua-doc').json['soChuaDoc'], 0)

    def test_chi_pdt_tao_sua_xoa(self):
        n = self.gui(self.pdt()).json['maThongBao']
        for cl in (self.as_user(*SV_AN), self.as_user(*GV_NAM), self.app.test_client()):
            codes = {cl.post('/api/thong-bao', json={'tieuDe': 'x', 'noiDung': 'y'}).status_code,
                     cl.put(f'/api/thong-bao/{n}', json={'tieuDe': 'x', 'noiDung': 'y'}).status_code,
                     cl.delete(f'/api/thong-bao/{n}').status_code, cl.post(f'/api/thong-bao/{n}/gui').status_code,
                     cl.post('/api/thong-bao/chung', json={'tieuDe': 'x', 'noiDung': 'y'}).status_code}
            self.assertTrue(codes <= {401, 403}, codes)
        self.assertIn(n, self.ids(self.pdt()))

    def test_sua_xoa_va_xem_chi_tiet(self):
        c = self.pdt(); n = self.gui(c).json['maThongBao']
        r = c.put(f'/api/thong-bao/{n}', json={'tieuDe': 'Moi', 'noiDung': 'Noi dung moi', 'loai': 'QUAN_TRONG', 'doiTuong': 'TAT_CA_GV'})
        self.assertEqual((r.status_code, r.json['tieuDe'], r.json['loai'], r.json['doiTuong']), (200, 'Moi', 'QUAN_TRONG', 'TAT_CA_GV'))
        self.assertIsNotNone(r.json['ngayCapNhat'])
        self.assertEqual(self.as_user(*SV_AN).get(f'/api/thong-bao/{n}').status_code, 403)        # sau khi doi doi tuong
        self.assertEqual(self.as_user(*GV_NAM).get(f'/api/thong-bao/{n}').json['noiDung'], 'Noi dung moi')
        self.assertEqual(c.delete(f'/api/thong-bao/{n}').status_code, 200)
        self.assertEqual(c.get(f'/api/thong-bao/{n}').status_code, 404)
        self.assertEqual(c.put(f'/api/thong-bao/{n}', json={'tieuDe': 'x', 'noiDung': 'y'}).status_code, 404)

    def test_ban_nhap_chi_pdt_thay_den_khi_gui(self):
        c = self.pdt(); sv = self.as_user(*SV_AN)
        n = self.gui(c, guiNgay=False).json
        self.assertEqual((n['trangThai'], n['thoiGianGui']), ('NHAP', None))
        self.assertNotIn(n['maThongBao'], self.ids(sv)); self.assertEqual(sv.get(f"/api/thong-bao/{n['maThongBao']}").status_code, 403)
        self.assertIn(n['maThongBao'], self.ids(c))
        r = c.post(f"/api/thong-bao/{n['maThongBao']}/gui")
        self.assertEqual((r.status_code, r.json['trangThai']), (200, 'DA_GUI')); self.assertTrue(r.json['thoiGianGui'])
        self.assertIn(n['maThongBao'], self.ids(sv))
        self.assertEqual(c.post(f"/api/thong-bao/{n['maThongBao']}/gui").status_code, 400)

    def test_thong_bao_tu_dong_va_cu_van_hoat_dong(self):
        c = self.pdt(); sv = self.as_user('sv1', 'sv123'); gv = self.as_user('gv1', 'gv123')
        ma = c.get('/api/tkb?ngay=2026-11-02&maLop=1').json[0]['maTKB']
        self.assertEqual(c.post(f'/api/tkb/{ma}/nghi-hoc', json={'lyDo': 'Bao'}).status_code, 200)
        self.assertEqual(c.post('/api/thong-bao/chung', json={'tieuDe': 'Chung', 'noiDung': 'ND'}).status_code, 200)
        for cl in (sv, gv):
            ds = cl.get('/api/thong-bao').json
            self.assertIn('NGHI', {n['loai'] for n in ds}); self.assertIn('Chung', {n['tieuDe'] for n in ds})
        self.assertNotIn('NGHI', {n['loai'] for n in self.as_user('sv5', 'sv123').get('/api/thong-bao').json})

    def test_pdt_khong_co_so_chua_doc_va_khong_danh_dau_doc(self):
        c = self.pdt()
        self.assertEqual(c.get('/api/thong-bao/so-chua-doc').json['soChuaDoc'], 0)
        self.assertEqual(c.post('/api/thong-bao/da-doc-tat-ca').status_code, 403)


class TestXacThucThamSo(BaseTest):
    def test_sinh_vien_giang_vien_khong_vao_api_quan_tri(self):
        for cl in (self.as_user(*SV_AN), self.as_user(*GV_NAM)):
            for m, u in (('get', '/api/danh-muc/sinh-vien'), ('get', '/api/danh-muc/giang-vien'), ('get', '/api/thong-ke'),
                         ('post', '/api/danh-muc/sinh-vien'), ('delete', '/api/danh-muc/sinh-vien/1'),
                         ('post', '/api/danh-muc/sinh-vien/1/cap-tai-khoan'), ('get', '/api/nhap-excel/sinh-vien/mau')):
                self.assertEqual(getattr(cl, m)(u).status_code, 403, (m, u))


if __name__ == '__main__':
    unittest.main()
