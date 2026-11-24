"""Nhap du lieu hang loat tu file Excel (.xlsx) hoac CSV.

Ho tro: sinh vien, giang vien, mon hoc, phong hoc, lop, khoa va buoi hoc (thoi khoa bieu).
Moi dong duoc xu ly rieng: dong hop le duoc luu, dong loi duoc bao cao (so dong + ly do).
Cac nghiep vu kiem tra (trung ma, trung lich...) dung lai dung ham tao() cua he thong.
"""
import csv
import io
import re
import unicodedata
from datetime import date, datetime

from ..errors import AppError
from . import danh_muc, thoi_khoa_bieu

TOI_DA_DONG = 5000
TOI_DA_BYTE = 5 * 1024 * 1024


# ---------------- Chuan hoa ten cot / gia tri ----------------
def _bo_dau(s):
    s = unicodedata.normalize('NFD', str(s).replace('đ', 'd').replace('Đ', 'D'))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def khoa_so_sanh(s):
    """Chu thuong, bo dau, bo ky tu thua: 'Điện - Điện tử 1' == 'dien dien tu 1'."""
    return re.sub(r'[^a-z0-9]+', ' ', _bo_dau(s).lower()).strip()


def _ten_cot(s):
    return khoa_so_sanh(s).replace(' ', '')


def _chuoi(v):
    """Excel hay tra so (123456.0) hoac ngay: dua ve chuoi gon."""
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (datetime, date)):
        return v.strftime('%Y-%m-%d')
    return str(v).strip()


# ---------------- Mo ta cot cua tung loai ----------------
# (khoa noi bo, tieu de trong file mau, bat buoc, cac ten cot chap nhan them)
_TK = [('tenDangNhap', 'Tên đăng nhập', False, ['taikhoan', 'username']),
       ('matKhau', 'Mật khẩu', False, ['password'])]

CAU_HINH = {
    'khoa': dict(
        ten='khoa', tep='mau_khoa', cot=[
            ('tenKhoa', 'Tên khoa', True, ['khoa'])],
        vi_du=['Công nghệ thông tin']),
    'lop': dict(
        ten='lớp', tep='mau_lop', cot=[
            ('tenLop', 'Tên lớp', True, ['malop', 'lop']),
            ('khoaHoc', 'Khóa học', False, ['khoa hoc', 'nienkhoa']),
            ('namTuyenSinh', 'Năm tuyển sinh', False, ['khoatuyensinh', 'namts']),
            ('khoa', 'Khoa', True, ['tenkhoa'])],
        vi_du=['CT2801', 'CNTT K28', 2028, 'Công nghệ thông tin']),
    'mon-hoc': dict(
        ten='môn học', tep='mau_mon_hoc', cot=[
            ('tenMonHoc', 'Tên môn học', True, ['monhoc', 'mon']),
            ('soTinChi', 'Số tín chỉ', True, ['tinchi', 'stc'])],
        vi_du=['Lập trình Java', 3]),
    'phong-hoc': dict(
        ten='phòng học', tep='mau_phong_hoc', cot=[
            ('tenPhong', 'Tên phòng', True, ['phong', 'phonghoc']),
            ('sucChua', 'Sức chứa', True, ['succhua', 'sosv'])],
        vi_du=['P501', 60]),
    'giang-vien': dict(
        ten='giảng viên', tep='mau_giang_vien', cot=[
            ('hoTen', 'Họ tên', True, ['tengiangvien', 'giangvien']),
            ('ngaySinh', 'Ngày sinh', True, ['ngaythangnamsinh']),
            ('email', 'Email', False, []),
            ('soDienThoai', 'Điện thoại', False, ['sdt', 'dienthoai', 'sodienthoai']),
            ('khoa', 'Khoa', True, ['tenkhoa'])],
        vi_du=['Nguyễn Văn A', '15/03/1985', 'a.nguyen@dhhp.edu.vn', '0912345678', 'Công nghệ thông tin']),
    'sinh-vien': dict(
        ten='sinh viên', tep='mau_sinh_vien', cot=[
            ('hoTen', 'Họ tên', True, ['tensinhvien', 'sinhvien']),
            ('ngaySinh', 'Ngày sinh', True, ['ngaythangnamsinh']),
            ('email', 'Email', False, []),
            ('soDienThoai', 'Điện thoại', False, ['sdt', 'dienthoai', 'sodienthoai']),
            ('lop', 'Lớp', True, ['tenlop', 'malop'])],
        vi_du=['Nguyễn Văn B', '15/03/2006', 'b.nguyen@sv.dhhp.edu.vn', '0910000031', 'CNTT 1 - K24']),
    'tkb': dict(
        ten='buổi học', tep='mau_buoi_hoc', cot=[
            ('ngayHoc', 'Ngày học', True, ['ngay']),
            ('tietBatDau', 'Tiết bắt đầu', True, ['tietbd', 'tubd', 'tiettu']),
            ('tietKetThuc', 'Tiết kết thúc', True, ['tietkt', 'tietden']),
            ('mon', 'Môn học', True, ['tenmonhoc', 'mon']),
            ('giangVien', 'Giảng viên', True, ['tengiangvien', 'gv']),
            ('lop', 'Lớp', True, ['tenlop', 'malop']),
            ('phong', 'Phòng', True, ['phonghoc', 'tenphong']),
            ('hocKy', 'Học kỳ', False, ['hk']),
            ('namHoc', 'Năm học', False, ['nam'])],
        vi_du=['2026-11-16', 1, 3, 'Lập trình Web', 'Nguyễn Văn A', 'CNTT 1', 'P101', 'HK1', '2026-2027']),
}


def cau_hinh(loai):
    if loai not in CAU_HINH:
        raise AppError('Loai du lieu khong duoc ho tro nhap file', 404)
    return CAU_HINH[loai]


# ---------------- Doc file ----------------
def _doc_xlsx(data):
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise AppError('May chu chua cai thu vien openpyxl. Chay: python -m pip install -r requirements.txt', 500)
    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception:
        raise AppError('Khong doc duoc file Excel (file hong hoac khong dung dinh dang .xlsx)')
    ws = wb.worksheets[0]  # luon doc sheet dau tien
    return [list(r) for r in ws.iter_rows(values_only=True)]


def _doc_csv(data):
    for enc in ('utf-8-sig', 'cp1258', 'cp1252'):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise AppError('Khong doc duoc file CSV (hay luu voi ma hoa UTF-8)')
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    return [row for row in csv.reader(io.StringIO(text), dialect)]


def doc_file(ten_file, data):
    """Tra ve (danh sach tieu de, danh sach (so dong, dong du lieu))."""
    if not data:
        raise AppError('File rong')
    if len(data) > TOI_DA_BYTE:
        raise AppError('File qua lon (toi da 5 MB)')
    ten = (ten_file or '').lower()
    if ten.endswith('.xlsx') or ten.endswith('.xlsm'):
        rows = _doc_xlsx(data)
    elif ten.endswith('.csv'):
        rows = _doc_csv(data)
    else:
        raise AppError('Chi ho tro file .xlsx hoac .csv (file .xls cu hay luu lai thanh .xlsx)')
    # Bo dong trong hoan toan; giu so dong that trong file de bao loi chinh xac.
    co_so_dong = [(i + 1, r) for i, r in enumerate(rows) if any(_chuoi(c) for c in r)]
    if not co_so_dong:
        raise AppError('File khong co du lieu')
    return co_so_dong[0][1], co_so_dong[1:]


# ---------------- Tra cuu ten -> ma ----------------
class _TraCuu:
    """Doi ten (khong phan biet hoa thuong/dau) thanh ma; bao loi neu khong co hoac trung ten."""

    def __init__(self, db, sql, cot_ten, cot_ma, nhan):
        self.nhan, self.map = nhan, {}
        for r in db.execute(sql):
            for t in cot_ten:
                if r[t]:
                    self.map.setdefault(khoa_so_sanh(r[t]), set()).add(r[cot_ma])

    def ma(self, ten):
        k = khoa_so_sanh(ten)
        ds = self.map.get(k)
        if not ds:
            raise AppError(f'{self.nhan} "{ten}" khong co trong he thong')
        if len(ds) > 1:
            raise AppError(f'{self.nhan} "{ten}" bi trung ten, khong xac dinh duoc')
        return next(iter(ds))


def _bo_tra_cuu(db):
    return {
        'khoa': _TraCuu(db, 'SELECT maKhoa, tenKhoa FROM Khoa', ['tenKhoa'], 'maKhoa', 'Khoa'),
        'lop': _TraCuu(db, 'SELECT maLop, tenLop, tenHienThi FROM Lop', ['tenLop', 'tenHienThi'], 'maLop', 'Lop'),
        'mon': _TraCuu(db, 'SELECT maMonHoc, tenMonHoc FROM MonHoc', ['tenMonHoc'], 'maMonHoc', 'Mon hoc'),
        'giangVien': _TraCuu(db, 'SELECT maGiangVien, hoTen FROM GiangVien', ['hoTen'], 'maGiangVien', 'Giang vien'),
        'phong': _TraCuu(db, 'SELECT maPhong, tenPhong FROM PhongHoc', ['tenPhong'], 'maPhong', 'Phong hoc'),
    }


def _ngay(v):
    """Chap nhan o ngay cua Excel, YYYY-MM-DD hoac dd/mm/yyyy (kieu Viet Nam)."""
    if isinstance(v, (datetime, date)):
        return v.strftime('%Y-%m-%d')
    s = _chuoi(v)
    m = re.fullmatch(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})', s)
    if m:
        d, mo, y = map(int, m.groups())
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            raise AppError(f'Ngay "{s}" khong hop le')
    return s  # de thoi_khoa_bieu bao loi dinh dang neu sai


# ---------------- Nhap ----------------
def _anh_xa_cot(cfg, tieu_de):
    """Tim cot nao trong file ung voi truong nao. Thieu cot bat buoc thi bao loi ngay."""
    chi_so = {}
    for i, t in enumerate(tieu_de):
        if _chuoi(t):
            chi_so.setdefault(_ten_cot(t), i)
    ket_qua, thieu = {}, []
    for ma, tieu, bat_buoc, bi_danh in cfg['cot']:
        ung_vien = [_ten_cot(tieu)] + [_ten_cot(b) for b in bi_danh]
        vt = next((chi_so[u] for u in ung_vien if u in chi_so), None)
        if vt is None:
            if bat_buoc:
                thieu.append(tieu)
        else:
            ket_qua[ma] = vt
    if thieu:
        raise AppError('File thieu cot bat buoc: ' + ', '.join(thieu) + '. Hay dung file mau.')
    return ket_qua


def _xu_ly_dong(db, loai, d, tra):
    if loai == 'tkb':
        v = {
            'ngayHoc': _ngay(d.get('ngayHoc')),
            'tietBatDau': _chuoi(d.get('tietBatDau')),
            'tietKetThuc': _chuoi(d.get('tietKetThuc')),
            'hocKy': _chuoi(d.get('hocKy')),
            'namHoc': _chuoi(d.get('namHoc')),
        }
        for truong, khoa_ma, khoa_ten in (('maMonHoc', 'mon', 'mon'), ('maGiangVien', 'giangVien', 'giangVien'),
                                          ('maLop', 'lop', 'lop'), ('maPhong', 'phong', 'phong')):
            ten = _chuoi(d.get(khoa_ten))
            if not ten:
                raise AppError(f'Thieu thong tin bat buoc: {khoa_ten}')
            v[truong] = tra[khoa_ma].ma(ten)
        thoi_khoa_bieu.tao(db, v)
        return
    v = {k: _chuoi(x) for k, x in d.items()}
    if loai in ('lop', 'giang-vien'):
        if not v.get('khoa'):
            raise AppError('Thieu thong tin bat buoc: khoa')
        v['maKhoa'] = tra['khoa'].ma(v['khoa'])
    if loai == 'sinh-vien':
        if not v.get('lop'):
            raise AppError('Thieu thong tin bat buoc: lop')
        v['maLop'] = tra['lop'].ma(v['lop'])
    danh_muc.tao(db, loai, v)


def _doi_ten_truong(cfg, thong_bao):
    """Doi ten truong noi bo (maSoSinhVien, maLop...) trong thong bao loi thanh ten cot trong file."""
    ten = {ma: tieu for ma, tieu, _, _ in cfg['cot']}
    ten.update({'maLop': 'Lớp', 'maKhoa': 'Khoa'})
    return re.sub(r'(?<=: )(\w+)$', lambda m: ten.get(m.group(1), m.group(1)), thong_bao)


def nhap(db, loai, ten_file, data):
    cfg = cau_hinh(loai)
    tieu_de, dong = doc_file(ten_file, data)
    if len(dong) > TOI_DA_DONG:
        raise AppError(f'File co qua nhieu dong (toi da {TOI_DA_DONG} dong moi lan)')
    cot = _anh_xa_cot(cfg, tieu_de)
    tra = _bo_tra_cuu(db)
    loi, thanh_cong = [], 0
    for so_dong, r in dong:
        d = {}
        for truong, vt in cot.items():
            d[truong] = r[vt] if vt < len(r) else None
        try:
            _xu_ly_dong(db, loai, d, tra)
            thanh_cong += 1
        except AppError as e:
            db.rollback()
            loi.append({'dong': so_dong, 'noiDung': _doi_ten_truong(cfg, e.message)})
    return {'tong': len(dong), 'thanhCong': thanh_cong, 'thatBai': len(loi), 'chiTietLoi': loi}


# ---------------- File mau ----------------
def tao_file_mau(db, loai):
    """File .xlsx gom: sheet 'Du lieu' (tieu de + 1 dong vi du) va sheet 'Danh sach hop le'."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise AppError('May chu chua cai thu vien openpyxl. Chay: python -m pip install -r requirements.txt', 500)
    cfg = cau_hinh(loai)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Du lieu'
    ws.append([c[1] + (' *' if c[2] else '') for c in cfg['cot']])
    ws.append(cfg['vi_du'])
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='1F4E79')
        c.alignment = Alignment(horizontal='center', vertical='center')
    for i in range(1, len(cfg['cot']) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 24
    # Cot ma / dien thoai / mat khau / ngay: dinh dang Van ban de Excel khong an so 0 dau
    van_ban = {'soDienThoai', 'ngaySinh', 'ngayHoc', 'namHoc', 'hocKy'}
    for i, c in enumerate(cfg['cot'], start=1):
        if c[0] in van_ban:
            for r in range(2, 1002):
                ws.cell(row=r, column=i).number_format = '@'
    ws.freeze_panes = 'A2'

    ghi_chu = wb.create_sheet('Huong dan')
    dong = ['Cot co dau * la bat buoc. Xoa dong vi du (dong 2) truoc khi nhap.',
            'Chi doc sheet dau tien. Toi da 5000 dong moi lan.']
    if loai == 'tkb':
        dong += ['Ngay hoc: dinh dang dd/mm/yyyy hoac yyyy-mm-dd.',
                 'Mon hoc, Giang vien, Lop, Phong: ghi dung ten nhu trong he thong (xem sheet "Danh sach hop le").',
                 'He thong van kiem tra trung lich giang vien / lop / phong nhu khi them tay.']
    if loai in ('sinh-vien', 'giang-vien'):
        dong += ['Ngay sinh: dd/mm/yyyy hoac yyyy-mm-dd. Tai khoan duoc tao tu dong: ten dang nhap = ho ten khong dau + ddmmyyyy; '
                 'mat khau ban dau = ho ten khong dau, khong cach, chi viet hoa chu dau + ddmmyyyy (vi du Nguyenvanan15032004).',
                 'Ma sinh vien duoc he thong tu cap theo khoa cua lop (vi du 2401); khong nhap ma.']
    for t in dong:
        ghi_chu.append([t])
    ghi_chu.column_dimensions['A'].width = 110

    tham_chieu = {
        'sinh-vien': [('Lớp', 'SELECT COALESCE(NULLIF(tenHienThi,\'\'),tenLop) FROM Lop ORDER BY tenLop')],
        'giang-vien': [('Khoa', 'SELECT tenKhoa FROM Khoa ORDER BY tenKhoa')],
        'lop': [('Khoa', 'SELECT tenKhoa FROM Khoa ORDER BY tenKhoa')],
        'tkb': [('Môn học', 'SELECT tenMonHoc FROM MonHoc ORDER BY tenMonHoc'),
                ('Giảng viên', 'SELECT hoTen FROM GiangVien ORDER BY hoTen'),
                ('Lớp', 'SELECT COALESCE(NULLIF(tenHienThi,\'\'),tenLop) FROM Lop ORDER BY tenLop'),
                ('Phòng', 'SELECT tenPhong FROM PhongHoc ORDER BY tenPhong')],
    }.get(loai)
    if tham_chieu:
        tc = wb.create_sheet('Danh sach hop le')
        cac_cot = [[t] + [r[0] for r in db.execute(sql)] for t, sql in tham_chieu]
        for i, cot in enumerate(cac_cot, start=1):
            for j, gia_tri in enumerate(cot, start=1):
                tc.cell(row=j, column=i, value=gia_tri)
            tc.cell(row=1, column=i).font = Font(bold=True)
            tc.column_dimensions[get_column_letter(i)].width = 28
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf, cfg['tep'] + '.xlsx'
