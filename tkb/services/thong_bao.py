"""Nghiep vu thong bao thay doi lich hoc."""
from ..config import LOAI_THONG_BAO, DOI_TUONG_NHAP
from ..errors import AppError, Forbidden, NotFound
from . import thoi_khoa_bieu as tkb


def _buoi(db, ma):
    r = db.execute(tkb.SELECT + " WHERE t.maTKB=?", (ma,)).fetchone()
    if r is None:
        raise NotFound("Buoi hoc khong ton tai")
    return dict(r)


def _tao(db, loai, tieu_de, noi_dung, buoi, ma_nguoi_gui=None):
    """Thong bao tu dong cho lop + giang vien cua buoi hoc (nghi, day bu, doi phong)."""
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,maTKB,doiTuong,maLop,maGiangVien,maNguoiGui,
                                       trangThai,thoiGianGui)
                  VALUES (?,?,?,?,'LOP_VA_GV',?,?,?,'DA_GUI',datetime('now','localtime'))""",
               (loai, tieu_de, noi_dung, buoi.get("maTKB"), buoi.get("maLop"), buoi.get("maGiangVien"),
                ma_nguoi_gui))


NHAN_DOI_TUONG = {'TAT_CA': 'Tất cả sinh viên và giảng viên', 'TAT_CA_SV': 'Tất cả sinh viên',
                  'TAT_CA_GV': 'Tất cả giảng viên'}

SELECT = """SELECT n.maThongBao,n.loai,n.tieuDe,n.noiDung,n.doiTuong,n.trangThai,n.ngayTao,n.thoiGianGui,
       n.ngayCapNhat,n.maTKB,n.maLop,n.maGiangVien,n.maNguoiGui,
       COALESCE(NULLIF(l.tenHienThi,''), l.tenLop) AS tenLop, g.hoTen AS tenGiangVien,
       CASE WHEN a.hoTen IS NOT NULL AND a.hoTen<>'' THEN 'Phòng Đào tạo – ' || a.hoTen ELSE 'Phòng Đào tạo' END AS nguoiGui,
       EXISTS(SELECT 1 FROM ThongBaoDaDoc d WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk) AS daDoc
       FROM ThongBao n
       LEFT JOIN Lop l ON l.maLop=n.maLop
       LEFT JOIN GiangVien g ON g.maGiangVien=n.maGiangVien
       LEFT JOIN TaiKhoan a ON a.maTaiKhoan=n.maNguoiGui"""


def _pham_vi(user, args):
    """Dieu kien SQL gioi han thong bao theo vai tro (kiem tra o backend)."""
    if user["vaiTro"] == "PHONG_DAO_TAO":
        return "1=1"
    if user["vaiTro"] == "GIANG_VIEN":
        args["gv"] = user.get("maGiangVien", -1)
        return ("n.trangThai='DA_GUI' AND (n.doiTuong IN ('TAT_CA','TAT_CA_GV') OR "
                "(n.doiTuong IN ('GIANG_VIEN','LOP_VA_GV') AND n.maGiangVien=:gv))")
    args["lop"] = user.get("maLop", -1)
    return ("n.trangThai='DA_GUI' AND (n.doiTuong IN ('TAT_CA','TAT_CA_SV') OR "
            "(n.doiTuong IN ('LOP','LOP_VA_GV') AND n.maLop=:lop))")


def _hoan_thien(r, user):
    r = dict(r)
    r["daDoc"] = bool(r["daDoc"])
    r["tenLoai"] = LOAI_THONG_BAO.get(r["loai"], r["loai"])
    dt = r["doiTuong"]
    if dt in NHAN_DOI_TUONG:
        r["tenDoiTuong"] = NHAN_DOI_TUONG[dt]
    elif dt == "LOP":
        r["tenDoiTuong"] = f"Lớp {r['tenLop']}"
    elif dt == "GIANG_VIEN":
        r["tenDoiTuong"] = f"Giảng viên {r['tenGiangVien']}"
    else:
        r["tenDoiTuong"] = f"Lớp {r['tenLop']} và giảng viên {r['tenGiangVien']}"
    if user["vaiTro"] != "PHONG_DAO_TAO":
        for k in ("maNguoiGui",):
            r.pop(k, None)
    return r


def danh_sach(db, user, p=None):
    p = p or {}
    args = {"tk": user["maTaiKhoan"]}
    where = [_pham_vi(user, args)]
    if p.get("loai"):
        if p["loai"] not in LOAI_THONG_BAO:
            raise AppError("Loai thong bao khong hop le")
        where.append("n.loai=:loai"); args["loai"] = p["loai"]
    if p.get("chuaDoc") in ("1", "true", 1, True):
        where.append("NOT EXISTS(SELECT 1 FROM ThongBaoDaDoc d WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk)")
    if p.get("trangThai") in ("NHAP", "DA_GUI") and user["vaiTro"] == "PHONG_DAO_TAO":
        where.append("n.trangThai=:tt"); args["tt"] = p["trangThai"]
    q = (p.get("q") or "").strip()
    if q:
        where.append("(n.tieuDe LIKE :q OR n.noiDung LIKE :q)"); args["q"] = f"%{q}%"
    sql = SELECT + " WHERE " + " AND ".join(where) + \
        " ORDER BY COALESCE(n.thoiGianGui, n.ngayTao) DESC, n.maThongBao DESC"
    return [_hoan_thien(r, user) for r in db.execute(sql, args).fetchall()]


def chi_tiet(db, user, ma):
    args = {"tk": user["maTaiKhoan"], "ma": ma}
    r = db.execute(SELECT + " WHERE n.maThongBao=:ma", args).fetchone()
    if r is None:
        raise NotFound("Thong bao khong ton tai hoac da bi xoa")
    args2 = {"tk": user["maTaiKhoan"], "ma": ma}
    ok = db.execute(SELECT + " WHERE n.maThongBao=:ma AND " + _pham_vi(user, args2), args2).fetchone()
    if ok is None:
        raise Forbidden("Ban khong co quyen xem thong bao nay")
    return _hoan_thien(ok, user)


def so_chua_doc(db, user):
    if user["vaiTro"] == "PHONG_DAO_TAO":
        return 0
    args = {"tk": user["maTaiKhoan"]}
    w = _pham_vi(user, args)
    return db.execute("SELECT COUNT(*) FROM ThongBao n WHERE " + w + " AND NOT EXISTS(SELECT 1 FROM ThongBaoDaDoc d "
                      "WHERE d.maThongBao=n.maThongBao AND d.maTaiKhoan=:tk)", args).fetchone()[0]


def danh_dau_da_doc(db, user, ma):
    chi_tiet(db, user, ma)   # kiem tra quyen truoc
    db.execute("INSERT OR IGNORE INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) VALUES (?,?)", (ma, user["maTaiKhoan"]))
    db.commit()


def danh_dau_tat_ca(db, user):
    args = {"tk": user["maTaiKhoan"]}
    w = _pham_vi(user, args)
    db.execute("INSERT OR IGNORE INTO ThongBaoDaDoc(maThongBao,maTaiKhoan) "
               "SELECT n.maThongBao, :tk FROM ThongBao n WHERE " + w, args)
    db.commit()


def _chuan_hoa(db, d):
    tieu_de = (d.get("tieuDe") or "").strip()
    noi_dung = (d.get("noiDung") or "").strip()
    if not tieu_de or not noi_dung:
        raise AppError("Vui long nhap day du tieu de va noi dung")
    if len(tieu_de) > 200 or len(noi_dung) > 5000:
        raise AppError("Tieu de toi da 200 ky tu, noi dung toi da 5000 ky tu")
    loai = d.get("loai") or "CHUNG"
    if loai not in LOAI_THONG_BAO:
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
    gui = d.get("guiNgay", True)
    gui = gui not in (False, "false", "0", 0, "NHAP")
    return dict(tieuDe=tieu_de, noiDung=noi_dung, loai=loai, doiTuong=dt, maLop=ma_lop, maGiangVien=ma_gv, gui=gui)


def tao(db, user, d):
    v = _chuan_hoa(db, d)
    cur = db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,doiTuong,maLop,maGiangVien,maNguoiGui,trangThai,thoiGianGui)
        VALUES (:loai,:tieuDe,:noiDung,:doiTuong,:maLop,:maGiangVien,:ng,:tt,
                CASE WHEN :tt='DA_GUI' THEN datetime('now','localtime') END)""",
                     {**v, "ng": user["maTaiKhoan"], "tt": "DA_GUI" if v["gui"] else "NHAP"})
    db.commit()
    return chi_tiet(db, user, cur.lastrowid)


def sua(db, user, ma, d):
    cu = chi_tiet(db, user, ma)
    v = _chuan_hoa(db, d)
    # Thong bao da gui van sua duoc (ghi nhan thoi gian cap nhat); khong chuyen nguoc ve nhap.
    gui = v["gui"] or cu["trangThai"] == "DA_GUI"
    db.execute("""UPDATE ThongBao SET loai=:loai,tieuDe=:tieuDe,noiDung=:noiDung,doiTuong=:doiTuong,maLop=:maLop,
                  maGiangVien=:maGiangVien,trangThai=:tt,ngayCapNhat=datetime('now','localtime'),
                  thoiGianGui=CASE WHEN :tt='DA_GUI' AND thoiGianGui IS NULL THEN datetime('now','localtime') ELSE thoiGianGui END
                  WHERE maThongBao=:ma""", {**v, "tt": "DA_GUI" if gui else "NHAP", "ma": ma})
    db.commit()
    return chi_tiet(db, user, ma)


def gui_ban_nhap(db, user, ma):
    cu = chi_tiet(db, user, ma)
    if cu["trangThai"] == "DA_GUI":
        raise AppError("Thong bao nay da duoc gui")
    db.execute("UPDATE ThongBao SET trangThai='DA_GUI', thoiGianGui=datetime('now','localtime') WHERE maThongBao=?", (ma,))
    db.commit()
    return chi_tiet(db, user, ma)


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
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,doiTuong,maNguoiGui,trangThai,thoiGianGui)
                  VALUES ('CHUNG',?,?,'TAT_CA',?,'DA_GUI',datetime('now','localtime'))""", (tieu_de, noi_dung, ma_nguoi_gui))
    db.commit()
    return {"thongBao": "Da phat hanh thong bao chung"}


def xoa(db, ma_thong_bao):
    cur = db.execute("DELETE FROM ThongBao WHERE maThongBao=?", (ma_thong_bao,))
    if cur.rowcount == 0:
        raise NotFound("Thong bao khong ton tai hoac da bi xoa")
    db.commit()
