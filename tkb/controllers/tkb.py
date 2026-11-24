from flask import Blueprint, jsonify, request, send_file
from ..auth import login_required, role_required
from ..config import PHONG_DAO_TAO, SINH_VIEN, GIANG_VIEN
from ..errors import AppError
from ..db import get_db
from ..services import thoi_khoa_bieu as svc
from ..services import xuat_tkb

bp = Blueprint('tkb', __name__, url_prefix='/api')


@bp.get('/tkb')
@login_required
def danh_sach(user):
    return jsonify(svc.danh_sach(get_db(), user, request.args.to_dict()))


@bp.get('/tkb/xuat')
@role_required(SINH_VIEN, GIANG_VIEN)
def xuat(user):
    """Xuat TKB cua chinh nguoi dung: ?dinhDang=pdf|xlsx&tuan=YYYY-MM-DD hoac &tuNgay=&denNgay="""
    p = request.args.to_dict()
    dinh_dang = (p.get('dinhDang') or '').lower()
    if dinh_dang not in ('pdf', 'xlsx'):
        raise AppError('Dinh dang xuat chi co the la pdf hoac xlsx')
    dl = xuat_tkb.lay_du_lieu(get_db(), user, p)
    if dinh_dang == 'pdf':
        buf, mime = xuat_tkb.tao_pdf(dl), 'application/pdf'
    else:
        buf, mime = xuat_tkb.tao_xlsx(dl), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=f"{dl['tenFile']}.{dinh_dang}")


@bp.get('/tkb/<int:ma>')
@login_required
def chi_tiet(user, ma):
    return jsonify(svc.chi_tiet(get_db(), user, ma))


@bp.post('/tkb')
@role_required(PHONG_DAO_TAO)
def tao(user):
    return jsonify(svc.tao(get_db(), request.get_json(silent=True) or {})), 201


@bp.put('/tkb/<int:ma>')
@role_required(PHONG_DAO_TAO)
def sua(user, ma):
    return jsonify(svc.sua(get_db(), ma, request.get_json(silent=True) or {}))


@bp.delete('/tkb/<int:ma>')
@role_required(PHONG_DAO_TAO)
def xoa(user, ma):
    svc.xoa(get_db(), ma)
    return jsonify({'thongBao': 'Da xoa buoi hoc'})


@bp.get('/thong-ke')
@role_required(PHONG_DAO_TAO)
def thong_ke(user):
    return jsonify(svc.thong_ke(get_db()))
