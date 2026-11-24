'use strict';

// ===== CHUYỂN ĐỔI GIAO DIỆN SÁNG / TỐI =====
function getTheme() {
    return localStorage.getItem('theme') || 'dark';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    // Tránh lỗi nếu body chưa được tạo
    if (document.body) {
        document.body.setAttribute('data-theme', theme);
    }

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

/* Giao diện web thuần HTML/CSS/JS, gọi API của Flask.
   Mọi dữ liệu động đều được esc() trước khi chèn vào HTML. */

const $ = (s, r = document) => r.querySelector(s);

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));

const THU = [
    'Thứ 2', 'Thứ 3', 'Thứ 4',
    'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'
];

const GV = 'GIANG_VIEN';
const SV = 'SINH_VIEN';
const PDT = 'PHONG_DAO_TAO';

async function api(method, url, body) {
    const r = await fetch(url, {
        method,
        credentials: 'same-origin',
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined
    });

    let data = null;

    try {
        data = await r.json();
    } catch {
        // Không có nội dung JSON
    }

    if (!r.ok) {
        const e = new Error((data && data.loi) || 'Có lỗi xảy ra');
        e.status = r.status;
        e.goiY = data && data.goiY;
        throw e;
    }

    return data;
}

let toastTimer;

function toast(msg, err) {
    const t = $('#toast');

    t.textContent = msg;
    t.className = 'show' + (err ? ' err' : '');

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {
        t.className = '';
    }, 3200);
}

// ---- Ngày giờ: dùng giờ địa phương, tránh lệch múi giờ ----

const pad = n => String(n).padStart(2, '0');

const iso = d =>
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

const parse = s => {
    const [y, m, d] = s.split('-').map(Number);
    return new Date(y, m - 1, d);
};

const addDays = (d, n) => {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return x;
};

const monday = d => addDays(d, -((d.getDay() + 6) % 7));

const fmt = s => {
    const [y, m, d] = s.split('-');
    return `${d}/${m}/${y}`;
};

const fmtShort = d =>
    `${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;

const thuOf = s =>
    THU[(parse(s).getDay() + 6) % 7];

const S = {
    user: null,
    tab: 'tkb',
    lists: {},

    tkb: {
        mode: 'tuan',
        date: iso(new Date()),
        maLop: '',
        maMonHoc: '',
        q: '',
        dang: innerWidth > 800 ? 'luoi' : 'ds'
    },

    ql: {
        date: iso(new Date()),
        maLop: ''
    },

    dm: 'khoa',
    unread: 0,
    pwPrompted: false,
    tb: { loai: '', chuaDoc: false },
    tbq: { loai: '', trangThai: '', q: '' },
    sv: { q: '', nam: '', lop: '', sap: 'maso|tang', trang: 1, soDong: 25 }
};

// ===== KHỞI ĐỘNG ỨNG DỤNG =====

async function boot() {
    try {
        S.user = await api('GET', '/api/toi');
    } catch {
        S.user = null;
    }

    render();
}

function render() {
    S.user ? shell() : loginView();
}

// ---------------- Đăng nhập ----------------

function loginView() {
    $('#app').innerHTML = `
        <div class="login-page">
            <div class="login-brand">
                <div class="brand-mark">HP</div>

                <div>
                    <span class="eyebrow">TRƯỜNG ĐẠI HỌC HẢI PHÒNG</span>
                    <h1>Hệ thống quản lý<br>thời khóa biểu</h1>
                    <p>Theo dõi lịch học, lịch giảng dạy và thông báo từ Phòng Đào tạo tại một nơi.</p>
                </div>

                <div class="login-note">
                    <span>INF722 · Kỹ nghệ phần mềm</span>
                    <span>Dành cho sinh viên, giảng viên và Phòng Đào tạo</span>
                </div>
            </div>

            <div class="login-panel">
                <button class="theme-toggle login-theme" id="themeToggle" type="button" title="Chuyển đổi giao diện">
                    ${getTheme() === 'dark' ? '🌙' : '☀️'}
                </button>

                <div class="login-heading">
                    <span class="eyebrow">CỔNG THÔNG TIN</span>
                    <h2>Đăng nhập</h2>
                    <p class="muted">Nhập tên đăng nhập và mật khẩu. Hệ thống tự nhận diện vai trò của bạn.</p>
                </div>

                <form id="f" class="form" autocomplete="on">
                    <label>
                        Tên đăng nhập
                        <input name="tenDangNhap" required autofocus autocomplete="username"
                               autocapitalize="none" spellcheck="false" placeholder="Nhập tên đăng nhập">
                    </label>

                    <label>
                        Mật khẩu
                        <span class="pw-wrap">
                            <input name="matKhau" id="matKhau" type="password" required
                                   autocomplete="current-password" placeholder="Nhập mật khẩu">
                            <button type="button" class="pw-toggle" id="pwToggle" aria-label="Hiện mật khẩu" aria-pressed="false">Hiện</button>
                        </span>
                    </label>

                    <div id="err" class="error" role="alert" hidden></div>

                    <button class="btn login-submit">
                        Đăng nhập <span aria-hidden="true">→</span>
                    </button>
                </form>

                <details class="demo-accounts">
                    <summary>Tài khoản mẫu để trải nghiệm</summary>
                    <p>
                        <b>Phòng Đào tạo:</b> tranthiminhanh08092003 / Tranthiminhanh08092003<br>
                        <b>Giảng viên:</b> lehoangnam12051985 / Lehoangnam12051985<br>
                        <b>Sinh viên:</b> nguyenvanan15032004 / Nguyenvanan15032004<br>
                        <small>Tên đăng nhập = họ tên không dấu + ngày sinh; mật khẩu = họ tên không dấu, chỉ viết hoa chữ đầu + ngày sinh (ddmmyyyy).</small>
                    </p>
                </details>

                <p class="login-foot">
                    © Trường Đại học Hải Phòng · Ứng dụng quản lý thời khóa biểu
                </p>
            </div>
        </div>
    `;

    $('#themeToggle').onclick = toggleTheme;

    $('#pwToggle').onclick = () => {
        const i = $('#matKhau');
        const show = i.type === 'password';

        i.type = show ? 'text' : 'password';
        $('#pwToggle').textContent = show ? 'Ẩn' : 'Hiện';
        $('#pwToggle').setAttribute('aria-pressed', String(show));
        $('#pwToggle').setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
    };

    $('#f').onsubmit = async e => {
        e.preventDefault();

        const f = new FormData(e.target);
        const err = $('#err');
        const btn = e.target.querySelector('.login-submit');

        err.hidden = true;
        btn.disabled = true;

        try {
            await api('POST', '/api/dang-nhap', {
                tenDangNhap: String(f.get('tenDangNhap')).trim(),
                matKhau: f.get('matKhau')
            });

            S.lists = {};
            S.tab = 'tkb';
            S.pwPrompted = false;

            await boot();

        } catch (ex) {
            err.textContent = ex.message;
            err.hidden = false;
            btn.disabled = false;
        }
    };
}

// ---------------- Khung chính ----------------

let unreadTimer;

async function refreshUnread() {
    if (!S.user || S.user.vaiTro === PDT) return;

    try {
        const r = await api('GET', '/api/thong-bao/so-chua-doc');

        setUnread(r.soChuaDoc);
    } catch {
        // bỏ qua lỗi tạm thời
    }
}

function setUnread(n) {
    S.unread = n;

    const b = $('#nbadge');

    if (b) {
        b.textContent = n > 99 ? '99+' : n;
        b.hidden = !n;
    }
}

function shell() {
    const u = S.user;

    const tabs = [
        ['tkb', 'Thời khóa biểu']
    ];

    // Chỉ Phòng Đào tạo được sử dụng chức năng quản lý
    if (u.vaiTro === PDT) {
        tabs.push(
            ['quanly', 'Quản lý TKB'],
            ['danhmuc', 'Danh mục'],
            ['thongke', 'Thống kê']
        );
    }

    tabs.push(['thongbao', 'Thông báo']);
    tabs.push(['taikhoan', 'Tài khoản']);

    $('#app').innerHTML = `
        <header class="top">
            <h1>Thời khóa biểu – ĐH Hải Phòng</h1>

            <span class="who">
                ${esc(u.hoTen)} · ${esc(u.tenVaiTro)}
            </span>

            <button
                class="theme-toggle"
                id="themeToggle"
                type="button"
                title="Chuyển đổi giao diện">
                ${getTheme() === 'dark' ? '🌙' : '☀️'}
            </button>

            <button
                class="btn sec sm"
                id="out"
                style="color:#fff;border-color:#fff">
                Đăng xuất
            </button>
        </header>

        <nav class="tabs" aria-label="Chức năng">
            ${tabs.map(([k, t]) => `
                <button data-k="${k}" ${S.tab === k ? 'aria-current="page"' : ''}>
                    ${t}${k === 'thongbao' && u.vaiTro !== PDT
                        ? ` <span class="nbadge" id="nbadge" ${S.unread ? '' : 'hidden'}>${S.unread > 99 ? '99+' : (S.unread || 0)}</span>`
                        : ''}
                </button>
            `).join('')}
        </nav>

        ${u.phaiDoiMatKhau ? `
            <div class="pw-banner" role="alert">
                <span>Bạn đang dùng mật khẩu ban đầu. Hãy đổi mật khẩu để bảo vệ tài khoản.</span>
                <button class="btn sm" id="pwNow">Đổi mật khẩu</button>
            </div>
        ` : ''}

        <main id="main"></main>
    `;

    $('#out').onclick = async () => {
        await api('POST', '/api/dang-xuat');

        S.user = null;
        S.lists = {};
        S.unread = 0;
        clearInterval(unreadTimer);

        render();
    };

    $('#themeToggle').onclick = toggleTheme;

    if ($('#pwNow')) {
        $('#pwNow').onclick = () => moDoiMatKhau();
    }

    document.querySelectorAll('nav.tabs button').forEach(b => {
        b.onclick = () => {
            S.tab = b.dataset.k;
            shell();
        };
    });

    const views = {
        tkb: viewTkb,
        quanly: viewQuanLy,
        danhmuc: viewDanhMuc,
        thongke: viewThongKe,
        thongbao: viewThongBao,
        taikhoan: viewTaiKhoan
    };

    views[S.tab]().catch(handle);

    refreshUnread();

    clearInterval(unreadTimer);
    unreadTimer = setInterval(refreshUnread, 60000);

    // Lần đăng nhập đầu tiên (mật khẩu ban đầu): nhắc đổi mật khẩu ngay
    if (u.phaiDoiMatKhau && !S.pwPrompted) {
        S.pwPrompted = true;
        moDoiMatKhau(true);
    }
}

function moDoiMatKhau(lanDau) {
    openForm({
        title: lanDau ? 'Đổi mật khẩu lần đầu' : 'Đổi mật khẩu',
        submit: 'Đổi mật khẩu',
        fields: [
            { type: 'note', html: lanDau
                ? 'Đây là lần đăng nhập đầu tiên với mật khẩu ban đầu. Nên đổi sang mật khẩu của riêng bạn (từ 6 ký tự).'
                : 'Mật khẩu mới phải từ 6 ký tự và khác mật khẩu hiện tại.' },
            { name: 'matKhauCu', label: 'Mật khẩu hiện tại', type: 'password', required: true, current: true },
            { name: 'matKhauMoi', label: 'Mật khẩu mới', type: 'password', required: true },
            { name: 'matKhauXacNhan', label: 'Nhập lại mật khẩu mới', type: 'password', required: true }
        ],
        onSubmit: async d => {
            if (d.matKhauMoi !== d.matKhauXacNhan) {
                throw new Error('Mật khẩu mới và xác nhận mật khẩu không khớp');
            }

            await api('POST', '/api/doi-mat-khau', d);

            S.user.phaiDoiMatKhau = false;
            toast('Đã đổi mật khẩu');
            shell();
        }
    });
}

function handle(e) {
    if (e.status === 401) {
        S.user = null;
        render();
    } else {
        toast(e.message, true);
    }
}

// ---------------- Tải danh sách dùng chung ----------------

async function lists(...names) {
    const url = {
        lop: '/api/danh-muc/lop',
        mon: '/api/danh-muc/mon-hoc',
        phong: '/api/danh-muc/phong-hoc',
        gv: '/api/danh-muc/giang-vien',
        khoa: '/api/danh-muc/khoa'
    };

    await Promise.all(
        names
            .filter(n => !S.lists[n])
            .map(async n => {
                S.lists[n] = await api('GET', url[n]);
            })
    );
}

const opts = (arr, v, t, sel, blank) =>
    (blank !== undefined ? `<option value="">${esc(blank)}</option>` : '') +
    arr.map(x => `
        <option value="${esc(x[v])}" ${String(sel) === String(x[v]) ? 'selected' : ''}>
            ${esc(typeof t === 'function' ? t(x) : x[t])}
        </option>
    `).join('');

// ---------------- Xem thời khóa biểu ----------------

async function viewTkb() {
    const u = S.user;
    const t = S.tkb;

    await lists('lop', 'mon');

    $('#main').innerHTML = `
        <div class="card">
            <div class="bar">
                <label>
                    Chế độ
                    <select id="mode">
                        <option value="tuan">Theo tuần</option>
                        <option value="ngay">Theo ngày</option>
                    </select>
                </label>

                <label>
                    Ngày
                    <input type="date" id="date" value="${esc(t.date)}">
                </label>

                <button class="btn sec" id="prev" aria-label="Trước">‹</button>
                <button class="btn sec" id="today">Hôm nay</button>
                <button class="btn sec" id="next" aria-label="Sau">›</button>

                ${u.vaiTro === SV ? '' : `
                    <label>
                        Lớp
                        <select id="lop">
                            ${opts(S.lists.lop, 'maLop', 'tenLop', t.maLop, 'Tất cả')}
                        </select>
                    </label>
                `}

                <label>
                    Môn học
                    <select id="mon">
                        ${opts(S.lists.mon, 'maMonHoc', 'tenMonHoc', t.maMonHoc, 'Tất cả')}
                    </select>
                </label>

                <label>
                    Tìm kiếm
                    <input id="q" type="search" placeholder="Môn, giảng viên, lớp, phòng…" value="${esc(t.q)}">
                </label>

                <label>
                    Hiển thị
                    <select id="dang">
                        <option value="luoi">Lưới</option>
                        <option value="ds">Danh sách</option>
                    </select>
                </label>

                ${u.vaiTro === PDT ? '' : `
                    <label>
                        Phạm vi xuất
                        <select id="xp">
                            <option value="tuan">Tuần đang xem</option>
                            <option value="thang">Tháng đang xem</option>
                        </select>
                    </label>

                    <button class="btn sec" id="xpdf" type="button">Xuất PDF</button>
                    <button class="btn sec" id="xxls" type="button">Xuất Excel</button>
                `}
            </div>

            <div id="kq"></div>
        </div>
    `;

    $('#mode').value = t.mode;
    $('#dang').value = t.dang;

    // Xuất thời khóa biểu của chính mình (sinh viên: lớp mình; giảng viên: lịch dạy của mình)
    const xuat = async (dinhDang, nut) => {
        const d = parse(t.date);
        const p = $('#xp').value === 'thang'
            ? `tuNgay=${iso(new Date(d.getFullYear(), d.getMonth(), 1))}&denNgay=${iso(new Date(d.getFullYear(), d.getMonth() + 1, 0))}`
            : `tuan=${t.date}`;

        nut.disabled = true;

        try {
            await taiFile(`/api/tkb/xuat?dinhDang=${dinhDang}&${p}`);
            toast(dinhDang === 'pdf' ? 'Đã xuất file PDF' : 'Đã xuất file Excel');
        } catch (ex) {
            handle(ex);
        } finally {
            nut.disabled = false;
        }
    };

    if ($('#xpdf')) {
        $('#xpdf').onclick = e => xuat('pdf', e.currentTarget);
        $('#xxls').onclick = e => xuat('xlsx', e.currentTarget);
    }

    const reload = () => loadTkb().catch(handle);

    const step = n => {
        t.date = iso(addDays(parse(t.date), n * (t.mode === 'tuan' ? 7 : 1)));
        $('#date').value = t.date;
        reload();
    };

    $('#mode').onchange = e => {
        t.mode = e.target.value;
        reload();
    };

    $('#date').onchange = e => {
        if (e.target.value) {
            t.date = e.target.value;
            reload();
        }
    };

    $('#prev').onclick = () => step(-1);
    $('#next').onclick = () => step(1);

    $('#today').onclick = () => {
        t.date = iso(new Date());
        $('#date').value = t.date;
        reload();
    };

    if ($('#lop')) {
        $('#lop').onchange = e => {
            t.maLop = e.target.value;
            reload();
        };
    }

    $('#mon').onchange = e => {
        t.maMonHoc = e.target.value;
        reload();
    };

    $('#q').onchange = e => {
        t.q = e.target.value.trim();
        reload();
    };

    $('#dang').onchange = e => {
        t.dang = e.target.value;
        reload();
    };

    reload();
}

async function loadTkb() {
    const t = S.tkb;
    const p = new URLSearchParams();

    const tim = !!t.q;

    if (t.q) {
        p.set('q', t.q);
    } else {
        p.set(t.mode === 'tuan' ? 'tuan' : 'ngay', t.date);
    }

    if (t.maLop && S.user.vaiTro !== SV) {
        p.set('maLop', t.maLop);
    }

    if (t.maMonHoc) {
        p.set('maMonHoc', t.maMonHoc);
    }

    const ds = await api('GET', '/api/tkb?' + p);

    const kq = $('#kq');

    if (!kq) return;

    const mon = parse(t.date);
    const thu2 = monday(mon);

    const tieuDe = tim
        ? `Kết quả tìm kiếm “${esc(t.q)}”: ${ds.length} buổi học`
        : t.mode === 'tuan'
            ? `Tuần ${fmtShort(thu2)} – ${fmtShort(addDays(thu2, 6))}/${addDays(thu2, 6).getFullYear()}`
            : `${THU[(mon.getDay() + 6) % 7]}, ${fmt(t.date)}`;

    let body;

    if (!ds.length) {
        body = `
            <div class="empty">
                ${tim
                    ? 'Không tìm thấy buổi học phù hợp.'
                    : 'Không có lịch học trong khoảng thời gian này.'}
            </div>
        `;
    } else if (!tim && t.mode === 'tuan' && t.dang === 'luoi' && !coVaCham(ds)) {
        body = luoiTuan(ds, thu2);
    } else {
        body = danhSachNgày(ds);
    }

    kq.innerHTML = `
        <h2 style="font-size:1.05rem;margin:.2rem 0 .8rem">
            ${tieuDe}
        </h2>
        ${body}
    `;

    kq.querySelectorAll('[data-id]').forEach(b => {
        b.onclick = () => chiTiết(b.dataset.id);
    });
}

function coVaCham(ds) {
    const seen = new Set();

    for (const e of ds) {
        for (let k = e.tietBatDau; k <= e.tietKetThuc; k++) {
            const key = e.ngayHoc + '-' + k;

            if (seen.has(key)) return true;

            seen.add(key);
        }
    }

    return false;
}

function phu(e) {
    const v = S.user.vaiTro;

    return v === GV
        ? `Lớp ${e.tenLop}`
        : v === SV
            ? e.tenGiangVien
            : `${e.tenGiangVien} · ${e.tenLop}`;
}

function moTa(e) {
    return `
        <b>${esc(e.tenMonHoc)}</b>
        Tiết ${e.tietBatDau}–${e.tietKetThuc} · ${esc(e.tenPhong)}
        <br>${esc(phu(e))}
    `;
}

function luoiTuan(ds, thu2) {
    const tiet = S.user.tiet;
    const today = iso(new Date());

    let h = '<div class="week"><div class="h" style="grid-row:1;grid-column:1"></div>';

    for (let i = 0; i < 7; i++) {
        const d = addDays(thu2, i);

        h += `
            <div class="h ${iso(d) === today ? 'today' : ''}"
                style="grid-row:1;grid-column:${i + 2}">
                ${THU[i]}<br>${fmtShort(d)}
            </div>
        `;
    }

    tiet.forEach((x, r) => {
        h += `
            <div class="t" style="grid-row:${r + 2};grid-column:1">
                Tiết ${x.tiet}<br>${x.tu}
            </div>
        `;

        for (let c = 0; c < 7; c++) {
            h += `
                <div class="slot" style="grid-row:${r + 2};grid-column:${c + 2}"></div>
            `;
        }
    });

    for (const e of ds) {
        const wd = (parse(e.ngayHoc).getDay() + 6) % 7;

        h += `
            <button
                class="ev c${e.maMonHoc % 6}"
                data-id="${e.maTKB}"
                style="grid-row:${e.tietBatDau + 1} / span ${e.tietKetThuc - e.tietBatDau + 1};grid-column:${wd + 2}">
                ${moTa(e)}
            </button>
        `;
    }

    return h + '</div>';
}

function danhSachNgày(ds) {
    const today = iso(new Date());
    const by = {};

    ds.forEach(e => {
        (by[e.ngayHoc] ||= []).push(e);
    });

    const tiet = S.user.tiet;

    const gio = e =>
        `${tiet[e.tietBatDau - 1]?.tu ?? ''}–${tiet[e.tietKetThuc - 1]?.den ?? ''}`;

    return Object.keys(by).sort().map(d => `
        <div class="day">
            <h3 class="${d === today ? 'today' : ''}">
                ${thuOf(d)}, ${fmt(d)}${d === today ? ' (hôm nay)' : ''}
            </h3>

            ${by[d].map(e => `
                <button class="item" data-id="${e.maTKB}">
                    <span class="when">
                        Tiết ${e.tietBatDau}–${e.tietKetThuc}<br>
                        ${gio(e)}
                    </span>

                    <span>
                        <b>${esc(e.tenMonHoc)}</b><br>
                        Phòng ${esc(e.tenPhong)} · ${esc(phu(e))}${e.daNghi ? '<br><b class="muted">Đã thông báo nghỉ học</b>' : ''}
                    </span>
                </button>
            `).join('')}
        </div>
    `).join('');
}

async function chiTiết(id) {
    try {
        const e = await api('GET', '/api/tkb/' + id);
        const tiet = S.user.tiet;

        openDlg(`
            <h2>Chi tiết buổi học</h2>

            <dl class="dl">
                <dt>Môn học</dt>
                <dd>${esc(e.tenMonHoc)} (${e.soTinChi} tín chỉ)</dd>

                <dt>Ngày học</dt>
                <dd>${thuOf(e.ngayHoc)}, ${fmt(e.ngayHoc)}</dd>

                <dt>Tiết / giờ học</dt>
                <dd>
                    Tiết ${e.tietBatDau}–${e.tietKetThuc}
                    (${tiet[e.tietBatDau - 1]?.tu ?? ''}–${tiet[e.tietKetThuc - 1]?.den ?? ''})
                </dd>

                <dt>Phòng học</dt>
                <dd>${esc(e.tenPhong)}</dd>

                <dt>Lớp</dt>
                <dd>${esc(e.tenLop)}</dd>

                <dt>Giảng viên</dt>
                <dd>${esc(e.tenGiangVien)}</dd>

                <dt>Học kỳ / năm học</dt>
                <dd>${esc(e.hocKy || '—')} / ${esc(e.namHoc || '—')}</dd>
            </dl>

            <div class="foot">
                <button class="btn" value="x" id="ok">Đóng</button>
            </div>
        `);

        $('#ok').onclick = () => $('#dlg').close();

    } catch (ex) {
        handle(ex);
    }
}

function openDlg(html) {
    const d = $('#dlg');

    d.innerHTML = html;

    if (!d.open) {
        d.showModal();
    }
}

// ---------------- Form dùng chung ----------------

function openForm({ title, fields, submit = 'Lưu', onSubmit }) {
    const input = f => f.type === 'textarea'
        ? `<textarea name="${f.name}" rows="3" ${f.required ? 'required' : ''}>${esc(f.value ?? '')}</textarea>`
        : f.type === 'select'
        ? `
            <select name="${f.name}" ${f.required ? 'required' : ''}>
                ${opts(f.options, 'v', 't', f.value, f.blank)}
            </select>
        `
        : `
            <input
                name="${f.name}"
                type="${f.type || 'text'}"
                value="${esc(f.value ?? '')}"
                ${f.required ? 'required' : ''}
                ${f.min ? `min="${f.min}"` : ''}
                ${f.name === 'ngaySinh' ? `max="${iso(new Date())}"` : ''}
                ${f.type === 'password' ? `autocomplete="${f.current ? 'current-password' : 'new-password'}" ${f.current ? '' : 'minlength="6"'}` : ''}>
        `;

    const rows = [];

    for (let i = 0; i < fields.length; i++) {
        const f = fields[i];
        const nx = fields[i + 1];

        if (f.type === 'note') {
            rows.push(`<p class="form-note">${f.html}</p>`);
            continue;
        }

        if (f.half && nx && nx.half) {
            rows.push(`
                <div class="row">
                    <label>${f.label}${input(f)}</label>
                    <label>${nx.label}${input(nx)}</label>
                </div>
            `);

            i++;
        } else {
            rows.push(`<label>${f.label}${input(f)}</label>`);
        }
    }

    openDlg(`
        <h2>${esc(title)}</h2>

        <form id="mf" class="form" method="dialog">
            ${rows.join('')}

            <div id="mfe" class="error" hidden></div>

            <div class="foot">
                <button type="button" class="btn sec" id="cancel">Hủy</button>
                <button class="btn" id="save">${esc(submit)}</button>
            </div>
        </form>
    `);

    $('#cancel').onclick = () => $('#dlg').close();

    $('#mf').onsubmit = async e => {
        e.preventDefault();

        const data = Object.fromEntries(new FormData(e.target));

        $('#mfe').hidden = true;
        $('#save').disabled = true;

        try {
            await onSubmit(data);
            $('#dlg').close();

        } catch (ex) {
            if (ex.status === 401) return handle(ex);

            $('#mfe').textContent = ex.message;
            $('#mfe').hidden = false;

        } finally {
            const b = $('#save');

            if (b) {
                b.disabled = false;
            }
        }
    };
}

// ---------------- Quản lý thời khóa biểu (Phòng Đào tạo) ----------------

async function viewQuanLy() {
    await lists('lop', 'mon', 'phong', 'gv');

    const q = S.ql;

    $('#main').innerHTML = `
        <div class="card">
            <div class="bar">
                <label>
                    Tuần chứa ngày
                    <input type="date" id="d" value="${esc(q.date)}">
                </label>

                <label>
                    Lớp
                    <select id="l">
                        ${opts(S.lists.lop, 'maLop', 'tenLop', q.maLop, 'Tất cả')}
                    </select>
                </label>

                <button class="btn" id="add">+ Thêm buổi học</button>
                <button class="btn sec" id="impTkb">Nhập từ Excel</button>
            </div>

            <div id="kq"></div>
        </div>
    `;

    $('#d').onchange = e => {
        q.date = e.target.value;
        tai();
    };

    $('#l').onchange = e => {
        q.maLop = e.target.value;
        tai();
    };

    $('#add').onclick = () => formTkb();
    $('#impTkb').onclick = () => moNhapExcel('tkb', 'thời khóa biểu', () => viewQuanLy().catch(handle));

    async function tai() {
        const p = new URLSearchParams({ tuan: q.date });

        if (q.maLop) {
            p.set('maLop', q.maLop);
        }

        const ds = await api('GET', '/api/tkb?' + p);

        $('#kq').innerHTML = ds.length
            ? `
                <div class="tablewrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Ngày</th>
                                <th>Tiết</th>
                                <th>Môn học</th>
                                <th>Giảng viên</th>
                                <th>Lớp</th>
                                <th>Phòng</th>
                                <th></th>
                            </tr>
                        </thead>

                        <tbody>
                            ${ds.map(e => `
                                <tr>
                                    <td>${thuOf(e.ngayHoc)}, ${fmt(e.ngayHoc)}</td>
                                    <td>${e.tietBatDau}–${e.tietKetThuc}</td>
                                    <td>${esc(e.tenMonHoc)}</td>
                                    <td>${esc(e.tenGiangVien)}</td>
                                    <td>${esc(e.tenLop)}</td>
                                    <td>${esc(e.tenPhong)}${e.daNghi ? '<br><small class="muted">Đã thông báo nghỉ</small>' : ''}</td>

                                    <td class="actions">
                                        <button class="btn sec sm" data-e="${e.maTKB}">Sửa</button>
                                        <button class="btn sec sm" data-nghi="${e.maTKB}">Nghỉ</button>
                                        <button class="btn sec sm" data-bu="${e.maTKB}">Dạy bù</button>
                                        <button class="btn sec sm" data-phong="${e.maTKB}">Đổi phòng</button>
                                        <button class="btn danger sm" data-x="${e.maTKB}">Xóa</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `
            : '<div class="empty">Không có buổi học trong tuần này.</div>';

        $('#kq').querySelectorAll('[data-e]').forEach(b => {
            b.onclick = () => formTkb(
                ds.find(x => x.maTKB == b.dataset.e)
            );
        });

        $('#kq').querySelectorAll('[data-nghi]').forEach(b => {
            b.onclick = () => {
                const e = ds.find(x => x.maTKB == b.dataset.nghi);
                openForm({
                    title: 'Thông báo nghỉ buổi học',
                    submit: 'Xác nhận nghỉ',
                    fields: [{ name: 'lyDo', label: 'Lý do nghỉ học', required: true }],
                    onSubmit: async d => {
                        await api('POST', `/api/tkb/${e.maTKB}/nghi-hoc`, d);
                        toast('Đã gửi thông báo nghỉ học cho lớp và giảng viên');
                    }
                });
            };
        });

        $('#kq').querySelectorAll('[data-bu]').forEach(b => {
            b.onclick = () => {
                const e = ds.find(x => x.maTKB == b.dataset.bu);
                openForm({
                    title: 'Sắp xếp buổi dạy bù',
                    submit: 'Tạo lịch và thông báo',
                    fields: [
                        { name: 'ngayHoc', label: 'Ngày dạy bù', type: 'date', required: true, value: q.date },
                        { name: 'tietBatDau', label: 'Tiết bắt đầu', type: 'number', min: 1, required: true, value: e.tietBatDau, half: true },
                        { name: 'tietKetThuc', label: 'Tiết kết thúc', type: 'number', min: 1, required: true, value: e.tietKetThuc, half: true },
                        { name: 'maPhong', label: 'Phòng học', type: 'select', options: S.lists.phong.map(x => ({v:x.maPhong,t:x.tenPhong})), value: e.maPhong, required: true }
                    ],
                    onSubmit: async d => {
                        d.tietBatDau = Number(d.tietBatDau);
                        d.tietKetThuc = Number(d.tietKetThuc);
                        d.maPhong = Number(d.maPhong);
                        await api('POST', `/api/tkb/${e.maTKB}/day-bu`, d);
                        toast('Đã tạo lịch dạy bù và gửi thông báo');
                        tai().catch(handle);
                    }
                });
            };
        });

        $('#kq').querySelectorAll('[data-phong]').forEach(b => {
            b.onclick = () => {
                const e = ds.find(x => x.maTKB == b.dataset.phong);
                openForm({
                    title: 'Thay đổi phòng học',
                    submit: 'Cập nhật và thông báo',
                    fields: [{
                        name: 'maPhong', label: 'Phòng học mới', type: 'select', required: true,
                        options: S.lists.phong.map(x => ({v:x.maPhong,t:x.tenPhong})),
                        value: e.maPhong
                    }],
                    onSubmit: async d => {
                        await api('POST', `/api/tkb/${e.maTKB}/doi-phong`, { maPhong: Number(d.maPhong) });
                        toast('Đã đổi phòng và gửi thông báo');
                        tai().catch(handle);
                    }
                });
            };
        });

        $('#kq').querySelectorAll('[data-x]').forEach(b => {
            b.onclick = async () => {
                if (!confirm('Xóa buổi học này?')) return;

                try {
                    await api('DELETE', '/api/tkb/' + b.dataset.x);

                    toast('Đã xóa buổi học');
                    tai().catch(handle);

                } catch (ex) {
                    handle(ex);
                }
            };
        });
    }

    function formTkb(e) {
        const tiet = S.user.tiet.map(x => ({
            v: x.tiet,
            t: `Tiết ${x.tiet} (${x.tu})`
        }));

        openForm({
            title: e ? 'Sửa buổi học' : 'Thêm buổi học',
            submit: e ? 'Cập nhật' : 'Tạo',

            fields: [
                {
                    name: 'ngayHoc',
                    label: 'Ngày học',
                    type: 'date',
                    required: true,
                    value: e?.ngayHoc || q.date
                },

                {
                    name: 'tietBatDau',
                    label: 'Tiết bắt đầu',
                    type: 'select',
                    options: tiet,
                    required: true,
                    value: e?.tietBatDau,
                    half: true
                },

                {
                    name: 'tietKetThuc',
                    label: 'Tiết kết thúc',
                    type: 'select',
                    options: tiet,
                    required: true,
                    value: e?.tietKetThuc,
                    half: true
                },

                {
                    name: 'maMonHoc',
                    label: 'Môn học',
                    type: 'select',
                    options: S.lists.mon.map(x => ({
                        v: x.maMonHoc,
                        t: x.tenMonHoc
                    })),
                    required: true,
                    blank: '— Chọn —',
                    value: e?.maMonHoc
                },

                {
                    name: 'maGiangVien',
                    label: 'Giảng viên',
                    type: 'select',
                    options: S.lists.gv.map(x => ({
                        v: x.maGiangVien,
                        t: x.hoTen
                    })),
                    required: true,
                    blank: '— Chọn —',
                    value: e?.maGiangVien
                },

                {
                    name: 'maLop',
                    label: 'Lớp',
                    type: 'select',
                    options: S.lists.lop.map(x => ({
                        v: x.maLop,
                        t: x.tenLop
                    })),
                    required: true,
                    blank: '— Chọn —',
                    value: e?.maLop,
                    half: true
                },

                {
                    name: 'maPhong',
                    label: 'Phòng học',
                    type: 'select',
                    options: S.lists.phong.map(x => ({
                        v: x.maPhong,
                        t: `${x.tenPhong} (${x.sucChua} chỗ)`
                    })),
                    required: true,
                    blank: '— Chọn —',
                    value: e?.maPhong,
                    half: true
                },

                {
                    name: 'hocKy',
                    label: 'Học kỳ',
                    value: e?.hocKy || 'HK1',
                    half: true
                },

                {
                    name: 'namHoc',
                    label: 'Năm học',
                    value: e?.namHoc || '',
                    half: true
                }
            ],

            onSubmit: async d => {
                await api(
                    e ? 'PUT' : 'POST',
                    e ? '/api/tkb/' + e.maTKB : '/api/tkb',
                    d
                );

                toast(e ? 'Đã cập nhật' : 'Đã tạo buổi học');

                tai().catch(handle);
            }
        });
    }

    tai().catch(handle);
}

// ---------------- Thông báo ----------------

const LOAI_TB = {
    CHUNG: ['Thông báo chung', 'notice-general'],
    NGHI: ['Nghỉ học', 'notice-leave'],
    DAY_BU: ['Học bù', 'notice-makeup'],
    DOI_PHONG: ['Thay đổi phòng học', 'notice-room'],
    DOI_LICH: ['Thay đổi lịch học', 'notice-schedule'],
    QUAN_TRONG: ['Thông báo quan trọng', 'notice-important']
};

const fmtDT = s => s ? `${s.slice(11, 16)} ${fmt(s.slice(0, 10))}` : '—';

const loaiOptions = (sel, blank) =>
    (blank ? `<option value="">${blank}</option>` : '') +
    Object.entries(LOAI_TB).map(([k, [t]]) =>
        `<option value="${k}" ${sel === k ? 'selected' : ''}>${t}</option>`).join('');

async function viewThongBao() {
    return S.user.vaiTro === PDT ? viewThongBaoPDT() : viewThongBaoNguoiDung();
}

// ----- Sinh viên / giảng viên: chỉ xem thông báo gửi đến mình -----
async function viewThongBaoNguoiDung() {
    const t = S.tb;
    const p = new URLSearchParams();

    if (t.loai) p.set('loai', t.loai);
    if (t.chuaDoc) p.set('chuaDoc', '1');

    const ds = await api('GET', '/api/thong-bao?' + p);
    const tong = ds.length;
    const chuaDoc = ds.filter(n => !n.daDoc).length;

    if (!t.loai && !t.chuaDoc) {
        setUnread(chuaDoc);
    }

    $('#main').innerHTML = `
        <section class="notice-page">
            <div class="notice-heading">
                <div>
                    <h2>Thông báo</h2>
                    <p class="muted">Thông báo từ Phòng Đào tạo gửi đến ${S.user.vaiTro === SV ? 'bạn và lớp của bạn' : 'bạn và các giảng viên'}.</p>
                </div>

                <div class="notice-tools">
                    <span class="notice-count">${tong} thông báo</span>
                    <span class="notice-count unread-count">${chuaDoc} chưa đọc</span>
                    <button class="btn sec sm" id="readAll" ${chuaDoc ? '' : 'disabled'}>Đánh dấu tất cả đã đọc</button>
                </div>
            </div>

            <div class="bar">
                <label>
                    Loại thông báo
                    <select id="fl">${loaiOptions(t.loai, 'Tất cả')}</select>
                </label>

                <label class="check">
                    <input type="checkbox" id="fu" ${t.chuaDoc ? 'checked' : ''}>
                    Chỉ hiện chưa đọc
                </label>
            </div>

            ${ds.length ? `<div class="notice-list">
                ${ds.map(n => {
                    const [label, cls] = LOAI_TB[n.loai] || LOAI_TB.CHUNG;

                    return `
                        <article class="notice-card ${cls} ${n.daDoc ? 'read' : 'unread'}" data-id="${n.maThongBao}" tabindex="0" role="button">
                            <div class="notice-top">
                                <span class="notice-meta">
                                    <span class="notice-tag">${label}</span>
                                    ${n.daDoc ? '' : '<span class="new-tag">Mới</span>'}
                                </span>
                                <time>${fmtDT(n.thoiGianGui || n.ngayTao)}</time>
                            </div>
                            <h3>${esc(n.tieuDe)}</h3>
                            <p class="clamp">${esc(n.noiDung)}</p>
                            <small>${esc(n.nguoiGui)} · Gửi đến: ${esc(n.tenDoiTuong)}</small>
                            ${n.daDoc ? '' : `<button class="btn sec sm mark" data-read="${n.maThongBao}">Đánh dấu đã đọc</button>`}
                        </article>`;
                }).join('')}
            </div>` : `<div class="empty notice-empty">${t.chuaDoc ? 'Bạn đã đọc hết thông báo.' : 'Hiện chưa có thông báo nào dành cho bạn.'}</div>`}
        </section>
    `;

    $('#fl').onchange = e => { t.loai = e.target.value; viewThongBaoNguoiDung().catch(handle); };
    $('#fu').onchange = e => { t.chuaDoc = e.target.checked; viewThongBaoNguoiDung().catch(handle); };

    $('#readAll').onclick = async () => {
        await api('POST', '/api/thong-bao/da-doc-tat-ca');
        setUnread(0);
        toast('Đã đánh dấu tất cả là đã đọc');
        viewThongBaoNguoiDung().catch(handle);
    };

    document.querySelectorAll('[data-read]').forEach(b => {
        b.onclick = async e => {
            e.stopPropagation();

            try {
                const r = await api('POST', `/api/thong-bao/${b.dataset.read}/da-doc`);

                setUnread(r.soChuaDoc);
                viewThongBaoNguoiDung().catch(handle);
            } catch (ex) {
                handle(ex);
            }
        };
    });

    document.querySelectorAll('.notice-card[data-id]').forEach(c => {
        const mo = () => chiTietThongBao(c.dataset.id, ds, () => viewThongBaoNguoiDung().catch(handle));

        c.onclick = mo;
        c.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); mo(); } };
    });
}

function noiDungChiTiet(n, pdt) {
    const [label, cls] = LOAI_TB[n.loai] || LOAI_TB.CHUNG;

    return `
        <div class="notice-top">
            <span class="notice-tag ${cls}">${label}</span>
            ${pdt ? `<span class="status-chip ${n.trangThai === 'DA_GUI' ? 'sent' : 'draft'}">${n.trangThai === 'DA_GUI' ? 'Đã gửi' : 'Bản nháp'}</span>` : ''}
        </div>
        <h2 style="margin-top:.6rem">${esc(n.tieuDe)}</h2>
        <dl class="dl">
            <dt>Mã thông báo</dt><dd>#${n.maThongBao}</dd>
            <dt>Người gửi</dt><dd>${esc(n.nguoiGui)}</dd>
            <dt>Gửi đến</dt><dd>${esc(n.tenDoiTuong)}</dd>
            <dt>Thời gian tạo</dt><dd>${fmtDT(n.ngayTao)}</dd>
            <dt>Thời gian gửi</dt><dd>${n.thoiGianGui ? fmtDT(n.thoiGianGui) : 'Chưa gửi'}</dd>
            ${n.ngayCapNhat ? `<dt>Chỉnh sửa lần cuối</dt><dd>${fmtDT(n.ngayCapNhat)}</dd>` : ''}
        </dl>
        <div class="notice-body">${esc(n.noiDung)}</div>
    `;
}

async function chiTietThongBao(id, ds, lamMoi) {
    try {
        const n = await api('GET', '/api/thong-bao/' + id);

        openDlg(`
            ${noiDungChiTiet(n, false)}
            <div class="foot">
                <button class="btn" id="ok">Đóng</button>
            </div>
        `);

        $('#ok').onclick = () => $('#dlg').close();

        if (!n.daDoc) {
            const r = await api('POST', `/api/thong-bao/${id}/da-doc`);

            setUnread(r.soChuaDoc);
            $('#dlg').addEventListener('close', lamMoi, { once: true });
        }
    } catch (ex) {
        handle(ex);
    }
}

// ----- Phòng Đào tạo: tạo, sửa, xóa, gửi thông báo -----
async function viewThongBaoPDT() {
    const t = S.tbq;
    const p = new URLSearchParams();

    if (t.loai) p.set('loai', t.loai);
    if (t.trangThai) p.set('trangThai', t.trangThai);
    if (t.q) p.set('q', t.q);

    const ds = await api('GET', '/api/thong-bao?' + p);

    $('#main').innerHTML = `
        <section class="notice-page">
            <div class="notice-heading">
                <div>
                    <h2>Quản lý thông báo</h2>
                    <p class="muted">Tạo, sửa, xóa và gửi thông báo đến sinh viên, giảng viên.</p>
                </div>

                <div class="notice-tools">
                    <span class="notice-count">${ds.length} thông báo</span>
                    <button class="btn" id="newTb">+ Tạo thông báo</button>
                </div>
            </div>

            <div class="bar">
                <label>
                    Loại thông báo
                    <select id="fl">${loaiOptions(t.loai, 'Tất cả')}</select>
                </label>

                <label>
                    Trạng thái
                    <select id="ft">
                        <option value="">Tất cả</option>
                        <option value="DA_GUI" ${t.trangThai === 'DA_GUI' ? 'selected' : ''}>Đã gửi</option>
                        <option value="NHAP" ${t.trangThai === 'NHAP' ? 'selected' : ''}>Bản nháp</option>
                    </select>
                </label>

                <label>
                    Tìm kiếm
                    <input id="fq" type="search" placeholder="Tiêu đề, nội dung…" value="${esc(t.q)}">
                </label>
            </div>

            ${ds.length ? `<div class="notice-list">
                ${ds.map(n => {
                    const [label, cls] = LOAI_TB[n.loai] || LOAI_TB.CHUNG;

                    return `
                        <article class="notice-card ${cls}">
                            <div class="notice-top">
                                <span class="notice-meta">
                                    <span class="notice-tag">${label}</span>
                                    <span class="status-chip ${n.trangThai === 'DA_GUI' ? 'sent' : 'draft'}">${n.trangThai === 'DA_GUI' ? 'Đã gửi' : 'Bản nháp'}</span>
                                </span>
                                <time>#${n.maThongBao} · ${n.thoiGianGui ? 'Gửi ' + fmtDT(n.thoiGianGui) : 'Tạo ' + fmtDT(n.ngayTao)}</time>
                            </div>
                            <h3>${esc(n.tieuDe)}</h3>
                            <p class="clamp">${esc(n.noiDung)}</p>
                            <small>${esc(n.nguoiGui)} · Gửi đến: ${esc(n.tenDoiTuong)}</small>
                            <div class="actions notice-actions">
                                <button class="btn sec sm" data-v="${n.maThongBao}">Xem</button>
                                <button class="btn sec sm" data-e="${n.maThongBao}">Sửa</button>
                                ${n.trangThai === 'NHAP' ? `<button class="btn sm" data-g="${n.maThongBao}">Gửi</button>` : ''}
                                <button class="btn danger sm" data-x="${n.maThongBao}">Xóa</button>
                            </div>
                        </article>`;
                }).join('')}
            </div>` : '<div class="empty notice-empty">Chưa có thông báo nào.</div>'}
        </section>
    `;

    const lamMoi = () => viewThongBaoPDT().catch(handle);

    $('#fl').onchange = e => { t.loai = e.target.value; lamMoi(); };
    $('#ft').onchange = e => { t.trangThai = e.target.value; lamMoi(); };
    $('#fq').onchange = e => { t.q = e.target.value.trim(); lamMoi(); };
    $('#newTb').onclick = () => formThongBao(null, lamMoi);

    const tim = id => ds.find(x => x.maThongBao == id);

    document.querySelectorAll('[data-v]').forEach(b => {
        b.onclick = () => {
            openDlg(`${noiDungChiTiet(tim(b.dataset.v), true)}<div class="foot"><button class="btn" id="ok">Đóng</button></div>`);
            $('#ok').onclick = () => $('#dlg').close();
        };
    });

    document.querySelectorAll('[data-e]').forEach(b => {
        b.onclick = () => formThongBao(tim(b.dataset.e), lamMoi);
    });

    document.querySelectorAll('[data-g]').forEach(b => {
        b.onclick = async () => {
            try {
                await api('POST', `/api/thong-bao/${b.dataset.g}/gui`);
                toast('Đã gửi thông báo');
                lamMoi();
            } catch (ex) {
                handle(ex);
            }
        };
    });

    document.querySelectorAll('[data-x]').forEach(b => {
        b.onclick = async () => {
            const n = tim(b.dataset.x);

            if (!confirm(`Xóa thông báo “${n.tieuDe}”?\nNgười nhận sẽ không còn thấy thông báo này.`)) return;

            try {
                await api('DELETE', '/api/thong-bao/' + n.maThongBao);
                toast('Đã xóa thông báo');
                lamMoi();
            } catch (ex) {
                handle(ex);
            }
        };
    });
}

async function formThongBao(n, xong) {
    await lists('lop', 'gv');

    const dt = n ? n.doiTuong : 'TAT_CA_SV';
    const dtOpts = [
        ['TAT_CA_SV', 'Tất cả sinh viên'],
        ['TAT_CA_GV', 'Tất cả giảng viên'],
        ['LOP', 'Một lớp sinh viên'],
        ['GIANG_VIEN', 'Một giảng viên'],
        ['TAT_CA', 'Tất cả (sinh viên và giảng viên)']
    ];
    const khoaDt = ['TAT_CA_SV', 'TAT_CA_GV', 'LOP', 'GIANG_VIEN', 'TAT_CA'].includes(dt) ? dt : 'LOP';
    const daGui = n && n.trangThai === 'DA_GUI';

    openDlg(`
        <h2>${n ? 'Sửa thông báo' : 'Tạo thông báo'}</h2>

        <form id="mf" class="form" method="dialog">
            <label>
                Tiêu đề
                <input name="tieuDe" required maxlength="200" value="${esc(n?.tieuDe || '')}">
            </label>

            <div class="row">
                <label>
                    Loại thông báo
                    <select name="loai">${loaiOptions(n?.loai || 'CHUNG')}</select>
                </label>

                <label>
                    Đối tượng nhận
                    <select name="doiTuong" id="dt">
                        ${dtOpts.map(([v, t]) => `<option value="${v}" ${khoaDt === v ? 'selected' : ''}>${t}</option>`).join('')}
                    </select>
                </label>
            </div>

            <label id="wLop" hidden>
                Lớp nhận thông báo
                <select name="maLop">${opts(S.lists.lop, 'maLop', x => x.tenLop + (x.namTuyenSinh ? ` (khóa ${x.namTuyenSinh})` : ''), n?.maLop, '— Chọn lớp —')}</select>
            </label>

            <label id="wGv" hidden>
                Giảng viên nhận thông báo
                <select name="maGiangVien">${opts(S.lists.gv, 'maGiangVien', 'hoTen', n?.maGiangVien, '— Chọn giảng viên —')}</select>
            </label>

            <label>
                Nội dung
                <textarea name="noiDung" rows="6" required maxlength="5000">${esc(n?.noiDung || '')}</textarea>
            </label>

            ${daGui ? '' : `
                <label>
                    Trạng thái
                    <select name="guiNgay">
                        <option value="true">Gửi ngay</option>
                        <option value="false" ${n ? 'selected' : ''}>Lưu bản nháp (chưa gửi)</option>
                    </select>
                </label>
            `}

            <div id="mfe" class="error" hidden></div>

            <div class="foot">
                <button type="button" class="btn sec" id="cancel">Hủy</button>
                <button class="btn" id="save">${n ? 'Cập nhật' : 'Lưu thông báo'}</button>
            </div>
        </form>
    `);

    const hien = () => {
        const v = $('#dt').value;

        $('#wLop').hidden = v !== 'LOP';
        $('#wGv').hidden = v !== 'GIANG_VIEN';
        $('#wLop select').required = v === 'LOP';
        $('#wGv select').required = v === 'GIANG_VIEN';
    };

    $('#dt').onchange = hien;
    hien();

    $('#cancel').onclick = () => $('#dlg').close();

    $('#mf').onsubmit = async e => {
        e.preventDefault();

        const d = Object.fromEntries(new FormData(e.target));

        if (d.doiTuong !== 'LOP') delete d.maLop;
        if (d.doiTuong !== 'GIANG_VIEN') delete d.maGiangVien;

        $('#mfe').hidden = true;
        $('#save').disabled = true;

        try {
            const luu = await api(n ? 'PUT' : 'POST', '/api/thong-bao' + (n ? '/' + n.maThongBao : ''), d);

            $('#dlg').close();
            toast(luu.trangThai === 'DA_GUI' ? 'Đã lưu và gửi thông báo' : 'Đã lưu bản nháp');
            xong();
        } catch (ex) {
            if (ex.status === 401) return handle(ex);

            $('#mfe').textContent = ex.message;
            $('#mfe').hidden = false;
            $('#save').disabled = false;
        }
    };
}

// ---------------- Danh mục ----------------

const NOTE_TK = 'Mã sinh viên được hệ thống tự cấp theo khóa. Tài khoản đăng nhập được tạo tự động: ' +
    'tên đăng nhập = họ tên không dấu + ngày sinh (ddmmyyyy); mật khẩu ban đầu = họ tên không dấu, không cách, chỉ viết hoa chữ cái đầu + ngày sinh (ddmmyyyy).';
const NOTE_TK_GV = NOTE_TK.replace('Mã sinh viên được hệ thống tự cấp theo khóa. ', '');

const RES = {
    'khoa': {
        ten: 'Khoa / Ngành',
        pk: 'maKhoa',
        cols: [['tenKhoa', 'Tên khoa']],
        dep: [],
        imp: true,
        f: () => [{ name: 'tenKhoa', label: 'Tên khoa', required: true }]
    },

    'lop': {
        ten: 'Lớp',
        pk: 'maLop',
        cols: [
            ['tenLop', 'Tên lớp'],
            ['namTuyenSinh', 'Khóa tuyển sinh'],
            ['khoaHoc', 'Khóa học'],
            ['tenKhoa', 'Khoa']
        ],
        dep: ['khoa'],
        imp: true,
        f: () => [
            { name: 'tenLop', label: 'Tên lớp', required: true },
            { name: 'namTuyenSinh', label: 'Khóa tuyển sinh (năm)', type: 'number', min: 2000, required: true, half: true },
            { name: 'khoaHoc', label: 'Khóa học (ví dụ CNTT K24)', half: true },
            sel('maKhoa', 'Khoa', 'khoa', 'maKhoa', 'tenKhoa')
        ]
    },

    'khoa-tuyen-sinh': {
        ten: 'Khóa tuyển sinh',
        pk: 'namTuyenSinh',
        readonly: true,
        cols: [
            ['tenKhoa', 'Khóa'],
            ['soLop', 'Số lớp'],
            ['soSinhVien', 'Số sinh viên'],
            ['maDaCapDen', 'Mã đã cấp đến'],
            ['conLai', 'Số mã còn có thể cấp']
        ],
        dep: [],
        note: 'Mã sinh viên gồm 4 chữ số: 2 số cuối của năm tuyển sinh + số thứ tự 01–99 trong khóa (ví dụ 2501, 2502…).'
    },

    'mon-hoc': {
        ten: 'Môn học',
        pk: 'maMonHoc',
        cols: [['tenMonHoc', 'Tên môn học'], ['soTinChi', 'Số tín chỉ']],
        dep: [],
        imp: true,
        f: () => [
            { name: 'tenMonHoc', label: 'Tên môn học', required: true },
            { name: 'soTinChi', label: 'Số tín chỉ', type: 'number', min: 1, required: true }
        ]
    },

    'phong-hoc': {
        ten: 'Phòng học',
        pk: 'maPhong',
        cols: [['tenPhong', 'Tên phòng'], ['sucChua', 'Sức chứa']],
        dep: [],
        imp: true,
        f: () => [
            { name: 'tenPhong', label: 'Tên phòng', required: true },
            { name: 'sucChua', label: 'Sức chứa', type: 'number', min: 1, required: true }
        ]
    },

    'giang-vien': {
        ten: 'Giảng viên',
        pk: 'maGiangVien',
        cols: [
            ['hoTen', 'Họ tên'],
            ['ngaySinh', 'Ngày sinh'],
            ['email', 'Email'],
            ['soDienThoai', 'Điện thoại'],
            ['tenKhoa', 'Khoa'],
            ['tenDangNhap', 'Tài khoản']
        ],
        dep: ['khoa'],
        imp: true,
        tk: true,
        f: m => [
            { type: 'note', html: NOTE_TK_GV },
            { name: 'hoTen', label: 'Họ tên', required: true },
            { name: 'ngaySinh', label: 'Ngày sinh', type: 'date', required: !m || !m.coTaiKhoan || !!m.ngaySinh, half: true },
            { name: 'soDienThoai', label: 'Điện thoại', half: true },
            { name: 'email', label: 'Email', type: 'email' },
            sel('maKhoa', 'Khoa', 'khoa', 'maKhoa', 'tenKhoa')
        ]
    },

    'sinh-vien': {
        ten: 'Sinh viên',
        pk: 'maSinhVien',
        cols: [
            ['maSoSinhVien', 'Mã SV'],
            ['hoTen', 'Họ tên'],
            ['ngaySinh', 'Ngày sinh'],
            ['namTuyenSinh', 'Khóa'],
            ['tenLop', 'Lớp'],
            ['email', 'Email'],
            ['soDienThoai', 'Điện thoại'],
            ['tenDangNhap', 'Tài khoản']
        ],
        dep: ['lop'],
        imp: true,
        tk: true
    }
};

function sel(name, label, list, v, t) {
    return {
        name,
        label,
        type: 'select',
        required: true,
        blank: '— Chọn —',
        options: S.lists[list].map(x => ({ v: x[v], t: x[t] }))
    };
}

// Hiển thị một ô của bảng danh mục
function oDanhMuc(key, c, r) {
    const v = r[c[0]];

    if (c[0] === 'ngaySinh') return v ? esc(fmt(v)) : '<span class="muted">Chưa có</span>';
    if (c[0] === 'namTuyenSinh' && key === 'sinh-vien') return v ? esc(v) : '';
    if (c[0] === 'tenDangNhap') return v ? `<code>${esc(v)}</code>` : '<span class="muted">Chưa có</span>';

    return esc(v ?? '');
}

async function taiFile(url) {
    const r = await fetch(url, { credentials: 'same-origin' });

    if (!r.ok) {
        let m = 'Không tải được tệp';

        try { m = (await r.json()).loi || m; } catch { /* không phải JSON */ }

        const e = new Error(m);
        e.status = r.status;
        throw e;
    }

    const blob = await r.blob();
    const cd = r.headers.get('Content-Disposition') || '';
    const ten = (cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i) || [])[1] || 'tep-xuat';
    const a = document.createElement('a');

    a.href = URL.createObjectURL(blob);
    a.download = decodeURIComponent(ten);
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

// ----- Nhập từ Excel (dùng cho danh mục và thời khóa biểu) -----
function moNhapExcel(loai, ten, xong) {
    openDlg(`
        <h2>Nhập ${esc(ten)} từ Excel</h2>

        <div class="form">
            <p class="muted">
                1. Tải file mẫu, điền dữ liệu theo đúng tiêu đề cột.<br>
                2. Chọn file .xlsx (hoặc .csv) rồi bấm Nhập dữ liệu. Dòng lỗi sẽ được bỏ qua và liệt kê bên dưới, dòng hợp lệ vẫn được lưu.
            </p>

            <a class="btn sec sm" href="/api/nhap-excel/${loai}/mau" download>Tải file mẫu (.xlsx)</a>

            <label>
                Chọn file dữ liệu
                <input type="file" id="nxFile" accept=".xlsx,.xlsm,.csv">
            </label>

            <div id="nxKq"></div>

            <div class="foot">
                <button type="button" class="btn sec" id="nxDong">Đóng</button>
                <button type="button" class="btn" id="nxGo">Nhập dữ liệu</button>
            </div>
        </div>
    `);

    $('#nxDong').onclick = () => $('#dlg').close();

    $('#nxGo').onclick = async () => {
        const f = $('#nxFile').files[0];

        if (!f) {
            $('#nxKq').innerHTML = '<div class="error">Vui lòng chọn file.</div>';
            return;
        }

        const fd = new FormData();
        fd.append('file', f);

        $('#nxGo').disabled = true;
        $('#nxKq').innerHTML = '<p class="muted">Đang xử lý…</p>';

        try {
            const r = await fetch(`/api/nhap-excel/${loai}`, { method: 'POST', body: fd, credentials: 'same-origin' });
            const d = await r.json().catch(() => ({}));

            if (r.status === 401) return handle({ status: 401 });
            if (!r.ok) throw new Error(d.loi || 'Không nhập được file');

            S.lists = {};

            $('#nxKq').innerHTML = `
                <div class="${d.thatBai ? 'nx-warn' : 'nx-ok'}">
                    Đã nhập thành công ${d.thanhCong}/${d.tong} dòng${d.thatBai ? `, ${d.thatBai} dòng lỗi` : ''}.
                </div>
                ${d.thatBai ? `<ul class="nx-list">
                    ${d.chiTietLoi.map(x => `<li>Dòng ${x.dong}: ${esc(x.noiDung)}</li>`).join('')}
                </ul>` : ''}
            `;

            if (d.thanhCong) xong();
        } catch (ex) {
            $('#nxKq').innerHTML = `<div class="error">${esc(ex.message)}</div>`;
        } finally {
            $('#nxGo').disabled = false;
        }
    };
}

async function viewDanhMuc() {
    const key = S.dm;
    const R = RES[key];
    const sv = key === 'sinh-vien';
    const f = S.sv;

    await lists('lop', 'khoa');

    const nams = [...new Set(S.lists.lop.map(l => l.namTuyenSinh).filter(Boolean))].sort();
    const lopTheoKhoa = f.nam ? S.lists.lop.filter(l => String(l.namTuyenSinh) === String(f.nam)) : S.lists.lop;

    $('#main').innerHTML = `
        <div class="card">
            <div class="bar">
                <label>
                    Danh mục
                    <select id="r">
                        ${Object.entries(RES).map(([k, x]) => `
                            <option value="${k}" ${k === key ? 'selected' : ''}>${x.ten}</option>
                        `).join('')}
                    </select>
                </label>

                <label>
                    Tìm kiếm
                    <input id="q" type="search" placeholder="${sv ? 'Mã SV, họ tên, email, lớp…' : 'Từ khóa…'}" value="${esc(sv ? f.q : '')}">
                </label>

                ${sv ? `
                    <label>
                        Khóa
                        <select id="fn">
                            <option value="">Tất cả</option>
                            ${nams.map(n => `<option value="${n}" ${String(f.nam) === String(n) ? 'selected' : ''}>Khóa ${n}</option>`).join('')}
                        </select>
                    </label>

                    <label>
                        Lớp
                        <select id="fl">
                            ${opts(lopTheoKhoa, 'maLop', 'tenLop', f.lop, 'Tất cả')}
                        </select>
                    </label>

                    <label>
                        Sắp xếp
                        <select id="fs">
                            <option value="maso|tang" ${f.sap === 'maso|tang' ? 'selected' : ''}>Mã SV tăng dần</option>
                            <option value="maso|giam" ${f.sap === 'maso|giam' ? 'selected' : ''}>Mã SV giảm dần</option>
                            <option value="hoten|tang" ${f.sap === 'hoten|tang' ? 'selected' : ''}>Họ tên A → Z</option>
                            <option value="hoten|giam" ${f.sap === 'hoten|giam' ? 'selected' : ''}>Họ tên Z → A</option>
                        </select>
                    </label>
                ` : ''}

                ${R.readonly ? '' : '<button class="btn" id="add">+ Thêm</button>'}
                ${R.imp ? '<button class="btn sec" id="imp">Nhập từ Excel</button>' : ''}
            </div>

            ${R.note ? `<p class="muted form-note">${esc(R.note)}</p>` : ''}

            <div id="kq"></div>
        </div>
    `;

    $('#r').onchange = e => {
        S.dm = e.target.value;
        viewDanhMuc().catch(handle);
    };

    if (sv) {
        $('#q').onchange = e => { f.q = e.target.value.trim(); f.trang = 1; tai().catch(handle); };
        $('#fn').onchange = e => { f.nam = e.target.value; f.lop = ''; f.trang = 1; viewDanhMuc().catch(handle); };
        $('#fl').onchange = e => { f.lop = e.target.value; f.trang = 1; tai().catch(handle); };
        $('#fs').onchange = e => { f.sap = e.target.value; f.trang = 1; tai().catch(handle); };
    } else {
        $('#q').onchange = () => tai().catch(handle);
    }

    // Sau khi thêm/sửa/xóa: nạp lại danh sách dùng chung (lớp, khoa…) rồi vẽ lại màn hình
    const bam = () => { S.lists = {}; return viewDanhMuc(); };

    if ($('#add')) $('#add').onclick = () => form();
    if ($('#imp')) $('#imp').onclick = () => moNhapExcel(key, R.ten.toLowerCase(), () => {
        S.lists = {};
        viewDanhMuc().catch(handle);
    });

    async function tai() {
        let ds, tong, tongTrang;

        if (sv) {
            const [sap, chieu] = f.sap.split('|');
            const p = new URLSearchParams({ sapXep: sap, thuTu: chieu, trang: f.trang, soDong: f.soDong });

            if (f.q) p.set('q', f.q);
            if (f.nam) p.set('namTuyenSinh', f.nam);
            if (f.lop) p.set('maLop', f.lop);

            const r = await api('GET', '/api/danh-muc/sinh-vien?' + p);

            ds = r.items;
            tong = r.tong;
            tongTrang = r.tongTrang;

            if (f.trang > tongTrang) {
                f.trang = tongTrang;
                return tai();
            }
        } else {
            ds = await api('GET', `/api/danh-muc/${key}?q=${encodeURIComponent($('#q').value)}`);
            tong = ds.length;
        }

        $('#kq').innerHTML = ds.length
            ? `
                <div class="tablewrap">
                    <table>
                        <thead>
                            <tr>
                                ${R.cols.map(c => `<th>${c[1]}</th>`).join('')}
                                ${R.readonly ? '' : '<th></th>'}
                            </tr>
                        </thead>

                        <tbody>
                            ${ds.map(r => `
                                <tr>
                                    ${R.cols.map(c => `<td>${oDanhMuc(key, c, r)}</td>`).join('')}

                                    ${R.readonly ? '' : `
                                        <td class="actions">
                                            ${R.tk && r.ngaySinh ? `<button class="btn sec sm" data-tk="${r[R.pk]}" title="Tạo tài khoản theo quy tắc họ tên + ngày sinh">Cấp TK</button>` : ''}
                                            <button class="btn sec sm" data-e="${r[R.pk]}">Sửa</button>
                                            <button class="btn danger sm" data-x="${r[R.pk]}">Xóa</button>
                                        </td>
                                    `}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>

                ${sv ? `
                    <div class="pager">
                        <span>${tong} sinh viên · Trang ${f.trang}/${tongTrang}</span>

                        <span class="pager-btns">
                            <button class="btn sec sm" id="pp" ${f.trang <= 1 ? 'disabled' : ''}>‹ Trước</button>
                            <button class="btn sec sm" id="pn" ${f.trang >= tongTrang ? 'disabled' : ''}>Sau ›</button>

                            <select id="ps" aria-label="Số dòng mỗi trang">
                                ${[25, 50, 100].map(n => `<option value="${n}" ${f.soDong == n ? 'selected' : ''}>${n} dòng/trang</option>`).join('')}
                            </select>
                        </span>
                    </div>
                ` : ''}
            `
            : '<div class="empty">Không có dữ liệu phù hợp.</div>';

        if (sv && $('#pp')) {
            $('#pp').onclick = () => { f.trang--; tai().catch(handle); };
            $('#pn').onclick = () => { f.trang++; tai().catch(handle); };
            $('#ps').onchange = e => { f.soDong = Number(e.target.value); f.trang = 1; tai().catch(handle); };
        }

        const tim = id => ds.find(x => x[R.pk] == id);

        $('#kq').querySelectorAll('[data-e]').forEach(b => {
            b.onclick = () => form(tim(b.dataset.e));
        });

        $('#kq').querySelectorAll('[data-tk]').forEach(b => {
            b.onclick = async () => {
                const m = tim(b.dataset.tk);
                const coTk = !!m.tenDangNhap;

                if (coTk && !confirm(
                    `${m.hoTen} đang có tài khoản “${m.tenDangNhap}”.\n\nĐổi sang tài khoản theo quy tắc sẽ ĐẶT LẠI mật khẩu về mật khẩu ban đầu và tên đăng nhập cũ không dùng được nữa. Tiếp tục?`
                )) return;

                try {
                    const r = await api('POST', `/api/danh-muc/${key}/${m[R.pk]}/cap-tai-khoan`, coTk ? { xacNhanDoi: true } : {});

                    toast(`Đã cấp tài khoản: ${r.tenDangNhap}`);
                    tai().catch(handle);
                } catch (ex) {
                    if (ex.goiY && confirm(`${ex.message}\n\nDùng tên đăng nhập đề xuất “${ex.goiY.tenDangNhapDeXuat}”?`)) {
                        try {
                            const r = await api('POST', `/api/danh-muc/${key}/${m[R.pk]}/cap-tai-khoan`, { xacNhanDoi: true, chapNhanHauTo: true });

                            toast(`Đã cấp tài khoản: ${r.tenDangNhap}`);
                            tai().catch(handle);
                        } catch (e2) { handle(e2); }
                    } else if (!ex.goiY) {
                        handle(ex);
                    }
                }
            };
        });

        $('#kq').querySelectorAll('[data-x]').forEach(b => {
            b.onclick = async () => {
                const m = tim(b.dataset.x);
                const ten = m.hoTen || m.tenLop || m.tenKhoa || m.tenMonHoc || m.tenPhong;
                const them = R.tk ? '\nTài khoản đăng nhập của người này cũng sẽ bị xóa. Mã sinh viên đã cấp không được cấp lại.' : '';

                if (!confirm(`Xóa “${ten}”?${them}`)) return;

                try {
                    await api('DELETE', `/api/danh-muc/${key}/${m[R.pk]}`);
                    toast('Đã xóa');
                    bam().catch(handle);
                } catch (ex) {
                    handle(ex);
                }
            };
        });
    }

    function form(m) {
        const sua = !!m;
        let fields;

        if (sv) {
            const dsLop = sua ? S.lists.lop.filter(l => l.namTuyenSinh === m.namTuyenSinh) : S.lists.lop;

            fields = [
                {
                    type: 'note',
                    html: sua
                        ? `Mã sinh viên <b>${esc(m.maSoSinhVien)}</b> được giữ nguyên khi sửa thông tin. Chỉ chuyển được sang lớp cùng khóa ${esc(m.namTuyenSinh)}.`
                        : NOTE_TK
                },
                { name: 'hoTen', label: 'Họ tên', required: true },
                { name: 'ngaySinh', label: 'Ngày sinh', type: 'date', required: !sua || !!m.ngaySinh, half: true },
                { name: 'soDienThoai', label: 'Điện thoại', half: true },
                { name: 'email', label: 'Email', type: 'email' }
            ];

            if (!sua) {
                fields.push({
                    name: 'namTuyenSinh', label: 'Khóa tuyển sinh', type: 'select', required: true, blank: '— Chọn khóa —',
                    options: nams.map(n => ({ v: n, t: 'Khóa ' + n })), value: f.nam
                });
            }

            fields.push({
                name: 'maLop', label: 'Lớp', type: 'select', required: true, blank: '— Chọn lớp —',
                options: dsLop.filter(l => sua || !f.nam || String(l.namTuyenSinh) === String(f.nam)).map(l => ({ v: l.maLop, t: l.tenLop })),
                value: sua ? m.maLop : f.lop
            });
        } else {
            fields = R.f(m);
        }

        if (sua) {
            fields.forEach(x => { if (x.name && m[x.name] != null && x.value === undefined) x.value = m[x.name]; });
        }

        openForm({
            title: (sua ? 'Sửa ' : 'Thêm ') + R.ten.toLowerCase(),
            fields,
            onSubmit: async d => {
                if (sv) {
                    if (!d.namTuyenSinh) delete d.namTuyenSinh;
                    d.maLop = Number(d.maLop);
                }

                ['maKhoa', 'soTinChi', 'sucChua', 'namTuyenSinh'].forEach(k => {
                    if (d[k] !== undefined && d[k] !== '') d[k] = Number(d[k]);
                });

                const url = `/api/danh-muc/${key}` + (sua ? '/' + m[R.pk] : '');
                let r;

                try {
                    r = await api(sua ? 'PUT' : 'POST', url, d);
                } catch (ex) {
                    // Trùng tên đăng nhập: không ghi đè, hỏi Phòng Đào tạo có dùng hậu tố đề xuất không
                    if (!sua && ex.goiY && confirm(`${ex.message}\n\nDùng tên đăng nhập đề xuất “${ex.goiY.tenDangNhapDeXuat}”?`)) {
                        r = await api('POST', url, { ...d, chapNhanHauTo: true });
                    } else {
                        throw ex;
                    }
                }

                toast(!sua && R.tk
                    ? `Đã thêm${r.maSoSinhVien ? ' · mã ' + r.maSoSinhVien : ''} · tài khoản ${r.tenDangNhap}`
                    : 'Đã lưu');

                bam().catch(handle);
            }
        });
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

    // Sự kiện mở rộng / thu gọn từng mục
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

    $('#main').innerHTML = `
        <div class="card" style="max-width:460px">
            <h2 style="margin-top:0;font-size:1.1rem">Tài khoản</h2>

            <dl class="dl">
                <dt>Họ tên</dt>
                <dd>${esc(u.hoTen)}</dd>

                <dt>Tên đăng nhập</dt>
                <dd>${esc(u.tenDangNhap)}</dd>

                <dt>Vai trò</dt>
                <dd>${esc(u.tenVaiTro)}</dd>

                ${u.maSoSinhVien ? `
                    <dt>Mã sinh viên</dt>
                    <dd>${esc(u.maSoSinhVien)}</dd>
                ` : ''}

                ${u.tenLop ? `
                    <dt>Lớp</dt>
                    <dd>${esc(u.tenLop)}</dd>
                ` : ''}
            </dl>

            <h3 style="font-size:1rem">Đổi mật khẩu</h3>

            <form id="pw" class="form">
                <label>
                    Mật khẩu hiện tại
                    <input type="password" name="matKhauCu" required autocomplete="current-password">
                </label>

                <label>
                    Mật khẩu mới (≥ 6 ký tự)
                    <input type="password" name="matKhauMoi" required minlength="6" autocomplete="new-password">
                </label>

                <label>
                    Nhập lại mật khẩu mới
                    <input type="password" name="matKhauXacNhan" required minlength="6" autocomplete="new-password">
                </label>

                <div id="pe" class="error" hidden></div>

                <button class="btn">Đổi mật khẩu</button>
            </form>
        </div>
    `;

    $('#pw').onsubmit = async e => {
        e.preventDefault();

        $('#pe').hidden = true;

        const d = Object.fromEntries(new FormData(e.target));

        try {
            if (d.matKhauMoi !== d.matKhauXacNhan) {
                throw new Error('Mật khẩu mới và xác nhận mật khẩu không khớp');
            }

            await api('POST', '/api/doi-mat-khau', d);

            e.target.reset();
            toast('Đã đổi mật khẩu');

            if (S.user.phaiDoiMatKhau) {
                S.user.phaiDoiMatKhau = false;
                shell();
            }
        } catch (ex) {
            if (ex.status === 401) return handle(ex);

            $('#pe').textContent = ex.message;
            $('#pe').hidden = false;
        }
    };
}

// ===== KHỞI CHẠY =====

boot();