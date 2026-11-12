"""Nghiep vu thong bao thay doi lich hoc."""
from ..errors import AppError, NotFound
from . import thoi_khoa_bieu as tkb


def _buoi(db, ma):
    r = db.execute(tkb.SELECT + " WHERE t.maTKB=?", (ma,)).fetchone()
    if r is None:
        raise NotFound("Buoi hoc khong ton tai")
    return dict(r)


def _tao(db, loai, tieu_de, noi_dung, buoi):
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung,maTKB,maLop,maGiangVien)
                  VALUES (?,?,?,?,?,?)""",
               (loai, tieu_de, noi_dung, buoi.get("maTKB"),
                buoi.get("maLop"), buoi.get("maGiangVien")))


def danh_sach(db, user):
    sql = """SELECT n.maThongBao,n.loai,n.tieuDe,n.noiDung,n.ngayTao,
                    n.maTKB,n.maLop,n.maGiangVien,COALESCE(l.tenHienThi, l.tenLop) AS tenLop,g.hoTen AS tenGiangVien
             FROM ThongBao n
             LEFT JOIN Lop l ON l.maLop=n.maLop
             LEFT JOIN GiangVien g ON g.maGiangVien=n.maGiangVien"""
    args = []
    if user["vaiTro"] == "GIANG_VIEN":
        sql += " WHERE n.maGiangVien=? OR (n.maGiangVien IS NULL AND n.maLop IS NULL)"
        args.append(user.get("maGiangVien", -1))
    elif user["vaiTro"] == "SINH_VIEN":
        sql += " WHERE n.maLop=? OR (n.maGiangVien IS NULL AND n.maLop IS NULL)"
        args.append(user.get("maLop", -1))
    sql += " ORDER BY n.ngayTao DESC, n.maThongBao DESC"
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def nghi_hoc(db, ma_tkb, ly_do):
    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise AppError("Vui long nhap ly do nghi hoc")
    b = _buoi(db, ma_tkb)
    noi_dung = (f"Lop {b['tenLop']} nghi hoc mon {b['tenMonHoc']} ngay {b['ngayHoc']}, "
                f"tiet {b['tietBatDau']}-{b['tietKetThuc']}, phong {b['tenPhong']}. Ly do: {ly_do}.")
    _tao(db, "NGHI", f"Thong bao nghi hoc - {b['tenMonHoc']}", noi_dung, b)
    db.commit()
    return {"thongBao": "Da gui thong bao nghi hoc"}


def doi_phong(db, ma_tkb, ma_phong):
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
    _tao(db, "DOI_PHONG", f"Thong bao doi phong - {b['tenMonHoc']}", noi_dung, b)
    db.commit()
    return {"thongBao": "Da doi phong va gui thong bao"}


def day_bu(db, ma_tkb, data):
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
    _tao(db, "DAY_BU", f"Thong bao day bu - {b['tenMonHoc']}", noi_dung, new_b)
    db.commit()
    return {"thongBao": "Da tao lich day bu va gui thong bao", "buoiHoc": new_b}


def thong_bao_chung(db, tieu_de, noi_dung):
    tieu_de = (tieu_de or "").strip()
    noi_dung = (noi_dung or "").strip()
    if not tieu_de or not noi_dung:
        raise AppError("Vui long nhap day du tieu de va noi dung")
    db.execute("""INSERT INTO ThongBao(loai,tieuDe,noiDung)
                  VALUES ('CHUNG',?,?)""", (tieu_de, noi_dung))
    db.commit()
    return {"thongBao": "Da phat hanh thong bao chung"}
