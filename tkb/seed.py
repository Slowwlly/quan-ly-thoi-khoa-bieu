"""Du lieu mau mo rong cho ung dung quan ly thoi khoa bieu.

Du lieu demo khong phai du lieu that cua Truong. Ham seed co tinh idempotent:
co the chay lai de bo sung du lieu mau ma khong xoa du lieu dang co.
"""
import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

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


def _lop(con, ten, khoa_hoc, ma_khoa):
    ma = _id(con, 'SELECT maLop FROM Lop WHERE tenLop=?', (ten,))
    return ma or con.execute(
        'INSERT INTO Lop(tenLop,khoaHoc,maKhoa) VALUES (?,?,?)',
        (ten, khoa_hoc, ma_khoa)
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
    ma_tk = _tai_khoan(con, username, 'gv123', 'GIANG_VIEN')
    ma = _id(con, 'SELECT maGiangVien FROM GiangVien WHERE maTaiKhoan=?', (ma_tk,))
    if ma:
        return ma
    return con.execute(
        'INSERT INTO GiangVien(hoTen,email,soDienThoai,maKhoa,maTaiKhoan) VALUES (?,?,?,?,?)',
        (ho_ten, f'{username}@dhhp.edu.vn', f'090{int(username[2:]):07d}', ma_khoa, ma_tk)
    ).lastrowid


def _sinh_vien(con, username, ho_ten, ma_lop):
    ma_tk = _tai_khoan(con, username, 'sv123', 'SINH_VIEN')
    ma = _id(con, 'SELECT maSinhVien FROM SinhVien WHERE maTaiKhoan=?', (ma_tk,))
    if ma:
        return ma
    return con.execute(
        'INSERT INTO SinhVien(hoTen,email,soDienThoai,maLop,maTaiKhoan) VALUES (?,?,?,?,?)',
        (ho_ten, f'{username}@sv.dhhp.edu.vn', f'091{int(username[2:]):07d}', ma_lop, ma_tk)
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

        con.commit()
        return True
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
