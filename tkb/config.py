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
