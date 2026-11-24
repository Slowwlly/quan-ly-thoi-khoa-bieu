"""Xuat thoi khoa bieu ra PDF (A4 ngang) va Excel (.xlsx) cho sinh vien / giang vien.

Pham vi du lieu LUON lay qua thoi_khoa_bieu.danh_sach(): sinh vien chi co lop cua minh, giang vien chi co lich
cua minh (neu gui maLop/maGiangVien cua nguoi khac se bi tu choi 403 o backend).
"""
import io
import os
import re
from datetime import date, datetime, timedelta

from ..config import GIANG_VIEN, SINH_VIEN, TIET
from ..errors import AppError
from . import dinh_danh
from . import thoi_khoa_bieu as tkb

THU = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
TOI_DA_NGAY = 400


def _fmt(d):
    return f'{d.day:02d}/{d.month:02d}/{d.year}'


def khoang_ngay(p):
    if p.get('tuNgay') or p.get('denNgay'):
        tu = tkb.parse_ngay(p.get('tuNgay') or p.get('denNgay'), 'tu ngay')
        den = tkb.parse_ngay(p.get('denNgay') or p.get('tuNgay'), 'den ngay')
    else:
        tu, den = tkb.khoang_tuan(tkb.parse_ngay(p['tuan'], 'ngay trong tuan') if p.get('tuan') else date.today())
    if den < tu:
        raise AppError('Ngay ket thuc khong duoc truoc ngay bat dau')
    if (den - tu).days > TOI_DA_NGAY:
        raise AppError(f'Chi duoc xuat toi da {TOI_DA_NGAY} ngay moi lan')
    return tu, den


def lay_du_lieu(db, user, p):
    """Tra ve dict: loai, tieuDe, thongTin [(nhan, gia tri)], cot, dong, tuNgay, denNgay, tenFile."""
    if user['vaiTro'] not in (SINH_VIEN, GIANG_VIEN):
        raise AppError('Chi sinh vien va giang vien duoc xuat thoi khoa bieu', 403)
    tu, den = khoang_ngay(p)
    loc = {'tuNgay': tu.isoformat(), 'denNgay': den.isoformat()}
    for k in ('maLop', 'maGiangVien'):          # de tkb.danh_sach tu choi neu vuot quyen
        if p.get(k) not in (None, ''):
            loc[k] = p[k]
    buoi = tkb.danh_sach(db, user, loc)
    sv = user['vaiTro'] == SINH_VIEN
    if sv:
        r = db.execute("""SELECT s.hoTen, s.maSoSinhVien, s.namTuyenSinh, COALESCE(NULLIF(l.tenHienThi,''),l.tenLop) AS lop,
                          k.tenKhoa FROM SinhVien s JOIN Lop l ON l.maLop=s.maLop JOIN Khoa k ON k.maKhoa=l.maKhoa
                          WHERE s.maSinhVien=?""", (user['maSinhVien'],)).fetchone()
        ten, ma_ten = r['hoTen'], r['maSoSinhVien']
        info = [('Họ và tên', r['hoTen']), ('Mã sinh viên', r['maSoSinhVien']), ('Lớp', r['lop']),
                ('Khóa', f"Khóa {r['namTuyenSinh']}" if r['namTuyenSinh'] else '—'), ('Ngành/Khoa', r['tenKhoa'])]
        tieu_de = 'THỜI KHÓA BIỂU SINH VIÊN'
        cot = ['Thứ', 'Ngày học', 'Tiết', 'Giờ học', 'Môn học', 'Giảng viên', 'Phòng học', 'Ghi chú']
    else:
        r = db.execute("""SELECT g.hoTen, k.tenKhoa FROM GiangVien g JOIN Khoa k ON k.maKhoa=g.maKhoa
                          WHERE g.maGiangVien=?""", (user['maGiangVien'],)).fetchone()
        ten = ma_ten = dinh_danh.bo_dau(r['hoTen']).replace(' ', '')
        info = [('Họ và tên', r['hoTen']), ('Khoa', r['tenKhoa'])]
        tieu_de = 'LỊCH GIẢNG DẠY GIẢNG VIÊN'
        cot = ['Thứ', 'Ngày dạy', 'Tiết', 'Giờ dạy', 'Môn học', 'Lớp', 'Phòng học', 'Ghi chú']
    hk = sorted({f"{b['hocKy'] or ''} {b['namHoc'] or ''}".strip() for b in buoi} - {''})
    ap_dung = f'Từ {_fmt(tu)} đến {_fmt(den)}'
    info.append(('Thời gian áp dụng', ap_dung + (f" ({'; '.join(hk)})" if hk else '')))
    dong = []
    for b in buoi:
        d = date.fromisoformat(b['ngayHoc'])
        gio = f"{TIET[b['tietBatDau'] - 1][1]}–{TIET[b['tietKetThuc'] - 1][2]}"
        doi = b['tenGiangVien'] if sv else b['tenLop']
        dong.append([THU[d.weekday()], _fmt(d), f"{b['tietBatDau']}–{b['tietKetThuc']}", gio, b['tenMonHoc'], doi,
                     b['tenPhong'], 'Nghỉ học' if b['daNghi'] else ''])
    ten_file = re.sub(r'[^A-Za-z0-9_-]+', '', f'TKB_{ma_ten}_{tu.isoformat()}_{den.isoformat()}')
    return dict(vaiTro=user['vaiTro'], tieuDe=tieu_de, thongTin=info, cot=cot, dong=dong, tuNgay=tu, denNgay=den,
                tenFile=ten_file, nguoi=ten)


# ---------------- Excel ----------------
def tao_xlsx(dl):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook(); ws = wb.active
    ws.title = 'Thoi khoa bieu'
    n = len(dl['cot'])
    mep = Side(style='thin', color='999999'); vien = Border(left=mep, right=mep, top=mep, bottom=mep)

    def ghi(o, v, **kw):          # chuoi bat dau bang = + - @ khong duoc bien thanh cong thuc
        o.value = v
        if isinstance(v, str) and v[:1] in '=+-@':
            o.data_type = 's'
        return o

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
    ghi(ws.cell(1, 1), 'TRƯỜNG ĐẠI HỌC HẢI PHÒNG').font = Font(bold=True, size=11)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n)
    c = ghi(ws.cell(2, 1), dl['tieuDe']); c.font = Font(bold=True, size=16, color='1F4E79')
    c.alignment = Alignment(horizontal='center')
    r = 4
    for nhan, gt in dl['thongTin']:
        ghi(ws.cell(r, 1), nhan + ':').font = Font(bold=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=n)
        ghi(ws.cell(r, 2), gt)
        r += 1
    r += 1
    dau = r
    for i, t in enumerate(dl['cot'], 1):
        c = ghi(ws.cell(r, i), t)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F4E79')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = vien
    if dl['dong']:
        for row in dl['dong']:
            r += 1
            for i, v in enumerate(row, 1):
                c = ghi(ws.cell(r, i), v)
                c.alignment = Alignment(vertical='top', wrap_text=True, horizontal='center' if i in (1, 2, 3, 4) else 'left')
                c.border = vien
    else:
        r += 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=n)
        ghi(ws.cell(r, 1), 'Không có buổi học trong khoảng thời gian này.').alignment = Alignment(horizontal='center')
    for i, w in enumerate([11, 13, 8, 14, 34, 28, 22, 13], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(dau + 1, 1)
    ws.page_setup.orientation = 'landscape'; ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f'{dau}:{dau}'
    ws.cell(r + 2, 1).value = f'Xuất ngày {datetime.now():%d/%m/%Y %H:%M}'
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf


# ---------------- PDF ----------------
_font_ok = False


def _dang_ky_font():
    global _font_ok
    if _font_ok:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('VN', os.path.join(FONT_DIR, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('VN-B', os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('VN', normal='VN', bold='VN-B', italic='VN', boldItalic='VN-B')
    _font_ok = True


def tao_pdf(dl):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape
    _dang_ky_font()
    st = lambda **k: ParagraphStyle('x', fontName='VN', fontSize=9, leading=11.5, **k)
    chu = st(); dam = ParagraphStyle('b', parent=chu, fontName='VN-B')
    tieu = ParagraphStyle('t', parent=chu, fontName='VN-B', fontSize=16, leading=20, alignment=1,
                          textColor=colors.HexColor('#1F4E79'))
    truong = ParagraphStyle('s', parent=chu, fontName='VN-B', fontSize=10)
    dau = ParagraphStyle('h', parent=chu, fontName='VN-B', textColor=colors.white, alignment=1)
    giua = ParagraphStyle('c', parent=chu, alignment=1)
    P = lambda t, s=chu: Paragraph(escape(str(t)), s)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm,
                            bottomMargin=16 * mm, title=dl['tieuDe'], author='Trường Đại học Hải Phòng')
    ds = [P('TRƯỜNG ĐẠI HỌC HẢI PHÒNG', truong), Spacer(1, 3 * mm), P(dl['tieuDe'], tieu), Spacer(1, 4 * mm)]
    info = Table([[P(n + ':', dam), P(g)] for n, g in dl['thongTin']], colWidths=[40 * mm, 220 * mm])
    info.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                              ('TOPPADDING', (0, 0), (-1, -1), 1)]))
    ds += [info, Spacer(1, 4 * mm)]
    rong = [18, 24, 14, 28, 62, 50, 42, 22]       # tong 260mm = A4 ngang tru le
    du = [[P(t, dau) for t in dl['cot']]]
    for row in dl['dong']:
        du.append([P(v, giua if i in (0, 1, 2, 3) else chu) for i, v in enumerate(row)])
    if not dl['dong']:
        du.append([P('Không có buổi học trong khoảng thời gian này.', giua)] + [''] * (len(dl['cot']) - 1))
    bang = Table(du, colWidths=[w * mm for w in rong], repeatRows=1)
    kieu = [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')), ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#8A8A8A')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EEF3F9')])]
    if not dl['dong']:
        kieu.append(('SPAN', (0, 1), (-1, 1)))
    bang.setStyle(TableStyle(kieu))
    ds.append(bang)
    gio = datetime.now().strftime('%d/%m/%Y %H:%M')

    def chan(canvas, d):
        canvas.saveState(); canvas.setFont('VN', 8); canvas.setFillColor(colors.HexColor('#555555'))
        canvas.drawString(12 * mm, 9 * mm, f'Xuất ngày {gio}')
        canvas.drawRightString(landscape(A4)[0] - 12 * mm, 9 * mm, f'Trang {d.page}')
        canvas.restoreState()
    doc.build(ds, onFirstPage=chan, onLaterPages=chan)
    buf.seek(0)
    return buf
