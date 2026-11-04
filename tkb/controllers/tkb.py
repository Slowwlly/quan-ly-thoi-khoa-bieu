from flask import Blueprint, jsonify, request
from ..auth import login_required, role_required
from ..config import PHONG_DAO_TAO
from ..db import get_db
from ..services import thoi_khoa_bieu as svc

bp = Blueprint('tkb', __name__, url_prefix='/api')


@bp.get('/tkb')
@login_required
def danh_sach(user):
    return jsonify(svc.danh_sach(get_db(), user, request.args.to_dict()))


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
