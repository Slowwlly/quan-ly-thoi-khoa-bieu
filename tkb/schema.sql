-- Luoc do quan he theo muc 3.4.6 cua bao cao (suy ra tu bieu do lop).
CREATE TABLE IF NOT EXISTS TaiKhoan (
  maTaiKhoan  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenDangNhap TEXT NOT NULL UNIQUE,
  matKhau     TEXT NOT NULL,                 -- luu dang bam (NFR-02)
  vaiTro      TEXT NOT NULL CHECK (vaiTro IN ('GIANG_VIEN','SINH_VIEN','PHONG_DAO_TAO')),
  hoTen       TEXT,                          -- chi dung cho tai khoan Phong dao tao
  ngaySinh    TEXT,                          -- YYYY-MM-DD, chi dung cho tai khoan Phong dao tao
  phaiDoiMatKhau INTEGER NOT NULL DEFAULT 0  -- 1 = mat khau ban dau, can doi o lan dang nhap dau
);
CREATE TABLE IF NOT EXISTS Khoa (
  maKhoa  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenKhoa TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Lop (
  maLop   INTEGER PRIMARY KEY AUTOINCREMENT,
  tenLop  TEXT NOT NULL UNIQUE,
  tenHienThi TEXT,
  khoaHoc TEXT,
  namTuyenSinh INTEGER,
  maKhoa  INTEGER NOT NULL REFERENCES Khoa(maKhoa)
);
CREATE TABLE IF NOT EXISTS GiangVien (
  maGiangVien INTEGER PRIMARY KEY AUTOINCREMENT,
  hoTen       TEXT NOT NULL,
  ngaySinh    TEXT,
  email       TEXT,
  soDienThoai TEXT,
  maKhoa      INTEGER NOT NULL REFERENCES Khoa(maKhoa),
  maTaiKhoan  INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS SinhVien (
  maSinhVien INTEGER PRIMARY KEY AUTOINCREMENT,
  maSoSinhVien TEXT NOT NULL UNIQUE,
  hoTen TEXT NOT NULL,
  ngaySinh TEXT,
  email TEXT,
  soDienThoai TEXT,
  namTuyenSinh INTEGER,
  maLop INTEGER NOT NULL REFERENCES Lop(maLop),
  maTaiKhoan INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS MonHoc (
  maMonHoc  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenMonHoc TEXT NOT NULL UNIQUE,
  soTinChi  INTEGER NOT NULL CHECK (soTinChi > 0)
);
CREATE TABLE IF NOT EXISTS PhongHoc (
  maPhong  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenPhong TEXT NOT NULL UNIQUE,
  sucChua  INTEGER NOT NULL CHECK (sucChua > 0)
);
CREATE TABLE IF NOT EXISTS ThoiKhoaBieu (
  maTKB       INTEGER PRIMARY KEY AUTOINCREMENT,
  ngayHoc     TEXT    NOT NULL,              -- YYYY-MM-DD
  tietBatDau  INTEGER NOT NULL,
  tietKetThuc INTEGER NOT NULL,
  hocKy       TEXT,
  namHoc      TEXT,
  maGiangVien INTEGER NOT NULL REFERENCES GiangVien(maGiangVien),
  maMonHoc    INTEGER NOT NULL REFERENCES MonHoc(maMonHoc),
  maLop       INTEGER NOT NULL REFERENCES Lop(maLop),
  maPhong     INTEGER NOT NULL REFERENCES PhongHoc(maPhong),
  CHECK (tietBatDau <= tietKetThuc)
);
CREATE INDEX IF NOT EXISTS idx_tkb_ngay_gv    ON ThoiKhoaBieu(ngayHoc, maGiangVien);
CREATE INDEX IF NOT EXISTS idx_tkb_ngay_lop   ON ThoiKhoaBieu(ngayHoc, maLop);
CREATE INDEX IF NOT EXISTS idx_tkb_ngay_phong ON ThoiKhoaBieu(ngayHoc, maPhong);


-- Thong bao cua Phong dao tao (nghi, hoc bu, doi phong, doi lich, quan trong, chung).
CREATE TABLE IF NOT EXISTS ThongBao (
  maThongBao INTEGER PRIMARY KEY AUTOINCREMENT,
  loai TEXT NOT NULL CHECK (loai IN ('CHUNG','NGHI','DAY_BU','DOI_PHONG','DOI_LICH','QUAN_TRONG')),
  tieuDe TEXT NOT NULL,
  noiDung TEXT NOT NULL,
  maTKB INTEGER REFERENCES ThoiKhoaBieu(maTKB) ON DELETE SET NULL,
  doiTuong TEXT NOT NULL DEFAULT 'TAT_CA'
    CHECK (doiTuong IN ('TAT_CA','TAT_CA_SV','TAT_CA_GV','LOP','GIANG_VIEN','LOP_VA_GV')),
  maLop INTEGER REFERENCES Lop(maLop) ON DELETE CASCADE,
  maGiangVien INTEGER REFERENCES GiangVien(maGiangVien) ON DELETE CASCADE,
  maNguoiGui INTEGER REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL,
  trangThai TEXT NOT NULL DEFAULT 'DA_GUI' CHECK (trangThai IN ('NHAP','DA_GUI')),
  ngayTao TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  thoiGianGui TEXT,
  ngayCapNhat TEXT,
  CHECK (doiTuong NOT IN ('LOP','LOP_VA_GV') OR maLop IS NOT NULL),
  CHECK (doiTuong NOT IN ('GIANG_VIEN','LOP_VA_GV') OR maGiangVien IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_thongbao_lop ON ThongBao(maLop, ngayTao);
CREATE INDEX IF NOT EXISTS idx_thongbao_gv ON ThongBao(maGiangVien, ngayTao);

-- Trang thai da doc cua tung tai khoan.
CREATE TABLE IF NOT EXISTS ThongBaoDaDoc (
  maThongBao INTEGER NOT NULL REFERENCES ThongBao(maThongBao) ON DELETE CASCADE,
  maTaiKhoan INTEGER NOT NULL REFERENCES TaiKhoan(maTaiKhoan) ON DELETE CASCADE,
  thoiGianDoc TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  PRIMARY KEY (maThongBao, maTaiKhoan)
);

-- Bo dem ma sinh vien theo khoa: chi tang, khong bao gio cap lai ma da xoa.
CREATE TABLE IF NOT EXISTS BoDemMaSinhVien (
  namTuyenSinh INTEGER PRIMARY KEY,
  soCuoi INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS CauHinhHeThong (
  khoa TEXT PRIMARY KEY,
  giaTri TEXT
);
