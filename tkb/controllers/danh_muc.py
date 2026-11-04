from flask import Blueprint, jsonify, request
from ..auth import login_required, role_required
from ..config import PHONG_DAO_TAO
from ..db import get_db
from ..errors import Forbidden
from ..services import danh_muc as svc

bp = Blueprint('danh_muc', __name__, url_prefix='/api/danh-muc')

# Danh muc dung cho o loc cua moi nguoi dung da dang nhap; con lai chi Phong dao tao.
CHO_PHEP_XEM_CHUNG = {'lop', 'mon-hoc', 'phong-hoc'}


@bp.get('/<ten>')
@login_required
def danh_sach(user, ten):
    if user['vaiTro'] != PHONG_DAO_TAO and ten not in CHO_PHEP_XEM_CHUNG:
        raise Forbidden()
    return jsonify(svc.danh_sach(get_db(), ten, request.args.get('q')))


@bp.post('/<ten>')
@role_required(PHONG_DAO_TAO)
def tao(user, ten):
    return jsonify(svc.tao(get_db(), ten, request.get_json(silent=True) or {})), 201


@bp.put('/<ten>/<int:ma>')
@role_required(PHONG_DAO_TAO)
def sua(user, ten, ma):
    return jsonify(svc.sua(get_db(), ten, ma, request.get_json(silent=True) or {}))


@bp.delete('/<ten>/<int:ma>')
@role_required(PHONG_DAO_TAO)
def xoa(user, ten, ma):
    svc.xoa(get_db(), ten, ma)
    return jsonify({'thongBao': 'Da xoa'})
