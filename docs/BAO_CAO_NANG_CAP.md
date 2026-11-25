# Báo cáo nâng cấp – Hệ thống quản lý thời khóa biểu

## 1. Vấn đề phát hiện trong mã nguồn nhận được (đã xử lý)

| # | Phát hiện | Xử lý |
|---|---|---|
| 1 | `static/app.js` trong file ZIP **rỗng (0 byte)** – bản chỉnh sửa chưa commit đã làm mất giao diện. | Khôi phục từ commit gần nhất rồi viết tiếp. Giao diện nhập Excel và xóa thông báo (backend có, giao diện mất theo) được dựng lại. **Các thay đổi giao diện chưa commit khác của bạn không thể khôi phục.** |
| 2 | Mã sinh viên cũ `SV0001` không theo quy tắc khóa; sinh viên/giảng viên chưa có ngày sinh. | Migration: thêm cột, đổi mã (60 SV → 2201–2214, 2301–2346), tài khoản cũ giữ nguyên. |
| 3 | Bảng `ThongBao` chỉ có 4 loại, không có đối tượng/trạng thái/đã đọc. | Dựng lại bảng bằng quy trình chuẩn SQLite, giữ 2 thông báo cũ. |
| 4 | Xóa sinh viên/giảng viên để lại tài khoản mồ côi. | Xóa kèm tài khoản. |
| 5 | Giao diện đăng nhập có bước chọn vai trò; nút đổi theme bị ẩn bằng CSS. | Bỏ chọn vai trò (tự nhận diện); hiện lại nút theme, trang đăng nhập theo theme sáng/tối. |
| 6 | Sửa lớp trên giao diện ghi đè tên lớp gốc bằng tên hiển thị. | Sửa tên hiển thị, giữ mã lớp gốc. |

## 2. Quyết định cần bạn biết

- **Dữ liệu cũ có khóa 2022, 2023** (các lớp CT22xx/CT23xx): giữ nguyên, nên CSDL có 6 khóa (2022–2027).
- **Tài khoản cũ** (`pdt`, `gv1`, `sv1`…) giữ nguyên mật khẩu; chưa có ngày sinh nên chưa có tên theo quy tắc. Bổ sung ngày sinh rồi bấm **Cấp TK** (có xác nhận vì mật khẩu bị đặt lại).
- **Tên đăng nhập trùng**: không ghi đè; đề xuất hậu tố `_2`, `_3`… (chỉ đổi tên đăng nhập, mật khẩu vẫn theo quy tắc) và hỏi Phòng Đào tạo.
- **Mật khẩu ban đầu đoán được từ họ tên + ngày sinh** (theo yêu cầu) → tài khoản tạo theo quy tắc bị nhắc đổi mật khẩu ở lần đầu (khuyến khích, không bắt buộc).
- **Khóa quá 99 sinh viên**: báo lỗi 409 kèm đề xuất mở rộng 5 chữ số (YYNNN); không tự tạo mã sai định dạng.
- **Mã sinh viên đã xóa không được cấp lại** (bảng bộ đếm `BoDemMaSinhVien`).
- Xuất TKB chỉ dành cho sinh viên/giảng viên (Phòng Đào tạo nhận 403) theo đúng đặc tả.
- Đối tượng nhận thông báo có thêm "Tất cả (sinh viên và giảng viên)" để giữ các thông báo chung cũ.
- Tìm kiếm số 1–4 chữ số trong Sinh viên khớp theo **đầu mã** (26 → cả khóa 2026; 2601 → đúng 1 mã).

## 3. File đã chỉnh sửa
`README.md`, `app.py`, `requirements.txt` (thêm reportlab), `static/app.js`, `static/style.css`, `tests/test_api.py`,
`tkb/auth.py`, `tkb/config.py`, `tkb/db.py`, `tkb/errors.py`, `tkb/schema.sql`, `tkb/seed.py`,
`tkb/controllers/{auth,danh_muc,thong_bao,tkb}.py`, `tkb/services/{danh_muc,tai_khoan,thong_bao}.py`,
`tkb/controllers/nhap_excel.py` và `tkb/services/nhap_excel.py` (đã có sẵn nhưng chưa commit; sửa theo quy tắc mới).

## 4. File mới
`tkb/migrations.py`, `tkb/services/dinh_danh.py`, `tkb/services/nguoi_dung.py`, `tkb/services/xuat_tkb.py`,
`tkb/fonts/DejaVuSans.ttf`, `tkb/fonts/DejaVuSans-Bold.ttf`, `tkb/fonts/LICENSE-DejaVu.txt`,
`tests/test_migration.py`, `docs/BAO_CAO_NANG_CAP.md`, `docs/ket_qua_kiem_thu.txt`.

## 5. Thay đổi cơ sở dữ liệu (tự động, có sao lưu)
- `TaiKhoan`: + `hoTen`, `ngaySinh` (nhân sự PĐT), `phaiDoiMatKhau`.
- `Lop`: + `namTuyenSinh` (suy từ "K23"/mã lớp). `GiangVien`: + `ngaySinh`. `SinhVien`: + `ngaySinh`, `namTuyenSinh`.
- `ThongBao` dựng lại: + loại `DOI_LICH`, `QUAN_TRONG`; `doiTuong`, `maNguoiGui`, `trangThai`, `thoiGianGui`, `ngayCapNhat`.
- Bảng mới: `ThongBaoDaDoc` (đã đọc theo tài khoản), `BoDemMaSinhVien`, `CauHinhHeThong`.
- Ràng buộc: UNIQUE `maSoSinhVien`; trigger từ chối mã sai định dạng / không khớp khóa; chỉ mục theo khóa, lớp.
- `PRAGMA user_version = 3` (v3: mật khẩu ban đầu không dấu, không cách – chỉ đặt lại tài khoản chưa tự đổi mật khẩu). Trước khi nâng cấp tạo `instance/tkb.sqlite3.bak-<thời gian>`; chạy lại không đổi gì thêm.
- Kết quả trên CSDL thật của bạn: 60 SV, 63 tài khoản, 430 buổi học, 2 thông báo đều còn nguyên; mật khẩu cũ không đổi.

## 6. Cập nhật và chạy
```powershell
python -m pip install -r requirements.txt     # có thêm reportlab
python app.py                                  # lần đầu: sao lưu + nâng cấp CSDL + seed (~30 giây)
python -m unittest -v
```
Nhấn Ctrl+F5 để tải JavaScript mới.

## 7. Tài khoản mẫu
`pdt/pdt123`, `gv1/gv123`, `sv1/sv123` (cũ) và theo quy tắc: PĐT `tranthiminhanh08092003` / `Tranthiminhanh08092003`;
GV `lehoangnam12051985` / `Lehoangnam12051985`; SV `nguyenvanan15032004` / `Nguyenvanan15032004`.

## 8. Kết quả kiểm thử (đã chạy thật)
- `python -m unittest -v`: **92 test, OK** (`docs/ket_qua_kiem_thu.txt`): quy tắc tài khoản, đăng nhập 3 vai trò, phân quyền,
  đổi mật khẩu, mã sinh viên (tuần tự, đồng thời 8 luồng, >99, trigger), sắp xếp/lọc/phân trang, xuất PDF/Excel
  (đọc lại nội dung, A4 ngang, tiếng Việt, 403 khi xem lớp/giảng viên khác), thông báo (đối tượng, 403, đã đọc, nháp),
  migration trên CSDL kiểu cũ.
- Chạy thật trên **bản sao CSDL của bạn** + Chromium headless: đăng nhập, nhắc đổi mật khẩu, tải PDF/Excel, thêm sinh viên,
  trùng tên → hậu tố, tạo/xóa thông báo, nhập Excel, đánh dấu đã đọc, theme sáng/tối, mobile 390px (không tràn ngang).
- Lỗi thật bắt được nhờ chạy trên dữ liệu thật và đã sửa: migration làm khóa ngoại bảng "đã đọc" trỏ nhầm bảng tạm (có test hồi quy).

## 9. Hạn chế còn lại
- Chưa thử trên Windows/Python 3.14 của bạn (đã chạy Python 3.12 trên Linux).
- Chưa có giới hạn số lần đăng nhập sai (ngoài phạm vi yêu cầu).
- Khoa seed cũ không có dấu ("Cong nghe thong tin") nên hiện như vậy trong file xuất; sửa trong Danh mục → Khoa.
- Tài khoản/ngày sinh của sinh viên cũ (dữ liệu demo) để trống, cần Phòng Đào tạo bổ sung.


---

## 10. Bổ sung: giảng viên gửi thông báo và phân biệt nguồn gửi (phiên bản CSDL 4)

**CSDL:** bảng `ThongBao` dựng lại (giữ nguyên mọi thông báo và trạng thái đã đọc; mọi thông báo cũ → `sender_type=PHONG_DAO_TAO`):
+ `sender_type`, `maGiangVienGui`, `tenNguoiGui`, `maMonHoc`, `tenMonHoc`; thêm 6 loại thông báo của giảng viên; ràng buộc CHECK:
thông báo của giảng viên bắt buộc `doiTuong='LOP'` có lớp. Tự động sao lưu trước khi nâng cấp.

**API mới/đổi:** `GET /api/thong-bao/lop-duoc-gui` (giảng viên); `POST/PUT/DELETE /api/thong-bao...` mở cho giảng viên với kiểm tra
quyền riêng; `GET /api/thong-bao?daGui=1` (giảng viên), `?nguon=`, `?daDoc=1`.

**Quyết định cần bạn biết:** (1) "đang dạy" = có buổi học từ 30 ngày trước trở đi; (2) khóa sau 24 giờ kể từ lúc gửi;
(3) Phòng Đào tạo chỉ xóa (không sửa) thông báo của giảng viên; (4) tên người gửi hiển thị là tên lưu lúc gửi; (5) sửa nội dung
trong thời gian cho phép sẽ ghi "Chỉnh sửa lần cuối" (không lưu lịch sử phiên bản).

**Kiểm thử:** 114 test đều đạt (`docs/ket_qua_kiem_thu.txt`), gồm 21 test thông báo giảng viên (gửi đúng/sai lớp, giả mạo nguồn gửi,
sửa/xóa của người khác và của PĐT, khóa 24 giờ, hết phân công, bản nháp, đã đọc lưu qua đăng xuất, bộ lọc, snapshot tên) và test
nâng cấp v3→v4. Chạy thật trên bản sao CSDL của bạn + Chromium: giảng viên tạo/sửa/xóa/gửi, sinh viên thấy nhãn và lọc đúng, theme sáng/tối.


---

## 11. Bổ sung: áp dụng quy tắc tên đăng nhập/mật khẩu cho cả tài khoản cũ (phiên bản CSDL 5)

- Tên đăng nhập = họ tên thường, không dấu, không cách + ddmmyyyy; mật khẩu = giống tên đăng nhập, **chỉ viết hoa chữ cái đầu**; băm bằng
  `generate_password_hash`, xác thực bằng `check_password_hash`.
- **Một hàm dùng chung** `tai_khoan.thong_tin_theo_quy_tac()` cho tài khoản mới, tài khoản cũ (`chuan_hoa_theo_quy_tac`: đổi tại chỗ, giữ `maTaiKhoan`)
  và seed; nút **Cấp TK** cũng dùng hàm này (trước đây xóa tài khoản rồi tạo lại làm mất trạng thái đã đọc).
- **Migration tự động (có sao lưu)**: mọi tài khoản sinh viên/giảng viên cũ (`sv1`…, `gv1`…, `svm*`) chuyển sang quy tắc, bật nhắc đổi mật khẩu.
  Tài khoản đã đúng quy tắc giữ nguyên, kể cả mật khẩu người dùng đã tự đổi. Tài khoản Phòng Đào tạo `pdt/pdt123` **không bị đổi**.
- **Lưu ý quan trọng:** sinh viên/giảng viên cũ chưa có ngày sinh nên mình gán **ngày sinh TẠM (dữ liệu demo, cố định theo số thứ tự)** để tạo được tên đăng nhập.
  Đây không phải ngày sinh thật; hãy cập nhật bằng ngày sinh thật rồi bấm Cấp TK. Người chưa có tài khoản (3 sinh viên cũ) không bị tạo mới.
- Seed không còn tạo lại `sv1/gv1` cũ: nhận diện người theo (họ tên + lớp/khoa) nên khởi động lại không nhân đôi dữ liệu (đã có test).
- Kiểm thử: **119 test đạt** (`docs/ket_qua_kiem_thu.txt`), gồm test mọi tài khoản sv/gv đúng quy tắc + mật khẩu băm, đăng nhập bằng tài khoản cũ đã đổi,
  từ chối `sv1/sv123`, khởi động lại không nhân đôi, và migration v4→v5.
