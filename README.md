# Ung dung quan ly thoi khoa bieu - Truong Dai hoc Hai Phong

Bai tap lon hoc phan Ky nghe phan mem (INF722).

## 1. Chuc nang

- Sinh vien xem thoi khoa bieu cua lop minh.
- Giang vien xem lich giang day cua minh.
- Phong Dao tao quan ly thoi khoa bieu, danh muc va thong ke.
- Kiem tra trung lich giang vien, lop hoc va phong hoc.
- Quan ly khoa, lop, mon hoc, phong hoc, giang vien va sinh vien.
- Sinh vien / giang vien xuat thoi khoa bieu cua chinh minh ra PDF (A4 ngang) va Excel (.xlsx).
- Phong Dao tao tao, sua, xoa, gui thong bao den tat ca sinh vien, tat ca giang vien, mot lop hoac mot giang vien;
  sinh vien / giang vien co muc Thong bao rieng, phan biet moi - da doc va dem so thong bao chua doc.
- Du lieu 4 khoa tuyen sinh 2024-2027; ma sinh vien tu sinh theo khoa (2401, 2501, 2601, 2701...).
- Dang nhap chung cho 3 vai tro (he thong tu nhan dien vai tro), tai khoan tao theo quy tac ho ten + ngay sinh.

## 2. Cong nghe

- Python 3, Flask
- SQLite
- HTML, CSS, JavaScript

## 3. Cai dat tren Windows

Mo thu muc co `app.py` va `requirements.txt` bang VS Code. Mo Terminal tai thu muc nay va chay:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Neu PowerShell chan script kich hoat, chay:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Mo trinh duyet tai `http://127.0.0.1:5000`.

## 4. Tai khoan mau

Man hinh dang nhap chung, **khong can chon vai tro**: he thong tu nhan dien vai tro tu tai khoan.

| Vai tro | Ten dang nhap | Mat khau |
|---|---|---|
| Phong Dao tao (theo quy tac) | `tranthiminhanh08092003` | `Tranthiminhanh08092003` |
| Giang vien (theo quy tac) | `lehoangnam12051985` | `Lehoangnam12051985` |
| Sinh vien khoa 2024 (theo quy tac) | `nguyenvanan15032004` | `Nguyenvanan15032004` |

Tai khoan cu (`pdt`, `gv1`, `sv1`...) duoc giu nguyen de khong lam mat du lieu. Tai khoan tao theo quy tac bi nhac doi mat
khau o lan dang nhap dau. Day la tai khoan demo, khong su dung cho he thong that.

### Quy tac tai khoan (tai khoan tao moi)

- **Ten dang nhap** = ho ten viet thuong, bo dau, bo khoang trang + ngay sinh `ddmmyyyy`
  (`Nguyễn Văn An`, 15/03/2004 → `nguyenvanan15032004`; giu so 0 dau ngay/thang).
- **Mat khau ban dau** = ho ten **khong dau, khong khoang trang, chi viet hoa chu cai dau tien**, con lai viet thuong + `ddmmyyyy`
  (→ `Nguyenvanan15032004`).
- Mat khau luu dang bam (Werkzeug), khong tra ve frontend. Trung ten dang nhap: khong ghi de, bao Phong Dao tao va
  de xuat hau to `_2`, `_3`... (chi doi ten dang nhap, mat khau van theo quy tac) - Phong Dao tao dong y moi tao.
- Nguoi dung cu chua co ngay sinh: tai khoan giu nguyen; Phong Dao tao bo sung ngay sinh roi bam **Cap TK** neu muon chuyen
  sang tai khoan theo quy tac (co hoi xac nhan vi mat khau se duoc dat lai).

### Quy tac ma sinh vien

4 chu so: 2 so cuoi nam tuyen sinh + so thu tu 01-99 trong khoa (khoa 2025: 2501, 2502, ...). He thong tu cap trong
giao dich `BEGIN IMMEDIATE`, co bo dem (khong cap lai ma da xoa), rang buoc UNIQUE + trigger kiem tra dinh dang. Khong doi
ma khi sua thong tin. Khoa vuot 99 sinh vien: bao loi va de xuat mo rong sang 5 chu so (khong tu y tao ma sai dinh dang).

## 5. Du lieu mau mo rong (gom 4 khoa 2024-2027)

Lan chay tiep theo, ung dung tu dong bo sung du lieu demo con thieu va khong xoa du lieu da co:

- 5 khoa.
- 11 lop, gom CNTT, Quan tri kinh doanh, Du lich, Ngoai ngu va Dien - Dien tu.
- 12 giang vien.
- 30 sinh vien.
- 20 mon hoc.
- 12 phong hoc.
- Khoang 315 buoi hoc trong khoang tuan demo.

Cac lop moi gom `CT2301`, `CT2302`, `QTKD2301`, `DL2301`, `DL2302`, `NN2301`, `DDT2301`, `DDT2302`.

Tai khoan moi:
- Giang vien: `gv5` den `gv12`, mat khau `gv123`.
- Sinh vien: `sv7` den `sv30`, mat khau `sv123`.

Bo sung (chi tao mot lan): 4 khoa tuyen sinh 2024, 2025, 2026, 2027, moi khoa 9 lop (CNTT 1-4, QTKD 1-2, Du lich 1,
Ngoai ngu 1, Dien - Dien tu 1) va 49 sinh vien (ma 2401-2449, 2501-2549, 2601-2649, 2701-2749), 12 giang vien moi,
lich hoc cho cac lop moi (khong trung lich). Cac lop cu CT22xx/CT23xx giu nguyen, ma sinh vien cu `SV0001`... duoc doi
sang dang 2201..., 2301... theo khoa cua lop.

Du lieu la du lieu gia lap phuc vu hoc tap va trinh dien, khong phai danh sach that cua Truong Dai hoc Hai Phong.

## 6. Thong ke

Muc Thong ke cua Phong Dao tao hien thi:
- Tong so buoi hoc.
- So buoi theo giang vien, phong hoc, lop va mon hoc.
- So giang vien theo khoa.

Neu trang web dang mo tu truoc khi cap nhat, nhan `Ctrl + F5` de tai lai JavaScript moi.

## 7. Co so du lieu

SQLite duoc tao tu dong tai `instance/tkb.sqlite3` khi chay ung dung. Khi nang cap tu ban cu, ung dung **tu dong sao luu**
CSDL thanh `instance/tkb.sqlite3.bak-<thoi gian>` roi moi chuyen doi (them cot, doi bang ThongBao, doi ma sinh vien). Ham khoi tao du lieu mau co tinh bo sung: khi chay lai, no them cac ban ghi demo con thieu, khong tu dong xoa du lieu cu.

Khong xoa `instance/tkb.sqlite3` neu ban dang co du lieu muon giu lai.

## 8. Kiem thu

Tai thu muc goc du an, kich hoat moi truong ao va chay:

```powershell
python -m unittest -v
```

## 9. Dung may chu

Trong Terminal dang chay Flask, nhan `Ctrl + C` de dung may chu. De mo lai, chay `python app.py`.


## Chức năng xuất thời khóa biểu

`GET /api/tkb/xuat?dinhDang=pdf|xlsx&tuan=YYYY-MM-DD` (hoặc `&tuNgay=...&denNgay=...`). Chỉ sinh viên (lớp mình) và giảng
viên (lịch của mình); gửi `maLop`/`maGiangVien` của người khác bị từ chối 403. PDF dùng font DejaVu Sans đóng gói sẵn
trong `tkb/fonts/` nên hiển thị đúng tiếng Việt trên mọi máy.

## Chức năng thông báo thay đổi lịch

- Phòng Đào tạo có thể gửi thông báo nghỉ học kèm lý do cho lớp và giảng viên liên quan.
- Phòng Đào tạo có thể tạo buổi dạy bù. Hệ thống kiểm tra trùng giảng viên, lớp và phòng trước khi lưu.
- Phòng Đào tạo có thể đổi phòng học; hệ thống kiểm tra phòng mới trước khi cập nhật.
- Phòng Đào tạo có thể phát hành thông báo chung.
- Sinh viên chỉ xem thông báo của lớp mình; giảng viên chỉ xem thông báo liên quan đến mình; Phòng Đào tạo xem toàn bộ.
- Các buổi đã có thông báo nghỉ được đánh dấu trong danh sách lịch học.

Các API tương ứng: `GET /api/thong-bao`, `POST /api/tkb/<ma>/nghi-hoc`,
`POST /api/tkb/<ma>/day-bu`, `POST /api/tkb/<ma>/doi-phong` và
`POST /api/thong-bao/chung`.

### Hệ thống thông báo của Phòng Đào tạo

- Loại: chung, nghỉ học, học bù, thay đổi phòng học, thay đổi lịch học, quan trọng. Đối tượng nhận: tất cả sinh viên,
  tất cả giảng viên, một lớp, một giảng viên (và "tất cả" cho các thông báo chung cũ). Trạng thái: bản nháp / đã gửi.
- Phòng Đào tạo: `POST /api/thong-bao`, `PUT /api/thong-bao/<ma>`, `POST /api/thong-bao/<ma>/gui`, `DELETE /api/thong-bao/<ma>`.
- Sinh viên / giảng viên: `GET /api/thong-bao`, `GET /api/thong-bao/<ma>`, `GET /api/thong-bao/so-chua-doc`,
  `POST /api/thong-bao/<ma>/da-doc`, `POST /api/thong-bao/da-doc-tat-ca`. Truy cập thông báo ngoài phạm vi trả 403.

## Nhập dữ liệu từ Excel

Nút **Nhập từ Excel** ở Danh mục và Quản lý TKB (có file mẫu). Sinh viên: cột Họ tên, Ngày sinh, Lớp (mã sinh viên và
tài khoản được hệ thống tự tạo).
