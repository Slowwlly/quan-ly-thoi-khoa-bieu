from flask import Blueprint, jsonify, request, send_file
from ..auth import role_required
from ..config import PHONG_DAO_TAO
from ..db import get_db
from ..errors import AppError
from ..services import nhap_excel as svc

bp = Blueprint('nhap_excel', __name__, url_prefix='/api/nhap-excel')


@bp.get('/<loai>/mau')
@role_required(PHONG_DAO_TAO)
def file_mau(user, loai):
    buf, ten = svc.tao_file_mau(get_db(), loai)
    return send_file(buf, as_attachment=True, download_name=ten,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.post('/<loai>')
@role_required(PHONG_DAO_TAO)
def nhap(user, loai):
    f = request.files.get('file')
    if f is None or not f.filename:
        raise AppError('Vui long chon file Excel (.xlsx) hoac CSV')
    data = f.read(svc.TOI_DA_BYTE + 1)
    return jsonify(svc.nhap(get_db(), loai, f.filename, data))
