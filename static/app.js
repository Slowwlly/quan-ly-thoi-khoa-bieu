'use strict';
// ===== CHUYEN DOI THEME SANG / TOI =====
function getTheme() {
    return localStorage.getItem('theme') || 'dark';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);

    localStorage.setItem('theme', theme);

    const btn = document.getElementById('themeToggle');

    if (btn) {
        btn.textContent = theme === 'dark' ? '🌙' : '☀️';
    }
}

function toggleTheme() {
    const newTheme = getTheme() === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}
setTheme(getTheme());
/* Giao dien web thuan HTML/CSS/JS, goi API cua Flask. Moi du lieu dong deu duoc esc() truoc khi chen vao HTML. */
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const THU = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];
const GV = 'GIANG_VIEN', SV = 'SINH_VIEN', PDT = 'PHONG_DAO_TAO';

async function api(method, url, body) {
  const r = await fetch(url, { method, credentials: 'same-origin', headers: body ? { 'Content-Type': 'application/json' } : {}, body: body ? JSON.stringify(body) : undefined });
  let data = null; try { data = await r.json(); } catch { /* khong co noi dung JSON */ }
  if (!r.ok) { const e = new Error((data && data.loi) || 'Co loi xay ra'); e.status = r.status; throw e; }
  return data;
}
let toastTimer;
function toast(msg, err) {
  const t = $('#toast'); t.textContent = msg; t.className = 'show' + (err ? ' err' : '');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.className = '', 3200);
}
// ---- ngay gio (dung gio dia phuong, tranh lech mui gio cua toISOString) ----
const pad = n => String(n).padStart(2, '0');
const iso = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parse = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const monday = d => addDays(d, -((d.getDay() + 6) % 7));
const fmt = s => { const [y, m, d] = s.split('-'); return `${d}/${m}/${y}`; };
const fmtShort = d => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
const thuOf = s => THU[(parse(s).getDay() + 6) % 7];

const S = { user: null, tab: 'tkb', lists: {}, tkb: { mode: 'tuan', date: iso(new Date()), maLop: '', maMonHoc: '', q: '', dang: innerWidth > 800 ? 'luoi' : 'ds' },
  ql: { date: iso(new Date()), maLop: '' }, dm: 'khoa' };

async function boot() { try { S.user = await api('GET', '/api/toi'); } catch { S.user = null; } render(); }
function render() { S.user ? shell() : loginView(); }

// ---------------- Đăng nhập ----------------
function loginView() {
  const roles = [
    ['SINH_VIEN', 'Sinh viên', 'Tra cứu thời khóa biểu cá nhân', 'graduation-cap'],
    ['GIANG_VIEN', 'Giảng viên', 'Xem lịch giảng dạy của mình', 'chalkboard'],
    ['PHONG_DAO_TAO', 'Phòng Đào tạo', 'Tạo và sắp xếp thời khóa biểu', 'calendar']
  ];
  $('#app').innerHTML = `<div class="login-page">
    <div class="login-brand">
      <div class="brand-mark">HP</div>
      <div><span class="eyebrow">TRƯỜNG ĐẠI HỌC HẢI PHÒNG</span><h1>Hệ thống quản lý<br>thời khóa biểu</h1>
      <p>Theo dõi lịch học và lịch giảng dạy tập trung, thuận tiện.</p></div>
      <div class="login-note"><span>INF722 · Kỹ nghệ phần mềm</span><span>Hệ thống phục vụ sinh viên, giảng viên và Phòng Đào tạo</span></div>
    </div>
    <div class="login-panel">
      <div class="login-heading"><span class="eyebrow">CỔNG THÔNG TIN</span><h2>Đăng nhập</h2><p class="muted">Chọn vai trò, sau đó nhập tài khoản của bạn.</p></div>
      <form id="f" class="form" autocomplete="on">
        <div class="role-picker" role="radiogroup" aria-label="Chọn vai trò">
          ${roles.map(([v,n,d]) => `<label class="role-option"><input type="radio" name="vaiTro" value="${v}" ${v==='SINH_VIEN'?'checked':''}><span class="role-icon">${v==='SINH_VIEN'?'SV':v==='GIANG_VIEN'?'GV':'PDT'}</span><span class="role-copy"><b>${n}</b><small>${d}</small></span><span class="role-check">✓</span></label>`).join('')}
        </div>
        <label>Tên đăng nhập<input name="tenDangNhap" required autofocus autocomplete="username" placeholder="Nhập tên đăng nhập"></label>
        <label>Mật khẩu<input name="matKhau" type="password" required autocomplete="current-password" placeholder="Nhập mật khẩu"></label>
        <div id="err" class="error" hidden></div>
        <button class="btn login-submit">Đăng nhập <span aria-hidden="true">→</span></button>
      </form>
      <details class="demo-accounts"><summary>Tài khoản mẫu để trải nghiệm</summary>
        <p><b>Phòng Dao tao:</b> pdt / pdt123<br><b>Giang vien:</b> gv1 – gv4 / gv123<br><b>Sinh vien:</b> sv1 – sv6 / sv123</p></details>
      <p class="login-foot">© Truong Dai hoc Hai Phòng · Ứng dụng quản lý thời khóa biểu</p>
    </div>
  </div>`;
  $('#f').onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target); const err = $('#err'); err.hidden = true;
    try {
      const result = await api('POST', '/api/dang-nhap', { tenDangNhap: f.get('tenDangNhap'), matKhau: f.get('matKhau') });
      if (result.vaiTro !== f.get('vaiTro')) {
        await api('POST', '/api/dang-xuat');
        throw new Error('Vai trò đã chọn không khớp với tài khoản. Vui lòng chọn đúng vai trò.');
      }
      S.lists = {}; S.tab = 'tkb'; await boot();
    } catch (ex) { err.textContent = ex.message; err.hidden = false; }
  };
}

// ---------------- Khung chinh ----------------
function shell() {
  const u = S.user;
  const tabs = [['tkb', 'Thời khóa biểu']];
  if (u.vaiTro === PDT) tabs.push(['quanly', 'Quản lý TKB'], ['danhmuc', 'Danh mục'], ['thongke', 'Thống kê']);
  tabs.push(['taikhoan', 'Tài khoản']);
  $('#app').innerHTML = `<header class="top"><h1>Thời khóa biểu – DH Hai Phòng</h1>
      <span class="who">${esc(u.hoTen)} · ${esc(u.tenVaiTro)}</span>

<button class="theme-toggle" id="themeToggle" type="button"
  title="Chuyển đổi giao diện">
  ${getTheme() === 'dark' ? '🌙' : '☀️'}
</button>

<button class="btn sec sm" id="out"
  style="color:#fff;border-color:#fff">Đăng xuất</button>
</header>
    <nav class="tabs" aria-label="Chức năng">${tabs.map(([k, t]) => `<button data-k="${k}" ${S.tab === k ? 'aria-current="page"' : ''}>${t}</button>`).join('')}</nav>
    <main id="main"></main>`;
  $('#out').onclick = async () => {
    await api('POST', '/api/dang-xuat');
    S.user = null;
    S.lists = {};
    render();
};
  $('#themeToggle').onclick = toggleTheme;
  document.querySelectorAll('nav.tabs button').forEach(b => b.onclick = () => { S.tab = b.dataset.k; shell(); });
  ({ tkb: viewTkb, quanly: viewQuanLy, danhmuc: viewDanhMuc, thongke: viewThongKe, taikhoan: viewTaiKhoan })[S.tab]().catch(handle);
}
function handle(e) { if (e.status === 401) { S.user = null; render(); } else toast(e.message, true); }
async function lists(...names) {
  const url = { lop: '/api/danh-muc/lop', mon: '/api/danh-muc/mon-hoc', phong: '/api/danh-muc/phong-hoc', gv: '/api/danh-muc/giang-vien', khoa: '/api/danh-muc/khoa' };
  await Promise.all(names.filter(n => !S.lists[n]).map(async n => S.lists[n] = await api('GET', url[n])));
}
const opts = (arr, v, t, sel, blank) => (blank !== undefined ? `<option value="">${esc(blank)}</option>` : '') +
  arr.map(x => `<option value="${esc(x[v])}" ${String(sel) === String(x[v]) ? 'selected' : ''}>${esc(typeof t === 'function' ? t(x) : x[t])}</option>`).join('');

// ---------------- Xem thoi khoa bieu ----------------
async function viewTkb() {
  const u = S.user, t = S.tkb;
  await lists('lop', 'mon');
  $('#main').innerHTML = `<div class="card"><div class="bar">
      <label>Chế độ<select id="mode"><option value="tuan">Theo tuần</option><option value="ngay">Theo ngày</option></select></label>
      <label>Ngày<input type="date" id="date" value="${esc(t.date)}"></label>
      <button class="btn sec" id="prev" aria-label="Trước">‹</button><button class="btn sec" id="today">Hôm nay</button><button class="btn sec" id="next" aria-label="Sau">›</button>
      ${u.vaiTro === SV ? '' : `<label>Lớp<select id="lop">${opts(S.lists.lop, 'maLop', 'tenLop', t.maLop, 'Tất cả')}</select></label>`}
      <label>Môn học<select id="mon">${opts(S.lists.mon, 'maMonHoc', 'tenMonHoc', t.maMonHoc, 'Tất cả')}</select></label>
      <label>Tìm kiếm<input id="q" type="search" placeholder="Mon, giang vien, lop, phong…" value="${esc(t.q)}"></label>
      <label>Hiển thị<select id="dang"><option value="luoi">Lưới</option><option value="ds">Danh sách</option></select></label>
    </div><div id="kq"></div></div>`;
  $('#mode').value = t.mode; $('#dang').value = t.dang;
  const reload = () => loadTkb().catch(handle);
  const step = n => { t.date = iso(addDays(parse(t.date), n * (t.mode === 'tuan' ? 7 : 1))); $('#date').value = t.date; reload(); };
  $('#mode').onchange = e => { t.mode = e.target.value; reload(); };
  $('#date').onchange = e => { if (e.target.value) { t.date = e.target.value; reload(); } };
  $('#prev').onclick = () => step(-1); $('#next').onclick = () => step(1);
  $('#today').onclick = () => { t.date = iso(new Date()); $('#date').value = t.date; reload(); };
  if ($('#lop')) $('#lop').onchange = e => { t.maLop = e.target.value; reload(); };
  $('#mon').onchange = e => { t.maMonHoc = e.target.value; reload(); };
  $('#q').onchange = e => { t.q = e.target.value.trim(); reload(); };
  $('#dang').onchange = e => { t.dang = e.target.value; reload(); };
  reload();
}
async function loadTkb() {
  const t = S.tkb, p = new URLSearchParams();
  const tim = !!t.q;
  if (t.q) p.set('q', t.q); else p.set(t.mode === 'tuan' ? 'tuan' : 'ngay', t.date);   // co tu khoa → tim tren moi ngay (UC-03)
  if (t.maLop && S.user.vaiTro !== SV) p.set('maLop', t.maLop);
  if (t.maMonHoc) p.set('maMonHoc', t.maMonHoc);
  const ds = await api('GET', '/api/tkb?' + p);
  const kq = $('#kq'); if (!kq) return;
  const mon = parse(t.date), thu2 = monday(mon);
  const tieuDe = tim ? `Kết quả tìm kiếm “${esc(t.q)}”: ${ds.length} buổi học`
    : t.mode === 'tuan' ? `Tuần ${fmtShort(thu2)} – ${fmtShort(addDays(thu2, 6))}/${addDays(thu2, 6).getFullYear()}` : `${THU[(mon.getDay() + 6) % 7]}, ${fmt(t.date)}`;
  let body;
  if (!ds.length) body = `<div class="empty">${tim ? 'Không tìm thấy buổi học phù hợp.' : 'Không có lịch học trong khoảng thời gian này.'}</div>`;
  else if (!tim && t.mode === 'tuan' && t.dang === 'luoi' && !coVaCham(ds)) body = luoiTuan(ds, thu2);
  else body = danhSachNgày(ds);
  kq.innerHTML = `<h2 style="font-size:1.05rem;margin:.2rem 0 .8rem">${tieuDe}</h2>${body}`;
  kq.querySelectorAll('[data-id]').forEach(b => b.onclick = () => chiTiết(b.dataset.id));
}
function coVaCham(ds) {
  const seen = new Set();
  for (const e of ds) for (let k = e.tietBatDau; k <= e.tietKetThuc; k++) { const key = e.ngayHoc + '-' + k; if (seen.has(key)) return true; seen.add(key); }
  return false;
}
function phu(e) { const v = S.user.vaiTro; return v === GV ? `Lớp ${e.tenLop}` : v === SV ? e.tenGiangVien : `${e.tenGiangVien} · ${e.tenLop}`; }
function moTa(e) { return `<b>${esc(e.tenMonHoc)}</b>Tiết ${e.tietBatDau}–${e.tietKetThuc} · ${esc(e.tenPhong)}<br>${esc(phu(e))}`; }
function luoiTuan(ds, thu2) {
  const tiet = S.user.tiet, today = iso(new Date());
  let h = '<div class="week"><div class="h" style="grid-row:1;grid-column:1"></div>';
  for (let i = 0; i < 7; i++) { const d = addDays(thu2, i); h += `<div class="h ${iso(d) === today ? 'today' : ''}" style="grid-row:1;grid-column:${i + 2}">${THU[i]}<br>${fmtShort(d)}</div>`; }
  tiet.forEach((x, r) => {
    h += `<div class="t" style="grid-row:${r + 2};grid-column:1">Tiết ${x.tiet}<br>${x.tu}</div>`;
    for (let c = 0; c < 7; c++) h += `<div class="slot" style="grid-row:${r + 2};grid-column:${c + 2}"></div>`;
  });
  for (const e of ds) {
    const wd = (parse(e.ngayHoc).getDay() + 6) % 7;
    h += `<button class="ev c${e.maMonHoc % 6}" data-id="${e.maTKB}" style="grid-row:${e.tietBatDau + 1} / span ${e.tietKetThuc - e.tietBatDau + 1};grid-column:${wd + 2}">${moTa(e)}</button>`;
  }
  return h + '</div>';
}
function danhSachNgày(ds) {
  const today = iso(new Date()), by = {};
  ds.forEach(e => (by[e.ngayHoc] ||= []).push(e));
  const tiet = S.user.tiet, gio = e => `${tiet[e.tietBatDau - 1]?.tu ?? ''}–${tiet[e.tietKetThuc - 1]?.den ?? ''}`;
  return Object.keys(by).sort().map(d => `<div class="day"><h3 class="${d === today ? 'today' : ''}">${thuOf(d)}, ${fmt(d)}${d === today ? ' (hôm nay)' : ''}</h3>` +
    by[d].map(e => `<button class="item" data-id="${e.maTKB}"><span class="when">Tiết ${e.tietBatDau}–${e.tietKetThuc}<br>${gio(e)}</span><span><b>${esc(e.tenMonHoc)}</b><br>Phòng ${esc(e.tenPhong)} · ${esc(phu(e))}</span></button>`).join('') + '</div>').join('');
}
async function chiTiết(id) {
  try {
    const e = await api('GET', '/api/tkb/' + id), tiet = S.user.tiet;
    openDlg(`<h2>Chi tiết buổi học</h2><dl class="dl">
      <dt>Môn học</dt><dd>${esc(e.tenMonHoc)} (${e.soTinChi} tín chỉ)</dd>
      <dt>Ngày học</dt><dd>${thuOf(e.ngayHoc)}, ${fmt(e.ngayHoc)}</dd>
      <dt>Tiết / giờ học</dt><dd>Tiết ${e.tietBatDau}–${e.tietKetThuc} (${tiet[e.tietBatDau - 1]?.tu ?? ''}–${tiet[e.tietKetThuc - 1]?.den ?? ''})</dd>
      <dt>Phòng học</dt><dd>${esc(e.tenPhong)}</dd><dt>Lớp</dt><dd>${esc(e.tenLop)}</dd><dt>Giang vien</dt><dd>${esc(e.tenGiangVien)}</dd>
      <dt>Học kỳ / năm học</dt><dd>${esc(e.hocKy || '—')} / ${esc(e.namHoc || '—')}</dd></dl>
      <div class="foot"><button class="btn" value="x" id="ok">Đóng</button></div>`);
    $('#ok').onclick = () => $('#dlg').close();
  } catch (ex) { handle(ex); }
}
function openDlg(html) { const d = $('#dlg'); d.innerHTML = html; if (!d.open) d.showModal(); }

// ---------------- Form dung chung ----------------
function openForm({ title, fields, submit = 'Lưu', onSubmit }) {
  const input = f => f.type === 'select'
    ? `<select name="${f.name}" ${f.required ? 'required' : ''}>${opts(f.options, 'v', 't', f.value, f.blank)}</select>`
    : `<input name="${f.name}" type="${f.type || 'text'}" value="${esc(f.value ?? '')}" ${f.required ? 'required' : ''} ${f.min ? `min="${f.min}"` : ''} ${f.type === 'password' ? 'autocomplete="new-password" minlength="6"' : ''}>`;
  const rows = []; for (let i = 0; i < fields.length; i++) {
    const f = fields[i], nx = fields[i + 1];
    if (f.half && nx && nx.half) { rows.push(`<div class="row"><label>${f.label}${input(f)}</label><label>${nx.label}${input(nx)}</label></div>`); i++; }
    else rows.push(`<label>${f.label}${input(f)}</label>`);
  }
  openDlg(`<h2>${esc(title)}</h2><form id="mf" class="form" method="dialog">${rows.join('')}<div id="mfe" class="error" hidden></div>
    <div class="foot"><button type="button" class="btn sec" id="cancel">Hủy</button><button class="btn" id="save">${esc(submit)}</button></div></form>`);
  $('#cancel').onclick = () => $('#dlg').close();
  $('#mf').onsubmit = async e => {
    e.preventDefault(); const data = Object.fromEntries(new FormData(e.target)); $('#mfe').hidden = true; $('#save').disabled = true;
    try { await onSubmit(data); $('#dlg').close(); }
    catch (ex) { if (ex.status === 401) return handle(ex); $('#mfe').textContent = ex.message; $('#mfe').hidden = false; }
    finally { const b = $('#save'); if (b) b.disabled = false; }
  };
}

// ---------------- Quan ly thoi khoa bieu (Phòng dao tao) ----------------
async function viewQuanLy() {
  await lists('lop', 'mon', 'phong', 'gv');
  const q = S.ql;
  $('#main').innerHTML = `<div class="card"><div class="bar">
    <label>Tuần chứa ngày<input type="date" id="d" value="${esc(q.date)}"></label>
    <label>Lớp<select id="l">${opts(S.lists.lop, 'maLop', 'tenLop', q.maLop, 'Tất cả')}</select></label>
    <button class="btn" id="add">+ Thêm buổi học</button></div><div id="kq"></div></div>`;
  $('#d').onchange = e => { q.date = e.target.value; tai(); }; $('#l').onchange = e => { q.maLop = e.target.value; tai(); };
  $('#add').onclick = () => formTkb();
  async function tai() {
    const p = new URLSearchParams({ tuan: q.date }); if (q.maLop) p.set('maLop', q.maLop);
    const ds = await api('GET', '/api/tkb?' + p);
    $('#kq').innerHTML = ds.length ? `<div class="tablewrap"><table><thead><tr><th>Ngày</th><th>Tiết</th><th>Môn học</th><th>Giang vien</th><th>Lớp</th><th>Phòng</th><th></th></tr></thead><tbody>` +
      ds.map(e => `<tr><td>${thuOf(e.ngayHoc)}, ${fmt(e.ngayHoc)}</td><td>${e.tietBatDau}–${e.tietKetThuc}</td><td>${esc(e.tenMonHoc)}</td><td>${esc(e.tenGiangVien)}</td><td>${esc(e.tenLop)}</td><td>${esc(e.tenPhong)}</td>
        <td class="actions"><button class="btn sec sm" data-e="${e.maTKB}">Sửa</button><button class="btn danger sm" data-x="${e.maTKB}">Xóa</button></td></tr>`).join('') + '</tbody></table></div>'
      : '<div class="empty">Không có buổi học trong tuần này.</div>';
    $('#kq').querySelectorAll('[data-e]').forEach(b => b.onclick = () => formTkb(ds.find(x => x.maTKB == b.dataset.e)));
    $('#kq').querySelectorAll('[data-x]').forEach(b => b.onclick = async () => {
      if (!confirm('Xóa buổi học này?')) return;
      try { await api('DELETE', '/api/tkb/' + b.dataset.x); toast('Đã xóa buổi học'); tai().catch(handle); } catch (ex) { handle(ex); }
    });
  }
  function formTkb(e) {
    const tiet = S.user.tiet.map(x => ({ v: x.tiet, t: `Tiết ${x.tiet} (${x.tu})` }));
    openForm({ title: e ? 'Sửa buổi học' : 'Thêm buổi học', submit: e ? 'Cập nhật' : 'Tạo',
      fields: [
        { name: 'ngayHoc', label: 'Ngày học', type: 'date', required: true, value: e?.ngayHoc || q.date },
        { name: 'tietBatDau', label: 'Tiết bắt đầu', type: 'select', options: tiet, required: true, value: e?.tietBatDau, half: true },
        { name: 'tietKetThuc', label: 'Tiết kết thúc', type: 'select', options: tiet, required: true, value: e?.tietKetThuc, half: true },
        { name: 'maMonHoc', label: 'Môn học', type: 'select', options: S.lists.mon.map(x => ({ v: x.maMonHoc, t: x.tenMonHoc })), required: true, blank: '— Chọn —', value: e?.maMonHoc },
        { name: 'maGiangVien', label: 'Giảng viên', type: 'select', options: S.lists.gv.map(x => ({ v: x.maGiangVien, t: x.hoTen })), required: true, blank: '— Chọn —', value: e?.maGiangVien },
        { name: 'maLop', label: 'Lớp', type: 'select', options: S.lists.lop.map(x => ({ v: x.maLop, t: x.tenLop })), required: true, blank: '— Chọn —', value: e?.maLop, half: true },
        { name: 'maPhong', label: 'Phòng học', type: 'select', options: S.lists.phong.map(x => ({ v: x.maPhong, t: `${x.tenPhong} (${x.sucChua} chỗ)` })), required: true, blank: '— Chọn —', value: e?.maPhong, half: true },
        { name: 'hocKy', label: 'Học kỳ', value: e?.hocKy || 'HK1', half: true }, { name: 'namHoc', label: 'Năm học', value: e?.namHoc || '', half: true }],
      onSubmit: async d => { await api(e ? 'PUT' : 'POST', e ? '/api/tkb/' + e.maTKB : '/api/tkb', d); toast(e ? 'Đã cập nhật' : 'Đã tạo buổi học'); tai().catch(handle); } });
  }
  tai().catch(handle);
}

// ---------------- Danh mục ----------------
const RES = {
  'khoa': { ten: 'Khoa', pk: 'maKhoa', cols: [['tenKhoa', 'Tên khoa']], dep: [], f: () => [{ name: 'tenKhoa', label: 'Tên khoa', required: true }] },
  'lop': { ten: 'Lớp', pk: 'maLop', cols: [['tenLop', 'Tên lớp'], ['khoaHoc', 'Khóa học'], ['tenKhoa', 'Khoa']], dep: ['khoa'],
    f: () => [{ name: 'tenLop', label: 'Tên lớp', required: true }, { name: 'khoaHoc', label: 'Khóa học' }, sel('maKhoa', 'Khoa', 'khoa', 'maKhoa', 'tenKhoa')] },
  'mon-hoc': { ten: 'Môn học', pk: 'maMonHoc', cols: [['tenMonHoc', 'Tên môn'], ['soTinChi', 'Số tín chỉ']], dep: [],
    f: () => [{ name: 'tenMonHoc', label: 'Tên môn hoc', required: true }, { name: 'soTinChi', label: 'Số tín chỉ', type: 'number', min: 1, required: true }] },
  'phong-hoc': { ten: 'Phòng học', pk: 'maPhong', cols: [['tenPhong', 'Ten phong'], ['sucChua', 'Sức chứa']], dep: [],
    f: () => [{ name: 'tenPhong', label: 'Ten phong', required: true }, { name: 'sucChua', label: 'Sức chứa', type: 'number', min: 1, required: true }] },
  'giang-vien': { ten: 'Giảng viên', pk: 'maGiangVien', cols: [['hoTen', 'Họ tên'], ['email', 'Email'], ['soDienThoai', 'Điện thoại'], ['tenKhoa', 'Khoa'], ['tenDangNhap', 'Tài khoản']], dep: ['khoa'],
    f: () => [{ name: 'hoTen', label: 'Họ tên', required: true }, { name: 'email', label: 'Email', type: 'email', half: true }, { name: 'soDienThoai', label: 'Điện thoại', half: true }, sel('maKhoa', 'Khoa', 'khoa', 'maKhoa', 'tenKhoa')], tk: true },
  'sinh-vien': { ten: 'Sinh viên', pk: 'maSinhVien', cols: [['hoTen', 'Họ tên'], ['email', 'Email'], ['soDienThoai', 'Điện thoại'], ['tenLop', 'Lớp'], ['tenDangNhap', 'Tài khoản']], dep: ['lop'],
    f: () => [{ name: 'hoTen', label: 'Họ tên', required: true }, { name: 'email', label: 'Email', type: 'email', half: true }, { name: 'soDienThoai', label: 'Điện thoại', half: true }, sel('maLop', 'Lớp', 'lop', 'maLop', 'tenLop')], tk: true },
};
function sel(name, label, list, v, t) { return { name, label, type: 'select', required: true, blank: '— Chọn —', options: S.lists[list].map(x => ({ v: x[v], t: x[t] })) }; }
async function viewDanhMuc() {
  const key = S.dm, R = RES[key];
  $('#main').innerHTML = `<div class="card"><div class="bar"><label>Danh mục<select id="r">${Object.entries(RES).map(([k, x]) => `<option value="${k}" ${k === key ? 'selected' : ''}>${x.ten}</option>`).join('')}</select></label>
    <label>Tìm kiếm<input id="q" type="search"></label><button class="btn" id="add">+ Them</button></div><div id="kq"></div></div>`;
  $('#r').onchange = e => { S.dm = e.target.value; viewDanhMuc().catch(handle); };
  $('#q').onchange = () => tai().catch(handle);
  $('#add').onclick = () => form();
  async function tai() {
    const ds = await api('GET', `/api/danh-muc/${key}?q=${encodeURIComponent($('#q').value)}`);
    $('#kq').innerHTML = ds.length ? `<div class="tablewrap"><table><thead><tr>${R.cols.map(c => `<th>${c[1]}</th>`).join('')}<th></th></tr></thead><tbody>` +
      ds.map(r => `<tr>${R.cols.map(c => `<td>${esc(r[c[0]] ?? '')}</td>`).join('')}<td class="actions"><button class="btn sec sm" data-e="${r[R.pk]}">Sửa</button><button class="btn danger sm" data-x="${r[R.pk]}">Xóa</button></td></tr>`).join('') + '</tbody></table></div>'
      : '<div class="empty">Chưa có dữ liệu.</div>';
    $('#kq').querySelectorAll('[data-e]').forEach(b => b.onclick = () => form(ds.find(x => x[R.pk] == b.dataset.e)));
    $('#kq').querySelectorAll('[data-x]').forEach(b => b.onclick = async () => {
      if (!confirm('Xóa bản ghi này?')) return;
      try { await api('DELETE', `/api/danh-muc/${key}/${b.dataset.x}`); S.lists = {}; toast('Đã xóa'); tai().catch(handle); } catch (ex) { handle(ex); }
    });
  }
  async function form(r) {
    await lists(...R.dep);
    const fields = R.f().map(f => ({ ...f, value: r ? r[f.name] : '' }));
    if (!r && R.tk) fields.push({ name: 'tenDangNhap', label: 'Tên đăng nhập (tùy chọn, để tạo tài khoản)', half: true }, { name: 'matKhau', label: 'Mật khẩu (≥ 6 ký tự)', type: 'password', half: true });
    openForm({ title: `${r ? 'Sửa' : 'Them'} ${R.ten.toLowerCase()}`, fields, onSubmit: async d => {
      await api(r ? 'PUT' : 'POST', `/api/danh-muc/${key}` + (r ? '/' + r[R.pk] : ''), d); S.lists = {}; toast('Đã lưu'); tai().catch(handle); } });
  }
  tai().catch(handle);
}

// ---------------- Thống kê ----------------

async function viewThongKe() {
  const d = await api('GET', '/api/thong-ke');

  const block = (id, t, rows) => {
    rows = Array.isArray(rows) ? rows : [];

    const max = Math.max(
      1,
      ...rows.map(r => Number(r.soBuoi ?? r.soGiangVien ?? 0))
    );

    return `
      <div class="card bars stats-section" style="padding:0; overflow:hidden;">

        <button
          class="stats-toggle"
          type="button"
          data-stats="${id}"
          aria-expanded="false">

          <span>${t}</span>
          <span class="stats-arrow">▼</span>
        </button>

        <div class="stats-content" id="stats-${id}" hidden>
          ${
            rows.length
              ? rows.map(r => {
                  const n = Number(r.soBuoi ?? r.soGiangVien ?? 0);

                  return `
                    <div class="r">
                      <span>${esc(r.ten)}</span>
                      <span>
                        <div class="b" style="width:${n / max * 100}%"></div>
                      </span>
                      <b>${n}</b>
                    </div>
                  `;
                }).join('')
              : `<p class="muted">Chưa có dữ liệu thống kê.</p>`
          }
        </div>

      </div>
    `;
  };

  $('#main').innerHTML = `
    <div class="card">
      <b>Tổng số buổi học trong hệ thống:</b>
      ${Number(d.tongSoBuoi || 0)}
    </div>
  `
    + block('gv', 'Số buổi theo giảng viên', d.theoGiangVien)
    + block('phong', 'Số buổi theo phòng học', d.theoPhong)
    + block('lop', 'Số buổi theo lớp', d.theoLop)
    + block('khoa', 'Số giảng viên theo khoa', d.theoKhoa)
    + block('mon', 'Số buổi theo môn học', d.theoMonHoc);

  // Su kien mo rong / thu gon tung muc
  document.querySelectorAll('.stats-toggle').forEach(btn => {
    btn.onclick = () => {
      const id = btn.dataset.stats;
      const content = document.getElementById(`stats-${id}`);
      const isOpening = content.hidden;

      content.hidden = !isOpening;
      btn.setAttribute('aria-expanded', String(isOpening));

      btn.querySelector('.stats-arrow').textContent =
        isOpening ? '▲' : '▼';
    };
  });
}


// ---------------- Tài khoản ----------------
async function viewTaiKhoan() {
  const u = S.user;
  $('#main').innerHTML = `<div class="card" style="max-width:460px"><h2 style="margin-top:0;font-size:1.1rem">Tài khoản</h2>
    <dl class="dl"><dt>Tên đăng nhập</dt><dd>${esc(u.tenDangNhap)}</dd><dt>Vai trò</dt><dd>${esc(u.tenVaiTro)}</dd>${u.tenLop ? `<dt>Lớp</dt><dd>${esc(u.tenLop)}</dd>` : ''}</dl>
    <h3 style="font-size:1rem">Đổi mật khẩu</h3><form id="pw" class="form">
      <label>Mật khẩu hiện tại<input type="password" name="matKhauCu" required autocomplete="current-password"></label>
      <label>Mật khẩu mới (≥ 6 ký tự)<input type="password" name="matKhauMoi" required minlength="6" autocomplete="new-password"></label>
      <div id="pe" class="error" hidden></div><button class="btn">Đổi mật khẩu</button></form></div>`;
  $('#pw').onsubmit = async e => { e.preventDefault(); $('#pe').hidden = true;
    try { await api('POST', '/api/doi-mat-khau', Object.fromEntries(new FormData(e.target))); e.target.reset(); toast('Đã đổi mật khẩu'); }
    catch (ex) { $('#pe').textContent = ex.message; $('#pe').hidden = false; } };
}

boot();
