# Ung dung quan ly thoi khoa bieu - Truong Dai hoc Hai Phong

Bai tap lon hoc phan Ky nghe phan mem (INF722).

## 1. Chuc nang

- Sinh vien xem thoi khoa bieu cua lop minh.
- Giang vien xem lich giang day cua minh.
- Phong Dao tao quan ly thoi khoa bieu, danh muc va thong ke.
- Kiem tra trung lich giang vien, lop hoc va phong hoc.
- Quan ly khoa, lop, mon hoc, phong hoc, giang vien va sinh vien.

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

| Vai tro | Ten dang nhap | Mat khau |
|---|---|---|
| Phong Dao tao | `pdt` | `pdt123` |
| Giang vien | `gv1` den `gv12` | `gv123` |
| Sinh vien | `sv1` den `sv30` | `sv123` |

Chon dung vai tro tren man hinh dang nhap. Day la tai khoan demo, khong su dung cho he thong that.

## 5. Du lieu mau mo rong

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

Du lieu la du lieu gia lap phuc vu hoc tap va trinh dien, khong phai danh sach that cua Truong Dai hoc Hai Phong.

## 6. Thong ke

Muc Thong ke cua Phong Dao tao hien thi:
- Tong so buoi hoc.
- So buoi theo giang vien, phong hoc, lop va mon hoc.
- So giang vien theo khoa.

Neu trang web dang mo tu truoc khi cap nhat, nhan `Ctrl + F5` de tai lai JavaScript moi.

## 7. Co so du lieu

SQLite duoc tao tu dong tai `instance/tkb.sqlite3` khi chay ung dung. Ham khoi tao du lieu mau co tinh bo sung: khi chay lai, no them cac ban ghi demo con thieu, khong tu dong xoa du lieu cu.

Khong xoa `instance/tkb.sqlite3` neu ban dang co du lieu muon giu lai.

## 8. Kiem thu

Tai thu muc goc du an, kich hoat moi truong ao va chay:

```powershell
python -m unittest -v
```

## 9. Dung may chu

Trong Terminal dang chay Flask, nhan `Ctrl + C` de dung may chu. De mo lai, chay `python app.py`.
