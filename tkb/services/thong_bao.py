"""Nghiep vu thong bao thay doi lich hoc."""
from datetime import date, datetime, timedelta

from flask import current_app

from ..config import (DOI_TUONG_NHAP, GV_LOP_NGAY_TRUOC, GV_SUA_TOI_DA_GIO, LOAI_GV, LOAI_PDT, LOAI_THONG_BAO,
                      NHAN_NGUON_GUI, SENDER_GV, SENDER_PDT)
from ..errors import AppError, Conflict, Forbidden, NotFound
from . import thoi_khoa_bieu as tkb


def _buoi(db, ma):
    r = db.execute(tkb.SELECT + " WHERE t.maTKB=?", (ma,)).fetchone()
    if r is None:
        raise NotFound("Buoi hoc khong ton tai")
    return dict(r)


def _tao(db, loai, tieu_de, noi_dung, buoi, ma_nguoi_gui=None):
    """Thong bao tu dong cho lop + giang vien cua buoi hoc (nghi, day bu, doi phong)."""
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,maTKB,doiTuong,maLop,maGiangVien,maNguoiGui,
                                       sender_type,tenNguoiGui,maMonHoc,tenMonHoc,trangThai,thoiGianGui)
                  VALUES (?,?,?,?,'LOP_VA_GV',?,?,?,'PHONG_DAO_TAO','Phòng Đào tạo',?,?,'DA_GUI',
                          datetime('now','localtime'))""",
               (loai, tieu_de, noi_dung, buoi.get("maTKB"), buoi.get("maLop"), buoi.get("maGiangVien"),
                ma_nguoi_gui, buoi.get("maMonHoc"), buoi.get("tenMonHoc")))


NHAN_DOI_TUONG = {'TAT_CA': 'Tất cả sinh viên và giảng viên', 'TAT_CA_SV': 'Tất cả sinh viên',
                  'TAT_CA_GV': 'Tất cả giảng viên'}

def _hom_nay():
    try:
        return current_app.config.get('HOM_NAY') or date.today()
    except RuntimeError:
        return date.today()


SELECT = """SELECT n.maThongBao,n.loai,n.tieuDe,n.noiDung,n.doiTuong,n.trangThai,n.ngayTao,n.thoiGianGui,
       n.ngayCapNhat,n.maTKB,n.maLop,n.maGiangVien,n.maNguoiGui,n.sender_type,n.maGiangVienGui,n.maMonHoc,
       COALESCE(NULLIF(l.tenHienThi,''), l.tenLop) AS tenLop, g.hoTen AS tenGiangVien,
       CASE WHEN n.sender_type='GIANG_VIEN' THEN COALESCE(NULLIF(n.tenNguoiGui,''), gs.hoTen, 'Giảng viên')
            ELSE 'Phòng Đào tạo' END AS nguoiGui,
       COALESCE(NULLIF(n.tenMonHoc,''), mh.tenMonHoc, mt.tenMonHoc) AS tenMonHoc,
       EXISTS(SELECT 1 FROM ThongBaoDaDoc d WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk) AS daDoc
       FROM ThongBao n
       LEFT JOIN Lop l ON l.maLop=n.maLop
       LEFT JOIN GiangVien g ON g.maGiangVien=n.maGiangVien
       LEFT JOIN GiangVien gs ON gs.maGiangVien=n.maGiangVienGui
       LEFT JOIN MonHoc mh ON mh.maMonHoc=n.maMonHoc
       LEFT JOIN ThoiKhoaBieu tk ON tk.maTKB=n.maTKB
       LEFT JOIN MonHoc mt ON mt.maMonHoc=tk.maMonHoc"""


def _pham_vi(user, args):
    """Thong bao NGUOI DUNG DUOC NHAN (kiem tra o backend). Phong Dao tao thay tat ca, tru ban nhap cua giang vien."""
    if user["vaiTro"] == "PHONG_DAO_TAO":
        return "(n.sender_type='PHONG_DAO_TAO' OR n.trangThai='DA_GUI')"
    if user["vaiTro"] == "GIANG_VIEN":
        args["gv"] = user.get("maGiangVien", -1)
        return ("n.trangThai='DA_GUI' AND (n.doiTuong IN ('TAT_CA','TAT_CA_GV') OR "
                "(n.doiTuong IN ('GIANG_VIEN','LOP_VA_GV') AND n.maGiangVien=:gv))")
    args["lop"] = user.get("maLop", -1)
    return ("n.trangThai='DA_GUI' AND (n.doiTuong IN ('TAT_CA','TAT_CA_SV') OR "
            "(n.doiTuong IN ('LOP','LOP_VA_GV') AND n.maLop=:lop))")


def _pham_vi_da_gui(user, args):
    """Thong bao giang vien da tao (ke ca ban nhap)."""
    args["gv"] = user.get("maGiangVien", -1)
    return "(n.sender_type='GIANG_VIEN' AND n.maGiangVienGui=:gv)"


def _pham_vi_xem(user, args):
    """Duoc xem chi tiet: thong bao gui den minh, hoac (giang vien) thong bao do chinh minh tao."""
    nhan = _pham_vi(user, args)
    if user["vaiTro"] == "GIANG_VIEN":
        return f"(({nhan}) OR {_pham_vi_da_gui(user, args)})"
    return nhan


# ---------- lop giang vien duoc phep gui ----------
def lop_giang_day(db, user):
    """Lop + mon giang vien DANG co lich day, lay tu thoi khoa bieu (khong tin du lieu tu frontend)."""
    if user["vaiTro"] != "GIANG_VIEN":
        raise Forbidden("Chi giang vien moi co danh sach lop giang day")
    tu = (_hom_nay() - timedelta(days=GV_LOP_NGAY_TRUOC)).isoformat()
    rows = db.execute("""SELECT t.maLop, COALESCE(NULLIF(l.tenHienThi,''), l.tenLop) AS tenLop, l.namTuyenSinh,
                                t.maMonHoc, m.tenMonHoc
                         FROM ThoiKhoaBieu t JOIN Lop l ON l.maLop=t.maLop JOIN MonHoc m ON m.maMonHoc=t.maMonHoc
                         WHERE t.maGiangVien=? AND t.ngayHoc>=?
                         GROUP BY t.maLop, t.maMonHoc ORDER BY tenLop, m.tenMonHoc""",
                      (user.get("maGiangVien", -1), tu)).fetchall()
    ds = {}
    for r in rows:
        lop = ds.setdefault(r["maLop"], {"maLop": r["maLop"], "tenLop": r["tenLop"],
                                         "namTuyenSinh": r["namTuyenSinh"], "monHoc": []})
        lop["monHoc"].append({"maMonHoc": r["maMonHoc"], "tenMonHoc": r["tenMonHoc"]})
    return list(ds.values())


def _ngu_canh(db, user):
    if user["vaiTro"] == "GIANG_VIEN":
        return {"lop": {x["maLop"]: x for x in lop_giang_day(db, user)}}
    return {"lop": {}}


def _da_khoa(r):
    """Thong bao giang vien da gui qua GV_SUA_TOI_DA_GIO gio thi bi khoa."""
    if r["sender_type"] != SENDER_GV or r["trangThai"] != "DA_GUI" or not r["thoiGianGui"]:
        return False
    try:
        gui = datetime.strptime(r["thoiGianGui"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    return datetime.now() - gui > timedelta(hours=GV_SUA_TOI_DA_GIO)


def _quyen(r, user, ctx):
    q = {"sua": False, "xoa": False, "gui": False, "daKhoa": _da_khoa(r)}
    if user["vaiTro"] == "PHONG_DAO_TAO":
        pdt = r["sender_type"] == SENDER_PDT
        q.update(sua=pdt, xoa=True, gui=pdt and r["trangThai"] == "NHAP")   # thong bao GV: PDT chi duoc xoa
    elif user["vaiTro"] == "GIANG_VIEN" and r["sender_type"] == SENDER_GV \
            and r["maGiangVienGui"] == user.get("maGiangVien"):
        con_day = r["maLop"] in ctx["lop"]
        q.update(sua=not q["daKhoa"] and con_day, xoa=not q["daKhoa"],
                 gui=r["trangThai"] == "NHAP" and con_day)
    return q


def _hoan_thien(r, user, ctx=None):
    r = dict(r)
    ctx = ctx or {"lop": {}}
    r["daDoc"] = bool(r["daDoc"])
    r["tenLoai"] = LOAI_THONG_BAO.get(r["loai"], r["loai"])
    r["nguonGui"] = NHAN_NGUON_GUI.get(r["sender_type"], r["sender_type"])
    dt = r["doiTuong"]
    if dt in NHAN_DOI_TUONG:
        r["tenDoiTuong"] = NHAN_DOI_TUONG[dt]
    elif dt == "LOP":
        r["tenDoiTuong"] = f"Lớp {r['tenLop']}"
    elif dt == "GIANG_VIEN":
        r["tenDoiTuong"] = f"Giảng viên {r['tenGiangVien']}"
    else:
        r["tenDoiTuong"] = f"Lớp {r['tenLop']} và giảng viên {r['tenGiangVien']}"
    r["quyen"] = _quyen(r, user, ctx)
    r["daKhoa"] = r["quyen"]["daKhoa"]
    if user["vaiTro"] != "PHONG_DAO_TAO":
        r.pop("maNguoiGui", None)
        if user["vaiTro"] == "SINH_VIEN":
            r.pop("maGiangVienGui", None)
    return r


def danh_sach(db, user, p=None):
    p = p or {}
    args = {"tk": user["maTaiKhoan"]}
    if p.get("daGui") in ("1", "true", 1, True):
        if user["vaiTro"] != "GIANG_VIEN":
            raise Forbidden("Chi giang vien co danh sach thong bao da gui")
        where = [_pham_vi_da_gui(user, args)]
    else:
        where = [_pham_vi(user, args)]
    if p.get("loai"):
        if p["loai"] not in LOAI_THONG_BAO:
            raise AppError("Loai thong bao khong hop le")
        where.append("n.loai=:loai"); args["loai"] = p["loai"]
    if p.get("nguon"):
        if p["nguon"] not in NHAN_NGUON_GUI:
            raise AppError("Nguon gui khong hop le")
        where.append("n.sender_type=:nguon"); args["nguon"] = p["nguon"]
    doc = "EXISTS(SELECT 1 FROM ThongBaoDaDoc d WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk)"
    if p.get("chuaDoc") in ("1", "true", 1, True):
        where.append("NOT " + doc)
    if p.get("daDoc") in ("1", "true", 1, True):
        where.append(doc)
    if p.get("trangThai") in ("NHAP", "DA_GUI") and user["vaiTro"] != "SINH_VIEN":
        where.append("n.trangThai=:tt"); args["tt"] = p["trangThai"]
    q = (p.get("q") or "").strip()
    if q:
        where.append("(n.tieuDe LIKE :q OR n.noiDung LIKE :q)"); args["q"] = f"%{q}%"
    sql = SELECT + " WHERE " + " AND ".join(where) + \
        " ORDER BY COALESCE(n.thoiGianGui, n.ngayTao) DESC, n.maThongBao DESC"
    ctx = _ngu_canh(db, user)
    return [_hoan_thien(r, user, ctx) for r in db.execute(sql, args).fetchall()]


def _lay(db, user, ma, xem=True):
    """Lay thong bao neu nguoi dung duoc phep xem; 404 neu khong co, 403 neu ngoai pham vi."""
    args = {"tk": user["maTaiKhoan"], "ma": ma}
    if db.execute("SELECT 1 FROM ThongBao WHERE maThongBao=?", (ma,)).fetchone() is None:
        raise NotFound("Thong bao khong ton tai hoac da bi xoa")
    w = (_pham_vi_xem if xem else _pham_vi)(user, args)
    r = db.execute(SELECT + " WHERE n.maThongBao=:ma AND " + w, args).fetchone()
    if r is None:
        raise Forbidden("Ban khong co quyen xem thong bao nay")
    return r


def chi_tiet(db, user, ma):
    return _hoan_thien(_lay(db, user, ma), user, _ngu_canh(db, user))


def so_chua_doc(db, user):
    if user["vaiTro"] == "PHONG_DAO_TAO":
        return 0
    args = {"tk": user["maTaiKhoan"]}
    w = _pham_vi(user, args)
    return db.execute("SELECT COUNT(*) FROM ThongBao n WHERE " + w + " AND NOT EXISTS(SELECT 1 FROM ThongBaoDaDoc d "
                      "WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk)", args).fetchone()[0]


def danh_dau_da_doc(db, user, ma):
    _lay(db, user, ma, xem=False)   # chi thong bao gui DEN minh moi co trang thai doc
    db.execute("INSERT OR IGNORE INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) VALUES (?,?)", (ma, user["maTaiKhoan"]))
    db.commit()


def danh_dau_tat_ca(db, user):
    args = {"tk": user["maTaiKhoan"]}
    w = _pham_vi(user, args)
    db.execute("INSERT OR IGNORE INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) "
               "SELECT n.maThongBao, :tk FROM ThongBao n WHERE " + w, args)
    db.commit()


def _tieu_noi_dung(d):
    tieu_de = (d.get("tieuDe") or "").strip()
    noi_dung = (d.get("noiDung") or "").strip()
    if not tieu_de or not noi_dung:
        raise AppError("Vui long nhap day du tieu de va noi dung")
    if len(tieu_de) > 200 or len(noi_dung) > 5000:
        raise AppError("Tieu de toi da 200 ky tu, noi dung toi da 5000 ky tu")
    gui = d.get("guiNgay", True)
    return tieu_de, noi_dung, gui not in (False, "false", "0", 0, "NHAP")


def _chuan_hoa(db, d):
    """Phong Dao tao: chon loai + doi tuong nhan."""
    tieu_de, noi_dung, gui = _tieu_noi_dung(d)
    loai = d.get("loai") or "CHUNG"
    if loai not in LOAI_PDT:
        raise AppError("Loai thong bao khong hop le")
    dt = d.get("doiTuong") or "TAT_CA_SV"
    if dt not in DOI_TUONG_NHAP:
        raise AppError("Doi tuong nhan khong hop le")
    ma_lop = ma_gv = None
    if dt == "LOP":
        try:
            ma_lop = int(d.get("maLop"))
        except (TypeError, ValueError):
            raise AppError("Vui long chon lop nhan thong bao")
        if db.execute("SELECT 1 FROM Lop WHERE maLop=?", (ma_lop,)).fetchone() is None:
            raise AppError("Lop khong ton tai")
    if dt == "GIANG_VIEN":
        try:
            ma_gv = int(d.get("maGiangVien"))
        except (TypeError, ValueError):
            raise AppError("Vui long chon giang vien nhan thong bao")
        if db.execute("SELECT 1 FROM GiangVien WHERE maGiangVien=?", (ma_gv,)).fetchone() is None:
            raise AppError("Giang vien khong ton tai")
    return dict(tieuDe=tieu_de, noiDung=noi_dung, loai=loai, doiTuong=dt, maLop=ma_lop, maGiangVien=ma_gv,
                maMonHoc=None, tenMonHoc=None, gui=gui)


def _chuan_hoa_gv(db, user, d):
    """Giang vien: chi gui cho LOP minh dang day (xac minh bang thoi khoa bieu o backend)."""
    tieu_de, noi_dung, gui = _tieu_noi_dung(d)
    loai = d.get("loai") or "GV_CHUNG"
    if loai not in LOAI_GV:
        raise AppError("Loai thong bao khong hop le")
    if (d.get("doiTuong") or "LOP") != "LOP" or d.get("maGiangVien") not in (None, ""):
        raise Forbidden("Giang vien chi duoc gui thong bao den lop minh giang day")
    try:
        ma_lop = int(d.get("maLop"))
    except (TypeError, ValueError):
        raise AppError("Vui long chon lop nhan thong bao")
    lop = _ngu_canh(db, user)["lop"].get(ma_lop)
    if lop is None:
        raise Forbidden("Ban khong co lich giang day lop nay nen khong the gui thong bao")
    ma_mon = ten_mon = None
    if d.get("maMonHoc") not in (None, ""):
        try:
            ma_mon = int(d.get("maMonHoc"))
        except (TypeError, ValueError):
            raise AppError("Mon hoc khong hop le")
        mon = next((m for m in lop["monHoc"] if m["maMonHoc"] == ma_mon), None)
        if mon is None:
            raise AppError("Ban khong day mon nay o lop da chon")
        ten_mon = mon["tenMonHoc"]
    return dict(tieuDe=tieu_de, noiDung=noi_dung, loai=loai, doiTuong="LOP", maLop=ma_lop, maGiangVien=None,
                maMonHoc=ma_mon, tenMonHoc=ten_mon, gui=gui)


def tao(db, user, d):
    gv = user["vaiTro"] == "GIANG_VIEN"
    v = _chuan_hoa_gv(db, user, d) if gv else _chuan_hoa(db, d)
    # Nguon gui lay tu phien dang nhap, KHONG nhan tu client.
    nguoi = {"st": SENDER_GV if gv else SENDER_PDT, "gvg": user.get("maGiangVien") if gv else None,
             "ten": user["hoTen"] if gv else "Phòng Đào tạo"}
    cur = db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,doiTuong,maLop,maGiangVien,maNguoiGui,sender_type,
                             maGiangVienGui,tenNguoiGui,maMonHoc,tenMonHoc,trangThai,thoiGianGui)
        VALUES (:loai,:tieuDe,:noiDung,:doiTuong,:maLop,:maGiangVien,:ng,:st,:gvg,:ten,:maMonHoc,:tenMonHoc,:tt,
                CASE WHEN :tt='DA_GUI' THEN datetime('now','localtime') END)""",
                     {**v, **nguoi, "ng": user["maTaiKhoan"], "tt": "DA_GUI" if v["gui"] else "NHAP"})
    db.commit()
    return chi_tiet(db, user, cur.lastrowid)


def _chu_so_huu(db, user, ma):
    """Tra ve thong bao neu nguoi dung duoc phep QUAN LY; 403 neu khong phai chu so huu."""
    r = _hoan_thien(_lay(db, user, ma), user, _ngu_canh(db, user))
    return r


def sua(db, user, ma, d):
    cu = _chu_so_huu(db, user, ma)
    if user["vaiTro"] == "GIANG_VIEN":
        if cu["sender_type"] != SENDER_GV or cu["maGiangVienGui"] != user.get("maGiangVien"):
            raise Forbidden("Ban chi duoc sua thong bao do chinh minh tao")
        if cu["daKhoa"]:
            raise Conflict(f"Thong bao da gui qua {GV_SUA_TOI_DA_GIO} gio nen da bi khoa, khong the sua")
        v = _chuan_hoa_gv(db, user, d)   # xac minh lai lich day (lop moi hoac lop cu)
    else:
        if cu["sender_type"] != SENDER_PDT:
            raise Forbidden("Phong Dao tao khong chinh sua noi dung thong bao cua giang vien (chi duoc xoa)")
        v = _chuan_hoa(db, d)
    # Thong bao da gui van sua duoc (ghi nhan thoi gian cap nhat); khong chuyen nguoc ve nhap.
    gui = v["gui"] or cu["trangThai"] == "DA_GUI"
    db.execute("""UPDATE ThongBao SET loai=:loai,tieuDe=:tieuDe,noiDung=:noiDung,doiTuong=:doiTuong,maLop=:maLop,
                  maGiangVien=:maGiangVien,maMonHoc=:maMonHoc,tenMonHoc=:tenMonHoc,trangThai=:tt,
                  ngayCapNhat=datetime('now','localtime'),
                  thoiGianGui=CASE WHEN :tt='DA_GUI' AND thoiGianGui IS NULL THEN datetime('now','localtime') ELSE thoiGianGui END
                  WHERE maThongBao=:ma""", {**v, "tt": "DA_GUI" if gui else "NHAP", "ma": ma})
    db.commit()
    return chi_tiet(db, user, ma)


def gui_ban_nhap(db, user, ma):
    cu = _chu_so_huu(db, user, ma)
    if cu["trangThai"] == "DA_GUI":
        raise AppError("Thong bao nay da duoc gui")
    if not cu["quyen"]["gui"]:
        raise Forbidden("Ban khong co quyen gui thong bao nay (chi gui duoc cho lop minh dang giang day)")
    db.execute("UPDATE ThongBao SET trangThai='DA_GUI', thoiGianGui=datetime('now','localtime') WHERE maThongBao=?", (ma,))
    db.commit()
    return chi_tiet(db, user, ma)


def xoa(db, user, ma_thong_bao):
    cu = _chu_so_huu(db, user, ma_thong_bao)
    if user["vaiTro"] == "GIANG_VIEN":
        if cu["sender_type"] != SENDER_GV or cu["maGiangVienGui"] != user.get("maGiangVien"):
            raise Forbidden("Ban chi duoc xoa thong bao do chinh minh tao")
        if cu["daKhoa"]:
            raise Conflict(f"Thong bao da gui qua {GV_SUA_TOI_DA_GIO} gio nen da bi khoa, khong the xoa")
    db.execute("DELETE FROM ThongBao WHERE maThongBao=?", (ma_thong_bao,))
    db.commit()


def nghi_hoc(db, ma_tkb, ly_do, ma_nguoi_gui=None):
    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise AppError("Vui long nhap ly do nghi hoc")
    b = _buoi(db, ma_tkb)
    noi_dung = (f"Lop {b['tenLop']} nghi hoc mon {b['tenMonHoc']} ngay {b['ngayHoc']}, "
                f"tiet {b['tietBatDau']}-{b['tietKetThuc']}, phong {b['tenPhong']}. Ly do: {ly_do}.")
    _tao(db, "NGHI", f"Thong bao nghi hoc - {b['tenMonHoc']}", noi_dung, b, ma_nguoi_gui)
    db.commit()
    return {"thongBao": "Da gui thong bao nghi hoc"}


def doi_phong(db, ma_tkb, ma_phong, ma_nguoi_gui=None):
    b = _buoi(db, ma_tkb)
    try:
        ma_phong = int(ma_phong)
    except (TypeError, ValueError):
        raise AppError("Phong hoc khong hop le")
    room = db.execute("SELECT maPhong,tenPhong FROM PhongHoc WHERE maPhong=?", (ma_phong,)).fetchone()
    if room is None:
        raise AppError("Phong hoc khong ton tai")
    v = {"ngayHoc": b["ngayHoc"], "tietBatDau": b["tietBatDau"], "tietKetThuc": b["tietKetThuc"],
         "hocKy": b["hocKy"], "namHoc": b["namHoc"], "maGiangVien": b["maGiangVien"],
         "maMonHoc": b["maMonHoc"], "maLop": b["maLop"], "maPhong": ma_phong}
    tkb.kiem_tra_trung_lich(db, v, bo_qua=ma_tkb)
    db.execute("UPDATE ThoiKhoaBieu SET maPhong=? WHERE maTKB=?", (ma_phong, ma_tkb))
    noi_dung = (f"Lop {b['tenLop']}, mon {b['tenMonHoc']} ngay {b['ngayHoc']} "
                f"(tiet {b['tietBatDau']}-{b['tietKetThuc']}) duoc chuyen tu phong "
                f"{b['tenPhong']} sang phong {room['tenPhong']}.")
    _tao(db, "DOI_PHONG", f"Thong bao doi phong - {b['tenMonHoc']}", noi_dung, b, ma_nguoi_gui)
    db.commit()
    return {"thongBao": "Da doi phong va gui thong bao"}


def day_bu(db, ma_tkb, data, ma_nguoi_gui=None):
    b = _buoi(db, ma_tkb)
    v = {"ngayHoc": data.get("ngayHoc"), "tietBatDau": data.get("tietBatDau"),
         "tietKetThuc": data.get("tietKetThuc"), "hocKy": b["hocKy"], "namHoc": b["namHoc"],
         "maGiangVien": b["maGiangVien"], "maMonHoc": b["maMonHoc"], "maLop": b["maLop"],
         "maPhong": data.get("maPhong") or b["maPhong"]}
    v = tkb._chuan_hoa(db, v)
    tkb.kiem_tra_trung_lich(db, v)
    cur = db.execute("""INSERT INTO ThoiKhoaBieu(ngayHoc,tietBatDau,tietKetThuc,hocKy,namHoc,
                         maGiangVien,maMonHoc,maLop,maPhong)
                         VALUES (:ngayHoc,:tietBatDau,:tietKetThuc,:hocKy,:namHoc,
                         :maGiangVien,:maMonHoc,:maLop,:maPhong)""", v)
    new_b = _buoi(db, cur.lastrowid)
    noi_dung = (f"Lop {b['tenLop']} hoc bu mon {b['tenMonHoc']} vao ngay {new_b['ngayHoc']}, "
                f"tiet {new_b['tietBatDau']}-{new_b['tietKetThuc']}, phong {new_b['tenPhong']}.")
    _tao(db, "DAY_BU", f"Thong bao day bu - {b['tenMonHoc']}", noi_dung, new_b, ma_nguoi_gui)
    db.commit()
    return {"thongBao": "Da tao lich day bu va gui thong bao", "buoiHoc": new_b}


def thong_bao_chung(db, tieu_de, noi_dung, ma_nguoi_gui=None):
    tieu_de = (tieu_de or "").strip()
    noi_dung = (noi_dung or "").strip()
    if not tieu_de or not noi_dung:
        raise AppError("Vui long nhap day du tieu de va noi dung")
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,doiTuong,maNguoiGui,sender_type,tenNguoiGui,trangThai,thoiGianGui)
                  VALUES ('CHUNG',?,?,'TAT_CA',?,'PHONG_DAO_TAO','Phòng Đào tạo','DA_GUI',datetime('now','localtime'))""", (tieu_de, noi_dung, ma_nguoi_gui))
    db.commit()
    return {"thongBao": "Da phat hanh thong bao chung"}
