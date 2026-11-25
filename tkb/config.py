"""Cau hinh nghiep vu. Bang tiet duoi day la GIA DINH - hay sua theo quy dinh cua Truong."""
GIANG_VIEN, SINH_VIEN, PHONG_DAO_TAO = 'GIANG_VIEN', 'SINH_VIEN', 'PHONG_DAO_TAO'
VAI_TRO_TEN = {GIANG_VIEN: 'Giang vien', SINH_VIEN: 'Sinh vien', PHONG_DAO_TAO: 'Phong dao tao'}

TIET = [  # (so tiet, gio bat dau, gio ket thuc)
    (1, '07:00', '07:50'), (2, '07:55', '08:45'), (3, '08:50', '09:40'),
    (4, '09:50', '10:40'), (5, '10:45', '11:35'),
    (6, '13:00', '13:50'), (7, '13:55', '14:45'), (8, '14:50', '15:40'),
    (9, '15:50', '16:40'), (10, '16:45', '17:35'),
]
SO_TIET = len(TIET)
MAT_KHAU_TOI_THIEU = 6

# ---- Bo sung: ma sinh vien, thong bao ----
SO_SV_TOI_DA_MOI_KHOA = 99   # ma sinh vien = 2 so nam + 2 so thu tu (01-99)
LOAI_THONG_BAO = {
    # Phong Dao tao
    'CHUNG': 'Thông báo chung', 'NGHI': 'Nghỉ học', 'DAY_BU': 'Học bù',
    'DOI_PHONG': 'Thay đổi phòng học', 'DOI_LICH': 'Thay đổi lịch học',
    'QUAN_TRONG': 'Thông báo quan trọng',
    # Giang vien
    'GV_CHUNG': 'Thông báo chung của giảng viên', 'NHAC_LICH': 'Nhắc lịch học',
    'DOI_NOI_DUNG': 'Thay đổi nội dung buổi học', 'TAI_LIEU': 'Chuẩn bị tài liệu học tập',
    'KIEM_TRA': 'Nhắc kiểm tra hoặc thi', 'KHAC': 'Thông báo khác',
}
# Doi tuong PDT duoc chon khi tao thong bao thu cong.
DOI_TUONG_NHAP = ('TAT_CA_SV', 'TAT_CA_GV', 'LOP', 'GIANG_VIEN', 'TAT_CA')

# ---- Thong bao cua giang vien ----
SENDER_PDT, SENDER_GV = 'PHONG_DAO_TAO', 'GIANG_VIEN'
NHAN_NGUON_GUI = {SENDER_PDT: 'PHÒNG ĐÀO TẠO', SENDER_GV: 'GIẢNG VIÊN'}
# Loai thong bao moi ben duoc phep chon (NGHI, DAY_BU dung chung ten voi Phong Dao tao)
LOAI_PDT = ('CHUNG', 'NGHI', 'DAY_BU', 'DOI_PHONG', 'DOI_LICH', 'QUAN_TRONG')
LOAI_GV = ('GV_CHUNG', 'NHAC_LICH', 'DOI_NOI_DUNG', 'TAI_LIEU', 'KIEM_TRA', 'NGHI', 'DAY_BU', 'KHAC')
GV_SUA_TOI_DA_GIO = 24        # sau ngay gui nay, thong bao cua giang vien bi khoa (khong sua/xoa duoc)
GV_LOP_NGAY_TRUOC = 30        # lop "dang day" = co buoi hoc tu (hom nay - 30 ngay) tro di
