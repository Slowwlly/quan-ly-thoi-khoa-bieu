-- Luoc do quan he theo muc 3.4.6 cua bao cao (suy ra tu bieu do lop).
CREATE TABLE IF NOT EXISTS TaiKhoan (
  maTaiKhoan  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenDangNhap TEXT NOT NULL UNIQUE,
  matKhau     TEXT NOT NULL,                 -- luu dang bam (NFR-02)
  vaiTro      TEXT NOT NULL CHECK (vaiTro IN ('GIANG_VIEN','SINH_VIEN','PHONG_DAO_TAO'))
);
CREATE TABLE IF NOT EXISTS Khoa (
  maKhoa  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenKhoa TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Lop (
  maLop   INTEGER PRIMARY KEY AUTOINCREMENT,
  tenLop  TEXT NOT NULL UNIQUE,
  khoaHoc TEXT,
  maKhoa  INTEGER NOT NULL REFERENCES Khoa(maKhoa)
);
CREATE TABLE IF NOT EXISTS GiangVien (
  maGiangVien INTEGER PRIMARY KEY AUTOINCREMENT,
  hoTen       TEXT NOT NULL,
  email       TEXT,
  soDienThoai TEXT,
  maKhoa      INTEGER NOT NULL REFERENCES Khoa(maKhoa),
  maTaiKhoan  INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS SinhVien (
  maSinhVien  INTEGER PRIMARY KEY AUTOINCREMENT,
  hoTen       TEXT NOT NULL,
  email       TEXT,
  soDienThoai TEXT,
  maLop       INTEGER NOT NULL REFERENCES Lop(maLop),
  maTaiKhoan  INTEGER UNIQUE REFERENCES TaiKhoan(maTaiKhoan) ON DELETE SET NULL
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
