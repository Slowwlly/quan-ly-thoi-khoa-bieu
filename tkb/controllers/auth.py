from flask import Blueprint, jsonify, request, session
from ..auth import login_required
from ..config import TIET, VAI_TRO_TEN
from ..db import get_db
from ..services import tai_khoan

bp = Blueprint('auth', __name__, url_prefix='/api')


def _body():
    return request.get_json(silent=True) or {}


@bp.post('/dang-nhap')
def dang_nhap():
    d = _body()
    tk = tai_khoan.xac_thuc(get_db(), d.get('tenDangNhap'), d.get('matKhau'))
    session.clear()
    session['maTaiKhoan'] = tk['maTaiKhoan']
    session.permanent = False
    return jsonify({'thongBao': 'Dang nhap thanh cong', 'vaiTro': tk['vaiTro']})


@bp.post('/dang-xuat')
def dang_xuat():
    session.clear()
    return jsonify({'thongBao': 'Da dang xuat'})


@bp.get('/toi')
@login_required
def toi(user):
    return jsonify({**user, 'tenVaiTro': VAI_TRO_TEN[user['vaiTro']],
                    'tiet': [{'tiet': t, 'tu': a, 'den': b} for t, a, b in TIET]})


@bp.post('/doi-mat-khau')
@login_required
def doi_mat_khau(user):
    d = _body()
    tai_khoan.doi_mat_khau(get_db(), user['maTaiKhoan'], d.get('matKhauCu'), d.get('matKhauMoi'))
    return jsonify({'thongBao': 'Da doi mat khau'})
