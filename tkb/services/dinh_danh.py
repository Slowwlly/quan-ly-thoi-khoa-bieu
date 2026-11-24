"""Quy tac tao ten dang nhap / mat khau ban dau / kiem tra ngay sinh.

Ten dang nhap = ho ten viet thuong, khong dau, khong khoang trang + ddmmyyyy
Mat khau      = ho ten KHONG dau, KHONG khoang trang, chi viet hoa chu cai dau tien + ddmmyyyy
"""
import re
import unicodedata
from datetime import date, datetime

from ..errors import AppError

_HOP_LE = re.compile(r"^[^\W\d_]+(?:[ '.\-][^\W\d_]+)*$", re.UNICODE)


def bo_dau(s):
    s = unicodedata.normalize('NFD', str(s).replace('đ', 'd').replace('Đ', 'D'))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def chuan_hoa_ho_ten(ho_ten):
    s = unicodedata.normalize('NFC', str(ho_ten or ''))
    s = re.sub(r'\s+', ' ', s).strip()
    if not s:
        raise AppError('Ho ten khong duoc de trong')
    if len(s) > 100 or not _HOP_LE.match(s):
        raise AppError('Ho ten chi duoc chua chu cai, khoang trang va dau - . \'')
    return s


def parse_ngay_sinh(v):
    """Nhan date, 'YYYY-MM-DD' hoac 'dd/mm/yyyy'. Tra ve date."""
    if isinstance(v, datetime):
        v = v.date()
    if isinstance(v, date):
        d = v
    else:
        s = str(v or '').strip()
        m = re.fullmatch(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})', s)
        try:
            d = date(int(m[3]), int(m[2]), int(m[1])) if m else date.fromisoformat(s)
        except (ValueError, TypeError):
            raise AppError('Ngay sinh khong hop le (dinh dang YYYY-MM-DD hoac dd/mm/yyyy)')
    if d.year < 1900 or d > date.today():
        raise AppError('Ngay sinh khong hop le')
    return d


def ddmmyyyy(d):
    return f'{d.day:02d}{d.month:02d}{d.year:04d}'


def tao_ten_dang_nhap(ho_ten, ngay_sinh):
    ten = re.sub(r'[^a-z0-9]', '', bo_dau(chuan_hoa_ho_ten(ho_ten)).lower())
    if not ten:
        raise AppError('Ho ten khong hop le')
    return ten + ddmmyyyy(parse_ngay_sinh(ngay_sinh))


def tao_mat_khau(ho_ten, ngay_sinh):
    """Nguyen Van An, 15/03/2004 -> Nguyenvanan15032004"""
    ten = re.sub(r'[^a-z0-9]', '', bo_dau(chuan_hoa_ho_ten(ho_ten)).lower())
    if not ten:
        raise AppError('Ho ten khong hop le')
    return ten[0].upper() + ten[1:] + ddmmyyyy(parse_ngay_sinh(ngay_sinh))
