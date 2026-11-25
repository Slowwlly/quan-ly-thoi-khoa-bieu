"""Du lieu mau mo rong cho ung dung quan ly thoi khoa bieu.

Du lieu demo khong phai du lieu that cua Truong. Ham seed co tinh idempotent:
co the chay lai de bo sung du lieu mau ma khong xoa du lieu dang co.
"""
import random
import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from .migrations import suy_ra_nam_tuyen_sinh
from .services import dinh_danh, nguoi_dung, tai_khoan

MAU_TUAN = [
    (0, 1, 3, 'Ky nghe phan mem', 'gv1', 'CT2201', 'P101'),
    (0, 6, 8, 'Co so du lieu', 'gv1', 'CT2202', 'P102'),
    (1, 1, 3, 'Lap trinh Web', 'gv2', 'CT2201', 'P102'),
    (1, 4, 5, 'Lap trinh Web', 'gv2', 'CT2202', 'P101'),
    (2, 1, 3, 'Co so du lieu', 'gv1', 'CT2201', 'P101'),
    (2, 6, 8, 'Ky nghe phan mem', 'gv1', 'CT2202', 'P101'),
    (2, 1, 2, 'Kinh te vi mo', 'gv3', 'QT2201', 'P201'),
    (3, 6, 8, 'Tieng Anh chuyen nganh', 'gv4', 'CT2201', 'P102'),
    (3, 1, 3, 'Tieng Anh chuyen nganh', 'gv4', 'CT2202', 'P102'),
    (4, 1, 3, 'Lap trinh Web', 'gv2', 'CT2202', 'P101'),
    (4, 6, 7, 'Kinh te vi mo', 'gv3', 'QT2201', 'P201'),
]

KHOA_MO_RONG = [
    'Du lịch',
    'Ngoại ngữ',
    'Điện - Điện tử',
]
LOP_MO_RONG = [
    ('CT2301', 'CNTT K23', 'Cong nghe thong tin', 'gv5', 'sv7', 'sv9'),
    ('CT2302', 'CNTT K23', 'Cong nghe thong tin', 'gv6', 'sv10', 'sv12'),
    ('QTKD2301', 'QTKD K23', 'Quan tri kinh doanh', 'gv7', 'sv13', 'sv15'),
    ('DL2301', 'Du lich K23', 'Du lịch', 'gv8', 'sv16', 'sv18'),
    ('DL2302', 'Du lich K23', 'Du lịch', 'gv9', 'sv19', 'sv21'),
    ('NN2301', 'Ngoai ngu K23', 'Ngoại ngữ', 'gv10', 'sv22', 'sv24'),
    ('DDT2301', 'Dien tu K23', 'Điện - Điện tử', 'gv11', 'sv25', 'sv27'),
    ('DDT2302', 'Dien tu K23', 'Điện - Điện tử', 'gv12', 'sv28', 'sv30'),
]
GIANG_VIEN_MO_RONG = [
    ('gv5', 'Nguyễn Minh Đức', 'Cong nghe thong tin'),
    ('gv6', 'Trần Thu Hà', 'Cong nghe thong tin'),
    ('gv7', 'Lê Quang Huy', 'Quan tri kinh doanh'),
    ('gv8', 'Phạm Ngọc Anh', 'Du lịch'),
    ('gv9', 'Đỗ Tuấn Kiệt', 'Du lịch'),
    ('gv10', 'Vũ Mai Linh', 'Ngoại ngữ'),
    ('gv11', 'Bùi Đức Thắng', 'Điện - Điện tử'),
    ('gv12', 'Hoàng Khánh Vy', 'Điện - Điện tử'),
]
MON_HOC_MO_RONG = [
    ('Cấu trúc dữ liệu và giải thuật', 3),
    ('Lập trình Python', 3),
    ('Mạng máy tính', 3),
    ('Hệ điều hành', 3),
    ('Trí tuệ nhân tạo', 3),
    ('Phân tích thiết kế hệ thống', 3),
    ('Quản trị học', 3),
    ('Marketing căn bản', 3),
    ('Kế toán đại cương', 3),
    ('Nghiệp vụ hướng dẫn du lịch', 3),
    ('Quản trị khách sạn', 3),
    ('Tiếng Anh giao tiếp', 3),
    ('Tiếng Trung cơ bản', 3),
    ('Mạch điện tử', 3),
    ('Kỹ thuật số', 3),
]


def _id(con, sql, args):
    row = con.execute(sql, args).fetchone()
    return row[0] if row else None


def _tai_khoan(con, ten, mat_khau, vai_tro):
    ma = _id(con, 'SELECT maTaiKhoan FROM TaiKhoan WHERE tenDangNhap=?', (ten,))
    if ma:
        return ma
    return con.execute(
        'INSERT INTO TaiKhoan(tenDangNhap,matKhau,vaiTro) VALUES (?,?,?)',
        (ten, generate_password_hash(mat_khau), vai_tro)
    ).lastrowid


def _khoa(con, ten):
    ma = _id(con, 'SELECT maKhoa FROM Khoa WHERE tenKhoa=?', (ten,))
    return ma or con.execute('INSERT INTO Khoa(tenKhoa) VALUES (?)', (ten,)).lastrowid


def _lop(con, ten, khoa_hoc, ma_khoa, nam=None):
    nam = nam or suy_ra_nam_tuyen_sinh(khoa_hoc, ten)
    ma = _id(con, 'SELECT maLop FROM Lop WHERE tenLop=?', (ten,))
    if ma:
        con.execute('UPDATE Lop SET namTuyenSinh=? WHERE maLop=? AND namTuyenSinh IS NULL', (nam, ma))
        return ma
    return con.execute(
        'INSERT INTO Lop(tenLop,khoaHoc,namTuyenSinh,maKhoa) VALUES (?,?,?,?)',
        (ten, khoa_hoc, nam, ma_khoa)
    ).lastrowid


def _mon(con, ten, tin_chi=3):
    ma = _id(con, 'SELECT maMonHoc FROM MonHoc WHERE tenMonHoc=?', (ten,))
    return ma or con.execute(
        'INSERT INTO MonHoc(tenMonHoc,soTinChi) VALUES (?,?)', (ten, tin_chi)
    ).lastrowid


def _phong(con, ten, suc_chua=45):
    ma = _id(con, 'SELECT maPhong FROM PhongHoc WHERE tenPhong=?', (ten,))
    return ma or con.execute(
        'INSERT INTO PhongHoc(tenPhong,sucChua) VALUES (?,?)', (ten, suc_chua)
    ).lastrowid


def _giang_vien(con, username, ho_ten, ma_khoa):
    """Giang vien demo cu: nhan dien theo (ho ten, khoa) - KHONG theo ten dang nhap vi tai khoan da doi theo quy tac.
    Tai khoan tao bang CUNG ham quy tac voi tai khoan moi (ho ten + ngay sinh)."""
    ma = _id(con, 'SELECT maGiangVien FROM GiangVien WHERE hoTen=? AND maKhoa=?', (ho_ten, ma_khoa))
    if ma:
        return ma
    ma = con.execute('SELECT COALESCE(MAX(maGiangVien), 0) + 1 FROM GiangVien').fetchone()[0]
    ngay = dinh_danh.ngay_sinh_demo('GIANG_VIEN', ma).isoformat()
    ma_tk, _ = tai_khoan.tao_theo_quy_tac(con, ho_ten, ngay, 'GIANG_VIEN', True)
    return con.execute(
        'INSERT INTO GiangVien(maGiangVien,hoTen,ngaySinh,email,soDienThoai,maKhoa,maTaiKhoan) VALUES (?,?,?,?,?,?,?)',
        (ma, ho_ten, ngay, f'{username}@dhhp.edu.vn', f'090{int(username[2:]):07d}', ma_khoa, ma_tk)
    ).lastrowid


def _sinh_vien(con, username, ho_ten, ma_lop):
    """Sinh vien demo cu: nhan dien theo (ho ten, lop). Ma sinh vien cap theo khoa, tai khoan theo quy tac."""
    ma = _id(con, 'SELECT maSinhVien FROM SinhVien WHERE hoTen=? AND maLop=?', (ho_ten, ma_lop))
    if ma:
        return ma
    ma_sv = con.execute(
        'SELECT COALESCE(MAX(maSinhVien), 0) + 1 FROM SinhVien'
    ).fetchone()[0]
    nam = con.execute('SELECT namTuyenSinh FROM Lop WHERE maLop=?', (ma_lop,)).fetchone()[0]
    ngay = dinh_danh.ngay_sinh_demo('SINH_VIEN', ma_sv, nam).isoformat()
    ma_tk, _ = tai_khoan.tao_theo_quy_tac(con, ho_ten, ngay, 'SINH_VIEN', True)
    return con.execute(
        'INSERT INTO SinhVien(maSinhVien,maSoSinhVien,hoTen,ngaySinh,email,soDienThoai,namTuyenSinh,maLop,maTaiKhoan) '
        'VALUES (?,?,?,?,?,?,?,?,?)',
        (ma_sv, nguoi_dung.cap_ma_sinh_vien(con, nam), ho_ten, ngay, f'{username}@sv.dhhp.edu.vn',
         f'091{int(username[2:]):07d}', nam, ma_lop, ma_tk)
    ).lastrowid


def seed(path, today=None, so_tuan_truoc=2, so_tuan_sau=6):
    today = today or date.today()
    con = sqlite3.connect(path)
    con.execute('PRAGMA foreign_keys = ON')
    try:
        # Phong dao tao va cac khoa co ban.
        _tai_khoan(con, 'pdt', 'pdt123', 'PHONG_DAO_TAO')
        khoa = {}
        for ten in ('Cong nghe thong tin', 'Quan tri kinh doanh', *KHOA_MO_RONG):
            khoa[ten] = _khoa(con, ten)

        # Cac lop co san, giu nguyen ma lop/ma khoa da duoc tao truoc do.
        lop = {}
        for ten, kh, ten_khoa in (
            ('CT2201', 'CNTT K22', 'Cong nghe thong tin'),
            ('CT2202', 'CNTT K22', 'Cong nghe thong tin'),
            ('QT2201', 'QTKD K22', 'Quan tri kinh doanh'),
        ):
            lop[ten] = _lop(con, ten, kh, khoa[ten_khoa])

        # Giang vien co san.
        gv = {}
        for ma, ten, kh in (
            ('gv1', 'Nguyen Van An', 'Cong nghe thong tin'),
            ('gv2', 'Tran Thi Binh', 'Cong nghe thong tin'),
            ('gv3', 'Le Van Cuong', 'Quan tri kinh doanh'),
            ('gv4', 'Pham Thi Dung', 'Cong nghe thong tin'),
        ):
            gv[ma] = _giang_vien(con, ma, ten, khoa[kh])

        # Sinh vien co san.
        sinh_vien_cu = [
            ('sv1', 'Hoang Van Em', 'CT2201'), ('sv2', 'Vu Thi Phuong', 'CT2201'),
            ('sv3', 'Do Van Giang', 'CT2202'), ('sv4', 'Bui Thi Ha', 'CT2202'),
            ('sv5', 'Ngo Van Hai', 'QT2201'), ('sv6', 'Dinh Thi Lan', 'QT2201'),
        ]
        for username, ten, ten_lop in sinh_vien_cu:
            _sinh_vien(con, username, ten, lop[ten_lop])

        # Mon hoc va phong hoc ban dau.
        mon = {}
        for ten in sorted({r[3] for r in MAU_TUAN}):
            mon[ten] = _mon(con, ten, 3)
        # Phong hoc duoc dat ten day du theo toa va tang, vi du: Toa C3 - P305.
        # Doi ten cac phong mau cu de giu nguyen maPhong va cac TKB da tham chieu.
        phong = {}
        phong_cu = [
            ('P101', 'Tòa C3 - P101', 50),
            ('P102', 'Tòa C3 - P102', 40),
            ('P201', 'Tòa C3 - P201', 60),
            ('P301', 'Tòa C3 - P301', 30),
        ]
        for ten_cu, ten_day_du, suc_chua in phong_cu:
            con.execute('UPDATE PhongHoc SET tenPhong=? WHERE tenPhong=?', (ten_day_du, ten_cu))
            phong[ten_cu] = _phong(con, ten_day_du, suc_chua)

        # So do toa nha tham khao tu so do khu giang duong cua truong.
        # Moi toa co 4 tang, moi tang co cac phong 01-09.
        cac_toa = ('C1', 'C3', 'C5', 'C6', 'C7', 'B3', 'B4', 'B5', 'B7', 'B10')
        for toa in cac_toa:
            for tang in range(1, 5):
                for so_phong in range(1, 10):
                    ma_phong = tang * 100 + so_phong
                    ten_day_du = f'Tòa {toa} - P{ma_phong}'
                    _phong(con, ten_day_du, 45)

        # Lich co ban chi tao neu chua co ban ghi tuong ung.
        thu_hai = today - timedelta(days=today.weekday())
        for w in range(-so_tuan_truoc, so_tuan_sau + 1):
            for thu, bd, kt, ten_mon, ten_gv, ten_lop, ten_phong in MAU_TUAN:
                ngay = (thu_hai + timedelta(weeks=w, days=thu)).isoformat()
                if not con.execute(
                    'SELECT 1 FROM ThoiKhoaBieu WHERE ngayHoc=? AND tietBatDau=? AND tietKetThuc=? '
                    'AND maGiangVien=? AND maLop=? AND maPhong=?',
                    (ngay, bd, kt, gv[ten_gv], lop[ten_lop], phong[ten_phong])
                ).fetchone():
                    con.execute(
                        'INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,hocKy,namHoc,maGiangVien,maMonHoc,maLop,maPhong) '
                        'VALUES (?,?,?,?,?,?,?,?,?)',
                        (ngay, bd, kt, 'HK1', '2026-2027', gv[ten_gv], mon[ten_mon], lop[ten_lop], phong[ten_phong])
                    )

        # Bo sung khoa, lop, giang vien va sinh vien de du lieu demo phong phu hon.
        lop_moi = {}
        for ten_lop, khoa_hoc, ten_khoa, ten_gv, sv_dau, sv_cuoi in LOP_MO_RONG:
            lop_moi[ten_lop] = _lop(con, ten_lop, khoa_hoc, khoa[ten_khoa])

        gv_moi = {}
        for username, ten, ten_khoa in GIANG_VIEN_MO_RONG:
            gv_moi[username] = _giang_vien(con, username, ten, khoa[ten_khoa])

        # Dien thong tin lien he con thieu cho du lieu demo cu, khong ghi de thong tin da co.
        con.execute("UPDATE GiangVien SET soDienThoai='0900000001' WHERE soDienThoai IS NULL AND maGiangVien=1")
        con.execute("UPDATE GiangVien SET soDienThoai='0900000002' WHERE soDienThoai IS NULL AND maGiangVien=2")
        con.execute("UPDATE SinhVien SET soDienThoai='0910000001' WHERE soDienThoai IS NULL AND maSinhVien=1")
        con.execute("UPDATE SinhVien SET soDienThoai='0910000002' WHERE soDienThoai IS NULL AND maSinhVien=2")

        # 3 sinh vien moi cho moi lop mo rong.
        ten_sv = [
            'Nguyễn Đức Anh', 'Trần Bảo Châu', 'Lê Gia Bảo', 'Phạm Minh Châu',
            'Đỗ Hoàng Nam', 'Vũ Thu Trang', 'Bùi Quốc Việt', 'Hoàng Mai Anh',
            'Đặng Tuấn Anh', 'Ngô Phương Thảo', 'Mai Thanh Tùng', 'Đinh Ngọc Hà',
            'Trương Minh Quân', 'Phan Thu Hiền', 'Cao Đức Minh', 'Lý Khánh Linh',
            'Tạ Quang Huy', 'Nguyễn Hà My', 'Dương Anh Khoa', 'Hồ Thị Yến',
            'Trịnh Đức Long', 'Bạch Ngọc Hân', 'Lương Minh Khang', 'Đặng Thu Hà',
        ]
        sv_index = 7
        for ten_lop, _khoa_hoc, _ten_khoa, _ten_gv, _sv_dau, _sv_cuoi in LOP_MO_RONG:
            for _ in range(3):
                _sinh_vien(con, f'sv{sv_index}', ten_sv[sv_index - 7], lop_moi[ten_lop])
                sv_index += 1

        for ten, tin_chi in MON_HOC_MO_RONG:
            mon[ten] = _mon(con, ten, tin_chi)

        # Phong rieng cho cac lop moi, tranh trung phong voi lich cu.
        for i, (ten_lop, _khoa_hoc, _ten_khoa, ten_gv, _sv_dau, _sv_cuoi) in enumerate(LOP_MO_RONG, 1):
            ten_phong = f'Tòa B10 - P40{i}'
            ma_phong = _phong(con, ten_phong, 45)

            # Lich 3 buoi/tuan, lap lai trong khoang tuan demo. Moi lop co GV/phong rieng.
            # Cac tiet va ngay khong trung nhau trong cung lop.
            lich = [
                (1, 1, 3, MON_HOC_MO_RONG[(i - 1) % len(MON_HOC_MO_RONG)][0]),
                (3, 6, 8, MON_HOC_MO_RONG[(i + 3) % len(MON_HOC_MO_RONG)][0]),
                (5, 1, 3, MON_HOC_MO_RONG[(i + 7) % len(MON_HOC_MO_RONG)][0]),
            ]
            for w in range(-so_tuan_truoc, so_tuan_sau + 1):
                for thu, bd, kt, ten_mon in lich:
                    ngay = (thu_hai + timedelta(weeks=w, days=thu)).isoformat()
                    exists = con.execute(
                        'SELECT 1 FROM ThoiKhoaBieu WHERE ngayHoc=? AND maLop=? AND tietBatDau=? AND tietKetThuc=?',
                        (ngay, lop_moi[ten_lop], bd, kt)
                    ).fetchone()
                    if not exists:
                        con.execute(
                            'INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,hocKy,namHoc,maGiangVien,maMonHoc,maLop,maPhong) '
                            'VALUES (?,?,?,?,?,?,?,?,?)',
                            (ngay, bd, kt, 'HK1', '2026-2027', gv_moi[ten_gv], mon[ten_mon],
                             lop_moi[ten_lop], ma_phong)
                        )

        # Ten lop hien thi than thien; giu tenLop goc de seed va khoa ngoai khong doi.
        ten_lop_hien_thi = {
            'CT2201': 'CNTT 1',
            'CT2202': 'CNTT 2',
            'CT2301': 'CNTT 3',
            'CT2302': 'CNTT 4',
            'QT2201': 'QTKD 1',
            'QTKD2301': 'QTKD 2',
            'DL2301': 'Du lịch 1',
            'DL2302': 'Du lịch 2',
            'NN2301': 'Ngoại ngữ 1',
            'DDT2301': 'Điện - Điện tử 1',
            'DDT2302': 'Điện - Điện tử 2',
        }
        for ma_lop, ten_hien_thi in ten_lop_hien_thi.items():
            con.execute(
                'UPDATE Lop SET tenHienThi=? WHERE tenLop=?',
                (ten_hien_thi, ma_lop)
            )

        seed_bon_khoa(con, today, so_tuan_truoc, so_tuan_sau, khoa, mon)
        con.commit()
        return True
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ======================================================================
# Du lieu mau 4 khoa tuyen sinh 2024-2027 (tai khoan theo quy tac ho ten + ngay sinh)
# ======================================================================
KHOA_TUYEN_SINH = (2024, 2025, 2026, 2027)
# (tien to ten lop, ten hien thi, ten khoa/nganh, so lop moi khoa, so sinh vien moi lop, cac mon)
NGANH_MAU = [
    ('CT', 'CNTT', 'Cong nghe thong tin', 4, 6,
     ['Cấu trúc dữ liệu và giải thuật', 'Lập trình Python', 'Mạng máy tính', 'Hệ điều hành',
      'Trí tuệ nhân tạo', 'Phân tích thiết kế hệ thống']),
    ('QTKD', 'QTKD', 'Quan tri kinh doanh', 2, 5, ['Quản trị học', 'Marketing căn bản', 'Kế toán đại cương']),
    ('DL', 'Du lịch', 'Du lịch', 1, 5, ['Nghiệp vụ hướng dẫn du lịch', 'Quản trị khách sạn', 'Marketing căn bản']),
    ('NN', 'Ngoại ngữ', 'Ngoại ngữ', 1, 5, ['Tiếng Anh giao tiếp', 'Tiếng Trung cơ bản', 'Tiếng Anh chuyên ngành']),
    ('DDT', 'Điện - Điện tử', 'Điện - Điện tử', 1, 5, ['Mạch điện tử', 'Kỹ thuật số', 'Mạng máy tính']),
]
GIANG_VIEN_QUY_TAC = [   # (ho ten, ngay sinh, khoa) - 2 den 4 nguoi moi nganh
    ('Lê Hoàng Nam', '1985-05-12', 'Cong nghe thong tin'), ('Phạm Thị Thu Hà', '1988-11-03', 'Cong nghe thong tin'),
    ('Ngô Quang Vinh', '1983-02-21', 'Cong nghe thong tin'), ('Đinh Mai Phương', '1990-07-30', 'Cong nghe thong tin'),
    ('Vũ Đức Trọng', '1980-09-14', 'Quan tri kinh doanh'), ('Bùi Thanh Hằng', '1987-01-25', 'Quan tri kinh doanh'),
    ('Đặng Minh Tuấn', '1984-04-08', 'Du lịch'), ('Hoàng Thị Lan Anh', '1991-12-17', 'Du lịch'),
    ('Trịnh Văn Khánh', '1982-06-19', 'Ngoại ngữ'), ('Lương Thị Ngọc Bích', '1989-10-05', 'Ngoại ngữ'),
    ('Cao Xuân Bách', '1981-03-27', 'Điện - Điện tử'), ('Tạ Thị Hồng Nhung', '1986-08-11', 'Điện - Điện tử'),
]
PDT_QUY_TAC = ('Trần Thị Minh Anh', '2003-09-08')
SV_MAU_DAU_TIEN = ('Nguyễn Văn An', '2004-03-15')   # SV dau tien khoa 2024 (vi du trong yeu cau)
_HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Ngô', 'Dương', 'Lý', 'Phan', 'Đinh',
       'Trịnh', 'Mai', 'Hồ', 'Lương', 'Cao', 'Tạ']
_NAM = (['Văn', 'Đức', 'Quốc', 'Minh', 'Hữu', 'Gia', 'Bảo'],
        ['Anh', 'Bình', 'Cường', 'Dũng', 'Đạt', 'Hiếu', 'Hùng', 'Huy', 'Khoa', 'Long', 'Nam', 'Phúc', 'Quân', 'Sơn',
         'Thắng', 'Tuấn', 'Việt'])
_NU = (['Thị', 'Thu', 'Ngọc', 'Mai', 'Khánh', 'Phương'],
       ['Anh', 'Chi', 'Dung', 'Hà', 'Hạnh', 'Hoa', 'Hương', 'Lan', 'Linh', 'My', 'Ngân', 'Nhung', 'Thảo', 'Trang', 'Vy', 'Yến'])
# 20 khung gio khong trung nhau trong tuan (thu 2-6) cho moi giang vien
_KHUNG = [(thu, bd, kt) for bd, kt in ((1, 3), (6, 8), (4, 5), (9, 10)) for thu in range(5)]
_TOA = [f'Tòa {t} - P{tang * 100 + so}' for t in ('B3', 'B4', 'B5', 'B7') for tang in range(1, 5) for so in range(1, 10)]


def _tao_nguoi_ten(rng, da_dung):
    for _ in range(1000):
        nu = rng.random() < .5
        gh, gt = _NU if nu else _NAM
        ten = f'{rng.choice(_HO)} {rng.choice(gh)} {rng.choice(gt)}'
        if ten not in da_dung:
            da_dung.add(ten)
            return ten
    raise RuntimeError('Het ten mau')


def seed_bon_khoa(con, today, so_tuan_truoc, so_tuan_sau, khoa, mon):
    """Lop + sinh vien + giang vien tai khoan theo quy tac (chi tao MOT LAN); lich hoc bo sung theo tuan nhu cu."""
    lop_theo_nganh = {}      # tien to -> [(ten lop, nam)]
    for nam in KHOA_TUYEN_SINH:
        for tt, hien_thi, ten_khoa, so_lop, _sv, _m in NGANH_MAU:
            for k in range(1, so_lop + 1):
                ten = f'{tt}{nam % 100}{k:02d}'
                lop_theo_nganh.setdefault(tt, []).append((ten, nam, k, hien_thi, ten_khoa))

    da_seed = con.execute("SELECT 1 FROM CauHinhHeThong WHERE khoa='seed_4_khoa_v1'").fetchone()
    gv_ma = {}
    for ho_ten, ngay, ten_khoa in GIANG_VIEN_QUY_TAC:
        r = con.execute('SELECT maGiangVien FROM GiangVien WHERE hoTen=? AND ngaySinh=?', (ho_ten, ngay)).fetchone()
        if r:
            gv_ma[(ho_ten, ngay)] = r[0]
        elif not da_seed:
            ma_tk, _ = tai_khoan.tao_theo_quy_tac(con, ho_ten, ngay, 'GIANG_VIEN', True)
            slug = dinh_danh.bo_dau(ho_ten).lower().replace(' ', '.')
            gv_ma[(ho_ten, ngay)] = con.execute(
                'INSERT INTO GiangVien(hoTen,ngaySinh,email,soDienThoai,maKhoa,maTaiKhoan) VALUES (?,?,?,?,?,?)',
                (ho_ten, ngay, f'{slug}@dhhp.edu.vn', f'0920{len(gv_ma):06d}', khoa[ten_khoa], ma_tk)).lastrowid

    if not da_seed:
        ho_ten, ngay = PDT_QUY_TAC
        if not con.execute('SELECT 1 FROM TaiKhoan WHERE hoTen=? AND ngaySinh=?', (ho_ten, ngay)).fetchone():
            ten_dn = dinh_danh.tao_ten_dang_nhap(ho_ten, ngay)
            if not con.execute('SELECT 1 FROM TaiKhoan WHERE tenDangNhap=?', (ten_dn,)).fetchone():
                tai_khoan.tao_tai_khoan(con, ten_dn, dinh_danh.tao_mat_khau(ho_ten, ngay), 'PHONG_DAO_TAO',
                                        phai_doi=1, ho_ten=ho_ten, ngay_sinh=date.fromisoformat(ngay))
        da_dung = {SV_MAU_DAU_TIEN[0]}
        for nam in KHOA_TUYEN_SINH:
            rng = random.Random(nam)
            for tt, hien_thi, ten_khoa, _sl, so_sv, _m in NGANH_MAU:
                for ten, n, k, _h, _t in [x for x in lop_theo_nganh[tt] if x[1] == nam]:
                    ma_lop = _lop(con, ten, f'{hien_thi} K{nam % 100}', khoa[ten_khoa], nam)
                    con.execute('UPDATE Lop SET tenHienThi=? WHERE maLop=?', (f'{hien_thi} {k} - K{nam % 100}', ma_lop))
                    for i in range(so_sv):
                        if nam == 2024 and tt == 'CT' and k == 1 and i == 0:
                            ho, ngay_sinh = SV_MAU_DAU_TIEN[0], SV_MAU_DAU_TIEN[1]
                        else:
                            ho = _tao_nguoi_ten(rng, da_dung)
                            ngay_sinh = date(nam - 18 - rng.randint(0, 1), rng.randint(1, 12), rng.randint(1, 28)).isoformat()
                        try:
                            ma_tk, _ = tai_khoan.tao_theo_quy_tac(con, ho, ngay_sinh, 'SINH_VIEN', True)
                        except Exception:
                            continue
                        ma_so = nguoi_dung.cap_ma_sinh_vien(con, nam)
                        con.execute(
                            'INSERT INTO SinhVien(maSoSinhVien,hoTen,ngaySinh,email,soDienThoai,namTuyenSinh,maLop,maTaiKhoan) '
                            'VALUES (?,?,?,?,?,?,?,?)',
                            (ma_so, ho, ngay_sinh, f'{ma_so}@sv.dhhp.edu.vn', f'0930{int(ma_so):06d}', nam, ma_lop, ma_tk))
        con.execute("INSERT INTO CauHinhHeThong(khoa, giaTri) VALUES ('seed_4_khoa_v1', datetime('now','localtime'))")

    # Lich hoc: moi lop 3 buoi/tuan. Gan giang vien/phong/khung gio theo cong thuc co dinh -> khong trung lich.
    thu_hai = today - timedelta(days=today.weekday())
    dem_gv, idx_lop = {}, 0
    for tt, hien_thi, ten_khoa, _sl, _sv, ds_mon in NGANH_MAU:
        gv_nganh = [g for g in GIANG_VIEN_QUY_TAC if g[2] == ten_khoa]
        for stt, (ten, nam, k, _h, _t) in enumerate(lop_theo_nganh[tt]):
            ma_lop = _id(con, 'SELECT maLop FROM Lop WHERE tenLop=?', (ten,))
            g = gv_nganh[stt % len(gv_nganh)]
            ma_gv = gv_ma.get((g[0], g[1]))
            idx_lop += 1
            if not ma_lop or not ma_gv:
                continue
            ma_phong = _phong(con, _TOA[(idx_lop - 1) % len(_TOA)], 45)
            for s_ in range(3):
                dem = dem_gv.get(ma_gv, 0); dem_gv[ma_gv] = dem + 1
                thu, bd, kt = _KHUNG[dem % len(_KHUNG)]
                ma_mon = _mon(con, ds_mon[(stt + s_) % len(ds_mon)], 3)
                for w in range(-so_tuan_truoc, so_tuan_sau + 1):
                    ngay = (thu_hai + timedelta(weeks=w, days=thu)).isoformat()
                    if not con.execute('SELECT 1 FROM ThoiKhoaBieu WHERE ngayHoc=? AND maLop=? AND tietBatDau=? AND tietKetThuc=?',
                                       (ngay, ma_lop, bd, kt)).fetchone():
                        con.execute('INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,hocKy,namHoc,maGiangVien,maMonHoc,maLop,maPhong) '
                                    'VALUES (?,?,?,?,?,?,?,?,?)', (ngay, bd, kt, 'HK1', '2026-2027', ma_gv, ma_mon, ma_lop, ma_phong))
