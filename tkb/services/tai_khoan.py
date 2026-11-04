from werkzeug.security import check_password_hash, generate_password_hash
from ..config import MAT_KHAU_TOI_THIEU
from ..errors import AppError


def xac_thuc(db, ten_dang_nhap, mat_khau):
    """Tra ve dong TaiKhoan neu hop le, nguoc lai nem loi (cung mot thong bao cho ca hai truong hop sai)."""
    ten_dang_nhap = (ten_dang_nhap or '').strip()
    if not ten_dang_nhap or not mat_khau:
        raise AppError('Vui long nhap tai khoan va mat khau', 400)
    tk = db.execute('SELECT * FROM TaiKhoan WHERE tenDangNhap=?', (ten_dang_nhap,)).fetchone()
    if tk is None or not check_password_hash(tk['matKhau'], mat_khau):
        raise AppError('Tai khoan hoac mat khau khong dung', 401)
    return tk


def tao_tai_khoan(db, ten_dang_nhap, mat_khau, vai_tro):
    ten_dang_nhap = (ten_dang_nhap or '').strip()
    kiem_tra_mat_khau(mat_khau)
    if not ten_dang_nhap:
        raise AppError('Ten dang nhap khong duoc de trong')
    if db.execute('SELECT 1 FROM TaiKhoan WHERE tenDangNhap=?', (ten_dang_nhap,)).fetchone():
        raise AppError('Ten dang nhap da ton tai', 409)
    cur = db.execute('INSERT INTO TaiKhoan(tenDangNhap, matKhau, vaiTro) VALUES (?,?,?)',
                     (ten_dang_nhap, generate_password_hash(mat_khau), vai_tro))
    return cur.lastrowid


def kiem_tra_mat_khau(mat_khau):
    if not mat_khau or len(mat_khau) < MAT_KHAU_TOI_THIEU:
        raise AppError(f'Mat khau phai co it nhat {MAT_KHAU_TOI_THIEU} ky tu')


def doi_mat_khau(db, ma_tai_khoan, cu, moi):
    tk = db.execute('SELECT * FROM TaiKhoan WHERE maTaiKhoan=?', (ma_tai_khoan,)).fetchone()
    if tk is None or not check_password_hash(tk['matKhau'], cu or ''):
        raise AppError('Mat khau hien tai khong dung', 400)
    kiem_tra_mat_khau(moi)
    db.execute('UPDATE TaiKhoan SET matKhau=? WHERE maTaiKhoan=?', (generate_password_hash(moi), ma_tai_khoan))
    db.commit()
