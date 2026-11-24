import unicodedata
from werkzeug.security import check_password_hash, generate_password_hash
from ..config import MAT_KHAU_TOI_THIEU
from ..errors import AppError, Conflict
from . import dinh_danh


def xac_thuc(db, ten_dang_nhap, mat_khau):
    """Tra ve dong TaiKhoan neu hop le, nguoc lai nem loi (cung mot thong bao cho ca hai truong hop sai)."""
    ten_dang_nhap = (ten_dang_nhap or '').strip()
    if not ten_dang_nhap or not mat_khau or not isinstance(mat_khau, str):
        raise AppError('Vui long nhap tai khoan va mat khau', 400)
    tk = db.execute('SELECT * FROM TaiKhoan WHERE lower(tenDangNhap)=lower(?)', (ten_dang_nhap,)).fetchone()
    # Mat khau co dau co the o dang NFC hoac NFD tuy ban phim/he dieu hanh: thu ca hai.
    thu = {mat_khau, unicodedata.normalize('NFC', mat_khau)}
    if tk is None or not any(check_password_hash(tk['matKhau'], m) for m in thu):
        raise AppError('Tai khoan hoac mat khau khong dung', 401)
    return tk


def kiem_tra_mat_khau(mat_khau):
    if not mat_khau or len(mat_khau) < MAT_KHAU_TOI_THIEU:
        raise AppError(f'Mat khau phai co it nhat {MAT_KHAU_TOI_THIEU} ky tu')


def tao_tai_khoan(db, ten_dang_nhap, mat_khau, vai_tro, phai_doi=0, ho_ten=None, ngay_sinh=None):
    ten_dang_nhap = (ten_dang_nhap or '').strip()
    kiem_tra_mat_khau(mat_khau)
    if not ten_dang_nhap:
        raise AppError('Ten dang nhap khong duoc de trong')
    if db.execute('SELECT 1 FROM TaiKhoan WHERE lower(tenDangNhap)=lower(?)', (ten_dang_nhap,)).fetchone():
        raise Conflict('Ten dang nhap da ton tai')
    cur = db.execute('INSERT INTO TaiKhoan(tenDangNhap, matKhau, vaiTro, phaiDoiMatKhau, hoTen, ngaySinh) VALUES (?,?,?,?,?,?)',
                     (ten_dang_nhap, generate_password_hash(mat_khau), vai_tro, phai_doi, ho_ten,
                      ngay_sinh.isoformat() if ngay_sinh else None))
    return cur.lastrowid


def tao_theo_quy_tac(db, ho_ten, ngay_sinh, vai_tro, chap_nhan_hau_to=False):
    """Tao tai khoan theo quy tac ho ten + ngay sinh. Trung ten dang nhap: KHONG ghi de.
    Neu chua duoc dong y dung hau to thi nem Conflict kem goi y (tenDangNhapDeXuat)."""
    ho_ten = dinh_danh.chuan_hoa_ho_ten(ho_ten)
    ngay = dinh_danh.parse_ngay_sinh(ngay_sinh)
    goc = dinh_danh.tao_ten_dang_nhap(ho_ten, ngay)
    mat_khau = dinh_danh.tao_mat_khau(ho_ten, ngay)
    ten, n = goc, 1
    while db.execute('SELECT 1 FROM TaiKhoan WHERE lower(tenDangNhap)=lower(?)', (ten,)).fetchone():
        n += 1
        ten = f'{goc}_{n}'
    if ten != goc:
        if not chap_nhan_hau_to:
            e = Conflict(f'Tên đăng nhập "{goc}" đã tồn tại (trùng họ tên và ngày sinh). '
                         f'Đề xuất dùng "{ten}" (thêm hậu tố _{n}); mật khẩu ban đầu vẫn theo quy tắc chung.')
            e.goi_y = {'tenDangNhapDeXuat': ten, 'tenDangNhapGoc': goc}
            raise e
    ma = tao_tai_khoan(db, ten, mat_khau, vai_tro, phai_doi=1)
    return ma, ten


def doi_mat_khau(db, ma_tai_khoan, cu, moi, xac_nhan=None):
    tk = db.execute('SELECT * FROM TaiKhoan WHERE maTaiKhoan=?', (ma_tai_khoan,)).fetchone()
    cu = cu or ''
    if tk is None or not any(check_password_hash(tk['matKhau'], m) for m in {cu, unicodedata.normalize('NFC', cu)}):
        raise AppError('Mat khau hien tai khong dung', 400)
    kiem_tra_mat_khau(moi)
    if xac_nhan is not None and xac_nhan != moi:
        raise AppError('Mat khau moi va xac nhan mat khau khong khop')
    if moi == cu:
        raise AppError('Mat khau moi phai khac mat khau hien tai')
    db.execute('UPDATE TaiKhoan SET matKhau=?, phaiDoiMatKhau=0 WHERE maTaiKhoan=?',
               (generate_password_hash(unicodedata.normalize('NFC', moi)), ma_tai_khoan))
    db.commit()
