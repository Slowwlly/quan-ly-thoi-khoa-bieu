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
        self.assertTrue(all(x['tenLop'] == 'CT2201' for x in ds))

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
        self.assertEqual(r.status_code, 201); self.assertEqual(r.json['tenPhong'], 'P301')
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

    def test_tao_giang_vien_kem_tai_khoan(self):
        c = self.as_user('pdt', 'pdt123')
        r = c.post('/api/danh-muc/giang-vien', json={'hoTen': 'Mau Thu', 'maKhoa': 1, 'tenDangNhap': 'gv9', 'matKhau': 'matkhau9'})
        self.assertEqual(r.status_code, 201); self.assertEqual(r.json['tenDangNhap'], 'gv9')
        self.assertEqual(self.login('gv9', 'matkhau9').json['vaiTro'], 'GIANG_VIEN')

    def test_danh_muc_tim_kiem_va_loc_cho_moi_nguoi(self):
        c = self.as_user('sv1', 'sv123')
        self.assertEqual(c.get('/api/danh-muc/lop').status_code, 200)
        self.assertEqual(len(self.as_user('pdt', 'pdt123').get('/api/danh-muc/sinh-vien?q=Hoang').json), 1)

    def test_thong_ke(self):
        r = self.as_user('pdt', 'pdt123').get('/api/thong-ke')
        self.assertEqual(r.status_code, 200); self.assertGreater(r.json['tongSoBuoi'], 0)


if __name__ == '__main__':
    unittest.main()
