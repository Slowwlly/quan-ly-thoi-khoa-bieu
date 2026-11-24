from flask import Blueprint, jsonify, request
from ..auth import login_required, role_required
from ..config import PHONG_DAO_TAO, GIANG_VIEN, SINH_VIEN
from ..db import get_db
from ..services import thong_bao as svc

bp = Blueprint("thong_bao", __name__, url_prefix="/api")


def _body():
    return request.get_json(silent=True) or {}


@bp.get("/thong-bao")
@login_required
def danh_sach(user):
    return jsonify(svc.danh_sach(get_db(), user, request.args.to_dict()))


@bp.get("/thong-bao/so-chua-doc")
@login_required
def so_chua_doc(user):
    return jsonify({"soChuaDoc": svc.so_chua_doc(get_db(), user)})


@bp.post("/thong-bao/da-doc-tat-ca")
@role_required(SINH_VIEN, GIANG_VIEN)
def da_doc_tat_ca(user):
    svc.danh_dau_tat_ca(get_db(), user)
    return jsonify({"thongBao": "Da danh dau tat ca la da doc", "soChuaDoc": 0})


@bp.get("/thong-bao/<int:ma>")
@login_required
def chi_tiet(user, ma):
    return jsonify(svc.chi_tiet(get_db(), user, ma))


@bp.post("/thong-bao/<int:ma>/da-doc")
@role_required(SINH_VIEN, GIANG_VIEN)
def da_doc(user, ma):
    svc.danh_dau_da_doc(get_db(), user, ma)
    return jsonify({"thongBao": "Da danh dau da doc", "soChuaDoc": svc.so_chua_doc(get_db(), user)})


@bp.post("/thong-bao")
@role_required(PHONG_DAO_TAO)
def tao(user):
    return jsonify(svc.tao(get_db(), user, _body())), 201


@bp.put("/thong-bao/<int:ma>")
@role_required(PHONG_DAO_TAO)
def sua(user, ma):
    return jsonify(svc.sua(get_db(), user, ma, _body()))


@bp.post("/thong-bao/<int:ma>/gui")
@role_required(PHONG_DAO_TAO)
def gui(user, ma):
    return jsonify(svc.gui_ban_nhap(get_db(), user, ma))


@bp.delete("/thong-bao/<int:ma>")
@role_required(PHONG_DAO_TAO)
def xoa(user, ma):
    svc.xoa(get_db(), ma)
    return jsonify({"thongBao": "Da xoa thong bao"})


@bp.post("/tkb/<int:ma>/nghi-hoc")
@role_required(PHONG_DAO_TAO)
def nghi_hoc(user, ma):
    return jsonify(svc.nghi_hoc(get_db(), ma, _body().get("lyDo"), user["maTaiKhoan"]))


@bp.post("/tkb/<int:ma>/doi-phong")
@role_required(PHONG_DAO_TAO)
def doi_phong(user, ma):
    return jsonify(svc.doi_phong(get_db(), ma, _body().get("maPhong"), user["maTaiKhoan"]))


@bp.post("/tkb/<int:ma>/day-bu")
@role_required(PHONG_DAO_TAO)
def day_bu(user, ma):
    return jsonify(svc.day_bu(get_db(), ma, _body(), user["maTaiKhoan"])), 201


@bp.post("/thong-bao/chung")
@role_required(PHONG_DAO_TAO)
def thong_bao_chung(user):
    d = _body()
    return jsonify(svc.thong_bao_chung(get_db(), d.get("tieuDe"), d.get("noiDung"), user["maTaiKhoan"]))


@bp.get("/giang-vien/thong-bao/lop-duoc-day")
@role_required(GIANG_VIEN)
def lop_duoc_day(user):
    return jsonify(svc.lop_duoc_giang_day(get_db(), user))


@bp.post("/giang-vien/thong-bao")
@role_required(GIANG_VIEN)
def gv_tao_thong_bao(user):
    return jsonify(svc.tao_cho_lop(get_db(), user, _body())), 201


@bp.put("/giang-vien/thong-bao/<int:ma>")
@role_required(GIANG_VIEN)
def gv_sua_thong_bao(user, ma):
    return jsonify(svc.sua_cua_giang_vien(get_db(), user, ma, _body()))


@bp.delete("/giang-vien/thong-bao/<int:ma>")
@role_required(GIANG_VIEN)
def gv_xoa_thong_bao(user, ma):
    svc.xoa_cua_giang_vien(get_db(), user, ma)
    return jsonify({"thongBao": "Da xoa thong bao"})
