from flask import Blueprint, jsonify, request
from ..auth import login_required, role_required
from ..config import PHONG_DAO_TAO
from ..db import get_db
from ..services import thong_bao as svc

bp = Blueprint("thong_bao", __name__, url_prefix="/api")


@bp.get("/thong-bao")
@login_required
def danh_sach(user):
    return jsonify(svc.danh_sach(get_db(), user))


@bp.post("/tkb/<int:ma>/nghi-hoc")
@role_required(PHONG_DAO_TAO)
def nghi_hoc(user, ma):
    d = request.get_json(silent=True) or {}
    return jsonify(svc.nghi_hoc(get_db(), ma, d.get("lyDo")))


@bp.post("/tkb/<int:ma>/doi-phong")
@role_required(PHONG_DAO_TAO)
def doi_phong(user, ma):
    d = request.get_json(silent=True) or {}
    return jsonify(svc.doi_phong(get_db(), ma, d.get("maPhong")))


@bp.post("/tkb/<int:ma>/day-bu")
@role_required(PHONG_DAO_TAO)
def day_bu(user, ma):
    return jsonify(svc.day_bu(get_db(), ma, request.get_json(silent=True) or {})), 201


@bp.post("/thong-bao/chung")
@role_required(PHONG_DAO_TAO)
def thong_bao_chung(user):
    d = request.get_json(silent=True) or {}
    return jsonify(svc.thong_bao_chung(get_db(), d.get("tieuDe"), d.get("noiDung")))
