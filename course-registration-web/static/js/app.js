const state = {
    user: null,
    view: null,
    selectedCourseId: null,
    studentSections: [],
    accountEdit: null,
    courseEdit: null,
    sectionEdit: null,
    adminCourses: [],
    adminSections: [],
};

const navItems = {
    student: [
        ["student-courses", "Học phần"],
        ["student-registered", "Đã đăng ký"],
        ["student-profile", "Hồ sơ cá nhân"],
        ["change-password", "Đổi mật khẩu"],
    ],
    admin: [
        ["admin-dashboard", "Tổng quan"],
        ["admin-accounts", "Tài khoản"],
        ["admin-courses", "Học phần"],
        ["admin-sections", "Lớp học phần"],
        ["admin-enrollments", "Đăng ký & học phí"],
        ["change-password", "Đổi mật khẩu"],
    ],
};

const viewTitles = {
    "student-courses": "Danh sách học phần",
    "student-registered": "Học phần đã đăng ký",
    "student-profile": "Hồ sơ cá nhân",
    "admin-dashboard": "Tổng quan quản trị",
    "admin-accounts": "Quản lý tài khoản",
    "admin-courses": "Quản lý học phần",
    "admin-sections": "Quản lý lớp học phần",
    "admin-enrollments": "Quản lý đăng ký và học phí",
    "change-password": "Đổi mật khẩu",
};

const statusText = {
    open: "Mở đăng ký",
    closed: "Khóa đăng ký",
    cancelled: "Đã hủy",
    registered: "Đang đăng ký",
};

const dayText = {
    2: "Thứ 2",
    3: "Thứ 3",
    4: "Thứ 4",
    5: "Thứ 5",
    6: "Thứ 6",
    7: "Thứ 7",
    8: "Chủ nhật",
};

const root = document.getElementById("view-root");
const authScreen = document.getElementById("auth-screen");
const appShell = document.getElementById("app-shell");
const toast = document.getElementById("toast");

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function currency(value) {
    return new Intl.NumberFormat("vi-VN", {
        style: "currency",
        currency: "VND",
        maximumFractionDigits: 0,
    }).format(Number(value || 0));
}

function dateText(value) {
    if (!value) return "";
    return new Intl.DateTimeFormat("vi-VN").format(new Date(value));
}

function showToast(message, type = "success") {
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => {
        toast.className = "toast";
    }, 3600);
}

async function api(path, options = {}) {
    const response = await fetch(path, {
        method: options.method || "GET",
        headers: { "Content-Type": "application/json" },
        body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const payload = await response.json().catch(() => ({
        ok: false,
        message: "Phản hồi từ máy chủ không hợp lệ.",
    }));
    if (!response.ok || !payload.ok) {
        throw new Error(payload.message || "Có lỗi xảy ra.");
    }
    return payload.data || {};
}

function formData(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function statusBadge(status) {
    return `<span class="status ${escapeHtml(status)}">${statusText[status] || escapeHtml(status)}</span>`;
}

function paymentBadge(isPaid) {
    return `<span class="status ${isPaid ? "paid" : "unpaid"}">${isPaid ? "Đã thu" : "Chưa thu"}</span>`;
}

function setAuthVisible(isAuth) {
    authScreen.classList.toggle("hidden", !isAuth);
    appShell.classList.toggle("hidden", isAuth);
}

function renderNav() {
    const nav = document.getElementById("nav");
    nav.innerHTML = navItems[state.user.role]
        .map(([view, label]) => {
            const active = state.view === view ? "active" : "";
            return `<button class="${active}" type="button" data-action="nav" data-view="${view}">${label}</button>`;
        })
        .join("");
}

function renderShell() {
    document.getElementById("view-title").textContent = viewTitles[state.view] || "Dashboard";
    document.getElementById("role-label").textContent =
        state.user.role === "admin" ? "Quản trị viên" : "Sinh viên";
    document.getElementById("user-chip").textContent =
        state.user.full_name || state.user.email || state.user.username;
    renderNav();
}

async function setView(view) {
    state.view = view;
    renderShell();
    root.innerHTML = `<section class="panel"><p class="muted">Đang tải dữ liệu...</p></section>`;
    try {
        if (view === "student-courses") await renderStudentCourses();
        if (view === "student-registered") await renderStudentRegistered();
        if (view === "student-profile") await renderStudentProfile();
        if (view === "admin-dashboard") await renderAdminDashboard();
        if (view === "admin-accounts") await renderAdminAccounts();
        if (view === "admin-courses") await renderAdminCourses();
        if (view === "admin-sections") await renderAdminSections();
        if (view === "admin-enrollments") await renderAdminEnrollments();
        if (view === "change-password") renderChangePassword();
    } catch (error) {
        root.innerHTML = `<section class="panel"><p>${escapeHtml(error.message)}</p></section>`;
        showToast(error.message, "error");
    }
}

async function bootstrap() {
    try {
        const data = await api("/api/me");
        state.user = data.user;
        setAuthVisible(false);
        await setView(state.user.role === "admin" ? "admin-dashboard" : "student-courses");
    } catch (_error) {
        setAuthVisible(true);
    }
}

function renderChangePassword() {
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div>
                    <h3>Đổi mật khẩu</h3>
                    <p class="muted">Mật khẩu mới cần tối thiểu 6 ký tự.</p>
                </div>
            </div>
            <form class="form-stack" data-form="change-password">
                <div class="grid two">
                    <label><span>Mật khẩu hiện tại</span><input name="current_password" type="password" required></label>
                    <label><span>Mật khẩu mới</span><input name="new_password" type="password" minlength="6" required></label>
                </div>
                <div class="actions"><button class="primary-button" type="submit">Lưu mật khẩu</button></div>
            </form>
        </section>
    `;
}

async function renderStudentProfile() {
    const { profile } = await api("/api/student/profile");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div>
                    <h3>Thông tin sinh viên</h3>
                    <p class="muted">Mã sinh viên và email @ut.edu.vn được khóa theo yêu cầu.</p>
                </div>
            </div>
            <form class="form-stack" data-form="student-profile">
                <div class="grid three">
                    <label><span>Mã sinh viên</span><input value="${escapeHtml(profile.student_code)}" disabled></label>
                    <label><span>Email</span><input value="${escapeHtml(profile.email)}" disabled></label>
                    <label><span>Username</span><input value="${escapeHtml(profile.username)}" disabled></label>
                </div>
                <div class="grid two">
                    <label><span>Họ tên</span><input name="full_name" value="${escapeHtml(profile.full_name)}" required></label>
                    <label><span>Số điện thoại</span><input name="phone" value="${escapeHtml(profile.phone)}"></label>
                    <label><span>Giới tính</span>${genderSelect(profile.gender)}</label>
                    <label><span>Ngày sinh</span><input name="date_of_birth" type="date" value="${escapeHtml(profile.date_of_birth)}"></label>
                    <label><span>Ngành</span><input name="major" value="${escapeHtml(profile.major)}"></label>
                    <label><span>Lớp</span><input name="class_name" value="${escapeHtml(profile.class_name)}"></label>
                </div>
                <div class="actions"><button class="primary-button" type="submit">Cập nhật hồ sơ</button></div>
            </form>
        </section>
    `;
}

function genderSelect(value) {
    return `
        <select name="gender">
            <option value="male" ${value === "male" ? "selected" : ""}>Nam</option>
            <option value="female" ${value === "female" ? "selected" : ""}>Nữ</option>
            <option value="other" ${value === "other" ? "selected" : ""}>Khác</option>
        </select>
    `;
}

async function renderStudentCourses() {
    const { courses } = await api("/api/student/courses");
    const rows = courses.map((course) => `
        <tr>
            <td>${escapeHtml(course.course_code)}</td>
            <td><strong>${escapeHtml(course.course_name)}</strong><br><span class="muted">${escapeHtml(course.description)}</span></td>
            <td>${course.credits}</td>
            <td>${currency(course.tuition_per_credit)}/TC</td>
            <td>${escapeHtml(course.prerequisites || "Không")}</td>
            <td><button class="table-button" type="button" data-action="load-sections" data-course-id="${course.id}">Xem lớp</button></td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div>
                    <h3>Học phần mở đăng ký</h3>
                    <p class="muted">Chọn một học phần để xem các lớp học phần, lịch học và trạng thái còn chỗ.</p>
                </div>
            </div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Mã HP</th><th>Tên học phần</th><th>Tín chỉ</th><th>Học phí</th><th>Tiên quyết</th><th></th></tr></thead>
                    <tbody>${rows || `<tr><td colspan="6">Chưa có học phần.</td></tr>`}</tbody>
                </table>
            </div>
        </section>
        <section id="student-sections"></section>
    `;
    if (state.selectedCourseId) {
        await loadStudentSections(state.selectedCourseId);
    }
}

async function loadStudentSections(courseId) {
    state.selectedCourseId = courseId;
    const { sections } = await api(`/api/student/courses/${courseId}/sections`);
    state.studentSections = sections;
    const rows = sections.map((section) => `
        <tr>
            <td>${escapeHtml(section.section_code)}</td>
            <td>${escapeHtml(section.expected_class_code)}</td>
            <td>${section.credits}</td>
            <td>${section.enrolled_count}/${section.max_capacity}</td>
            <td>${dayText[section.day_of_week]}, tiết ${section.start_period}-${section.end_period}<br><span class="muted">${escapeHtml(section.building)} ${escapeHtml(section.room)}</span></td>
            <td>${statusBadge(section.status)}</td>
            <td>
                <div class="actions">
                    <button class="table-button" type="button" data-action="section-detail" data-section-id="${section.id}">Chi tiết</button>
                    <button class="primary-button" type="button" data-action="register-section" data-section-id="${section.id}">Đăng ký</button>
                </div>
            </td>
        </tr>
    `).join("");
    document.getElementById("student-sections").innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div>
                    <h3>Lớp học phần</h3>
                    <p class="muted">Hệ thống sẽ kiểm tra trạng thái lớp, tiên quyết, trùng lịch và sức chứa trước khi lưu đăng ký.</p>
                </div>
            </div>
            <div id="section-detail" class="summary-bar"></div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Mã lớp</th><th>Lớp dự kiến</th><th>TC</th><th>Sĩ số</th><th>Lịch học</th><th>Trạng thái</th><th></th></tr></thead>
                    <tbody>${rows || `<tr><td colspan="7">Học phần này chưa có lớp.</td></tr>`}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function showSectionDetail(sectionId) {
    const { section } = await api(`/api/student/sections/${sectionId}`);
    document.getElementById("section-detail").innerHTML = `
        <span>${escapeHtml(section.course_code)} - ${escapeHtml(section.course_name)}</span>
        <span>${dayText[section.day_of_week]}, tiết ${section.start_period}-${section.end_period}</span>
        <span>Phòng ${escapeHtml(section.building)} ${escapeHtml(section.room)}</span>
        <span>Còn ${section.available_seats} chỗ</span>
        <span>Tiên quyết: ${escapeHtml(section.prerequisites || "Không")}</span>
    `;
}

async function renderStudentRegistered() {
    const data = await api("/api/student/registered");
    const rows = data.items.map((item, index) => `
        <tr>
            <td>${index + 1}</td>
            <td><strong>${escapeHtml(item.course_code)}</strong><br>${escapeHtml(item.course_name)}</td>
            <td>${escapeHtml(item.section_code)}<br><span class="muted">${escapeHtml(item.expected_class_code)}</span></td>
            <td>${item.credits}</td>
            <td>${dayText[item.day_of_week]}, tiết ${item.start_period}-${item.end_period}</td>
            <td>${dateText(item.registered_at)}</td>
            <td>${currency(item.tuition_fee)}<br><span class="muted">Hạn: ${dateText(item.payment_deadline)}</span></td>
            <td>${paymentBadge(item.is_paid)}</td>
            <td><button class="danger-button" type="button" data-action="cancel-registration" data-enrollment-id="${item.enrollment_id}">Hủy</button></td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="summary-bar">
            <span>Tổng tín chỉ: ${data.total_credits}</span>
            <span>Tổng học phí: ${currency(data.total_tuition)}</span>
            <span>Còn phải thu: ${currency(data.unpaid_total)}</span>
        </section>
        <section class="panel">
            <div class="panel-header">
                <div>
                    <h3>Học phần đã đăng ký</h3>
                    <p class="muted">Hủy đăng ký sẽ giải phóng một chỗ trong lớp học phần.</p>
                </div>
            </div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>STT</th><th>Học phần</th><th>Lớp</th><th>TC</th><th>Lịch</th><th>Ngày ĐK</th><th>Học phí</th><th>Thu phí</th><th></th></tr></thead>
                    <tbody>${rows || `<tr><td colspan="9">Bạn chưa đăng ký học phần nào.</td></tr>`}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function renderAdminDashboard() {
    const { stats, sections } = await api("/api/admin/dashboard");
    const statCards = [
        ["Tài khoản hoạt động", stats.active_accounts],
        ["Học phần", stats.active_courses],
        ["Lớp đang mở", stats.open_sections],
        ["Đăng ký hiện tại", stats.active_enrollments],
        ["Chưa thu", currency(stats.unpaid_total)],
    ].map(([label, value]) => `<div class="stat"><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");
    const rows = sections.map((section) => `
        <tr>
            <td>${escapeHtml(section.section_code)}</td>
            <td>${escapeHtml(section.course_code)} - ${escapeHtml(section.course_name)}</td>
            <td>${section.enrolled_count}/${section.max_capacity}</td>
            <td>${statusBadge(section.status)}</td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="stat-grid">${statCards}</section>
        <section class="panel">
            <div class="panel-header"><div><h3>Lớp gần đầy</h3><p class="muted">Theo dõi sĩ số để điều chỉnh sức chứa khi cần.</p></div></div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Mã lớp</th><th>Học phần</th><th>Sĩ số</th><th>Trạng thái</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function renderAdminAccounts() {
    const { accounts } = await api("/api/admin/accounts");
    const edit = state.accountEdit;
    const rows = accounts.map((account) => `
        <tr>
            <td>${account.id}</td>
            <td>${escapeHtml(account.username)}<br><span class="muted">${escapeHtml(account.email)}</span></td>
            <td>${account.role === "admin" ? "Admin" : "Sinh viên"}</td>
            <td>${escapeHtml(account.student_code || "")}<br><span class="muted">${escapeHtml(account.full_name || "")}</span></td>
            <td>${account.is_active ? statusBadge("open").replace("Mở đăng ký", "Hoạt động") : statusBadge("cancelled").replace("Đã hủy", "Vô hiệu")}</td>
            <td>
                <div class="actions">
                    <button class="table-button" type="button" data-action="edit-account" data-id="${account.id}">Sửa</button>
                    <button class="danger-button" type="button" data-action="disable-account" data-id="${account.id}">Vô hiệu</button>
                </div>
            </td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div><h3>${edit ? "Cập nhật tài khoản" : "Tạo tài khoản"}</h3><p class="muted">Email sinh viên có thể tự tạo theo quy tắc trong báo cáo nếu để trống.</p></div>
                ${edit ? `<button class="ghost-button" type="button" data-action="clear-account-edit">Tạo mới</button>` : ""}
            </div>
            <form class="form-stack" data-form="account">
                <input type="hidden" name="id" value="${edit ? edit.id : ""}">
                <div class="grid four">
                    ${edit ? `<label><span>Vai trò</span><input value="${edit.role}" disabled></label>` : `<label><span>Vai trò</span><select name="role"><option value="student">Sinh viên</option><option value="admin">Admin</option></select></label>`}
                    <label><span>Username</span><input name="username" value="${escapeHtml(edit?.username || "")}" placeholder="2251120003 hoặc admin2" required></label>
                    <label><span>Email</span><input name="email" type="email" value="${escapeHtml(edit?.email || "")}" placeholder="Để trống khi tạo sinh viên"></label>
                    <label><span>Mật khẩu</span><input name="password" type="password" placeholder="${edit ? "Để trống nếu không đổi" : "Mặc định student123"}"></label>
                </div>
                <div class="grid four">
                    <label><span>Mã SV</span><input name="student_code" value="${escapeHtml(edit?.student_code || "")}" ${edit ? "disabled" : ""}></label>
                    <label><span>Họ tên</span><input name="full_name" value="${escapeHtml(edit?.full_name || "")}"></label>
                    <label><span>SĐT</span><input name="phone" value="${escapeHtml(edit?.phone || "")}"></label>
                    <label><span>Hoạt động</span><select name="is_active"><option value="1" ${!edit || edit.is_active ? "selected" : ""}>Có</option><option value="0" ${edit && !edit.is_active ? "selected" : ""}>Không</option></select></label>
                    <label><span>Giới tính</span>${genderSelect(edit?.gender || "other")}</label>
                    <label><span>Ngày sinh</span><input name="date_of_birth" type="date" value="${escapeHtml(edit?.date_of_birth || "")}"></label>
                    <label><span>Ngành</span><input name="major" value="${escapeHtml(edit?.major || "")}"></label>
                    <label><span>Lớp</span><input name="class_name" value="${escapeHtml(edit?.class_name || "")}"></label>
                </div>
                <div class="actions"><button class="primary-button" type="submit">${edit ? "Lưu tài khoản" : "Tạo tài khoản"}</button></div>
            </form>
        </section>
        <section class="panel">
            <div class="table-wrap">
                <table>
                    <thead><tr><th>ID</th><th>Tài khoản</th><th>Vai trò</th><th>Sinh viên</th><th>Trạng thái</th><th></th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
    state.accounts = accounts;
}

async function renderAdminCourses() {
    const { courses } = await api("/api/admin/courses");
    state.adminCourses = courses;
    const edit = state.courseEdit;
    const selected = String(edit?.prerequisite_ids || "").split(",").filter(Boolean);
    const checks = courses.map((course) => `
        <label><input type="checkbox" name="prerequisite_ids" value="${course.id}" ${selected.includes(String(course.id)) ? "checked" : ""}> ${escapeHtml(course.course_code)}</label>
    `).join("");
    const rows = courses.map((course) => `
        <tr>
            <td>${escapeHtml(course.course_code)}</td>
            <td><strong>${escapeHtml(course.course_name)}</strong><br><span class="muted">${escapeHtml(course.description)}</span></td>
            <td>${course.credits}</td>
            <td>${currency(course.tuition_per_credit)}</td>
            <td>${escapeHtml(course.prerequisites || "Không")}</td>
            <td>${course.is_active ? "Có" : "Không"}</td>
            <td>
                <div class="actions">
                    <button class="table-button" type="button" data-action="edit-course" data-id="${course.id}">Sửa</button>
                    <button class="danger-button" type="button" data-action="delete-course" data-id="${course.id}">Ẩn</button>
                </div>
            </td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div><h3>${edit ? "Cập nhật học phần" : "Tạo học phần"}</h3><p class="muted">Thiết lập số tín chỉ, học phí mỗi tín chỉ và học phần tiên quyết.</p></div>
                ${edit ? `<button class="ghost-button" type="button" data-action="clear-course-edit">Tạo mới</button>` : ""}
            </div>
            <form class="form-stack" data-form="course">
                <input type="hidden" name="id" value="${edit ? edit.id : ""}">
                <div class="grid four">
                    <label><span>Mã HP</span><input name="course_code" value="${escapeHtml(edit?.course_code || "")}" required></label>
                    <label><span>Tên học phần</span><input name="course_name" value="${escapeHtml(edit?.course_name || "")}" required></label>
                    <label><span>Tín chỉ</span><input name="credits" type="number" min="1" value="${escapeHtml(edit?.credits || 3)}" required></label>
                    <label><span>Học phí / tín chỉ</span><input name="tuition_per_credit" type="number" min="0" value="${escapeHtml(edit?.tuition_per_credit || 0)}" required></label>
                </div>
                <label><span>Mô tả</span><textarea name="description">${escapeHtml(edit?.description || "")}</textarea></label>
                <label><span>Học phần tiên quyết</span><div class="check-grid">${checks || "Chưa có học phần khác."}</div></label>
                <label><span>Đang mở</span><select name="is_active"><option value="1" ${!edit || edit.is_active ? "selected" : ""}>Có</option><option value="0" ${edit && !edit.is_active ? "selected" : ""}>Không</option></select></label>
                <div class="actions"><button class="primary-button" type="submit">${edit ? "Lưu học phần" : "Tạo học phần"}</button></div>
            </form>
        </section>
        <section class="panel">
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Mã HP</th><th>Tên học phần</th><th>TC</th><th>Học phí</th><th>Tiên quyết</th><th>Mở</th><th></th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function renderAdminSections() {
    const [{ courses }, { sections }] = await Promise.all([
        api("/api/admin/courses"),
        api("/api/admin/sections"),
    ]);
    state.adminCourses = courses;
    state.adminSections = sections;
    const edit = state.sectionEdit;
    const courseOptions = courses.map((course) => `
        <option value="${course.id}" ${edit?.course_id === course.id ? "selected" : ""}>${escapeHtml(course.course_code)} - ${escapeHtml(course.course_name)}</option>
    `).join("");
    const rows = sections.map((section) => `
        <tr>
            <td>${escapeHtml(section.section_code)}</td>
            <td>${escapeHtml(section.course_code)} - ${escapeHtml(section.course_name)}</td>
            <td>${escapeHtml(section.expected_class_code)}</td>
            <td>${dayText[section.day_of_week]}, tiết ${section.start_period}-${section.end_period}</td>
            <td>${escapeHtml(section.building)} ${escapeHtml(section.room)}</td>
            <td>${section.enrolled_count}/${section.max_capacity}</td>
            <td>${statusBadge(section.status)}</td>
            <td>
                <div class="actions">
                    <button class="table-button" type="button" data-action="edit-section" data-id="${section.id}">Sửa</button>
                    <button class="danger-button" type="button" data-action="delete-section" data-id="${section.id}">Hủy lớp</button>
                </div>
            </td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div><h3>${edit ? "Cập nhật lớp học phần" : "Tạo lớp học phần"}</h3><p class="muted">Lịch học dùng để phát hiện trùng lịch khi sinh viên đăng ký.</p></div>
                ${edit ? `<button class="ghost-button" type="button" data-action="clear-section-edit">Tạo mới</button>` : ""}
            </div>
            <form class="form-stack" data-form="section">
                <input type="hidden" name="id" value="${edit ? edit.id : ""}">
                <div class="grid four">
                    <label><span>Học phần</span><select name="course_id">${courseOptions}</select></label>
                    <label><span>Mã lớp</span><input name="section_code" value="${escapeHtml(edit?.section_code || "")}" required></label>
                    <label><span>Lớp dự kiến</span><input name="expected_class_code" value="${escapeHtml(edit?.expected_class_code || "")}" required></label>
                    <label><span>Giảng viên</span><input name="lecturer" value="${escapeHtml(edit?.lecturer || "")}"></label>
                    <label><span>Học kỳ</span><input name="semester" value="${escapeHtml(edit?.semester || "HK1")}" required></label>
                    <label><span>Năm học</span><input name="academic_year" value="${escapeHtml(edit?.academic_year || "2026-2027")}" required></label>
                    <label><span>Thứ</span><select name="day_of_week">${Object.entries(dayText).map(([value, text]) => `<option value="${value}" ${Number(edit?.day_of_week || 2) === Number(value) ? "selected" : ""}>${text}</option>`).join("")}</select></label>
                    <label><span>Trạng thái</span><select name="status"><option value="open" ${edit?.status === "open" ? "selected" : ""}>Mở</option><option value="closed" ${edit?.status === "closed" ? "selected" : ""}>Khóa</option><option value="cancelled" ${edit?.status === "cancelled" ? "selected" : ""}>Hủy</option></select></label>
                    <label><span>Tiết bắt đầu</span><input name="start_period" type="number" min="1" value="${escapeHtml(edit?.start_period || 1)}" required></label>
                    <label><span>Tiết kết thúc</span><input name="end_period" type="number" min="1" value="${escapeHtml(edit?.end_period || 3)}" required></label>
                    <label><span>Tòa</span><input name="building" value="${escapeHtml(edit?.building || "")}"></label>
                    <label><span>Phòng</span><input name="room" value="${escapeHtml(edit?.room || "")}"></label>
                    <label><span>Sức chứa</span><input name="max_capacity" type="number" min="1" value="${escapeHtml(edit?.max_capacity || 35)}" required></label>
                </div>
                <div class="actions"><button class="primary-button" type="submit">${edit ? "Lưu lớp" : "Tạo lớp"}</button></div>
            </form>
        </section>
        <section class="panel">
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Mã lớp</th><th>Học phần</th><th>Lớp dự kiến</th><th>Lịch</th><th>Phòng</th><th>Sĩ số</th><th>Trạng thái</th><th></th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function renderAdminEnrollments() {
    const { enrollments, students, sections } = await api("/api/admin/enrollments");
    const studentOptions = students.map((student) => `<option value="${student.id}">${escapeHtml(student.student_code)} - ${escapeHtml(student.full_name)}</option>`).join("");
    const sectionOptions = sections.map((section) => `<option value="${section.id}">${escapeHtml(section.section_code)} - ${escapeHtml(section.course_code)} (${section.enrolled_count}/${section.max_capacity})</option>`).join("");
    const rows = enrollments.map((item) => `
        <tr data-enrollment-row="${item.id}">
            <td>${item.id}</td>
            <td>${escapeHtml(item.student_code)}<br><span class="muted">${escapeHtml(item.full_name)}</span></td>
            <td>${escapeHtml(item.course_code)} - ${escapeHtml(item.course_name)}<br><span class="muted">${escapeHtml(item.section_code)}</span></td>
            <td>${statusBadge(item.status === "registered" ? "open" : "cancelled").replace("Mở đăng ký", "Đang ĐK")}</td>
            <td><input name="tuition_fee" type="number" min="0" value="${escapeHtml(item.tuition_fee)}"></td>
            <td><input name="payment_deadline" type="date" value="${escapeHtml(item.payment_deadline || "")}"></td>
            <td><select name="is_paid"><option value="0" ${!item.is_paid ? "selected" : ""}>Chưa thu</option><option value="1" ${item.is_paid ? "selected" : ""}>Đã thu</option></select></td>
            <td>
                <div class="actions">
                    <button class="table-button" type="button" data-action="save-tuition" data-id="${item.id}">Lưu phí</button>
                    <button class="danger-button" type="button" data-action="admin-cancel-enrollment" data-id="${item.id}">Hủy ĐK</button>
                </div>
            </td>
        </tr>
    `).join("");
    root.innerHTML = `
        <section class="panel">
            <div class="panel-header">
                <div><h3>Thêm đăng ký thủ công</h3><p class="muted">Quản trị có thể can thiệp đăng ký khi cần xử lý nghiệp vụ.</p></div>
            </div>
            <form class="form-stack" data-form="admin-enrollment">
                <div class="grid three">
                    <label><span>Sinh viên</span><select name="student_id">${studentOptions}</select></label>
                    <label><span>Lớp học phần</span><select name="section_id">${sectionOptions}</select></label>
                    <label><span>Bỏ qua tiên quyết</span><select name="force"><option value="0">Không</option><option value="1">Có</option></select></label>
                </div>
                <div class="actions"><button class="primary-button" type="submit">Thêm đăng ký</button></div>
            </form>
        </section>
        <section class="panel">
            <div class="panel-header"><div><h3>Danh sách đăng ký và học phí</h3><p class="muted">Cập nhật học phí, hạn nộp và trạng thái thu phí.</p></div></div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>ID</th><th>Sinh viên</th><th>Học phần</th><th>Trạng thái</th><th>Học phí</th><th>Hạn nộp</th><th>Thu phí</th><th></th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
}

async function handleSubmit(event) {
    const form = event.target;
    if (form.id === "login-form") {
        event.preventDefault();
        try {
            const data = await api("/api/login", { method: "POST", body: formData(form) });
            state.user = data.user;
            setAuthVisible(false);
            showToast("Đăng nhập thành công.");
            await setView(state.user.role === "admin" ? "admin-dashboard" : "student-courses");
        } catch (error) {
            showToast(error.message, "error");
        }
        return;
    }
    if (form.id === "forgot-form") {
        event.preventDefault();
        try {
            const data = await api("/api/forgot-password", { method: "POST", body: formData(form) });
            document.getElementById("reset-result").textContent = `Mật khẩu tạm thời: ${data.temporary_password}`;
            showToast("Đã tạo mật khẩu tạm thời.");
        } catch (error) {
            showToast(error.message, "error");
        }
        return;
    }
    const kind = form.dataset.form;
    if (!kind) return;
    event.preventDefault();
    try {
        if (kind === "change-password") {
            await api("/api/change-password", { method: "POST", body: formData(form) });
            form.reset();
        }
        if (kind === "student-profile") {
            await api("/api/student/profile", { method: "PUT", body: formData(form) });
            await renderStudentProfile();
        }
        if (kind === "account") {
            const data = formData(form);
            data.is_active = data.is_active === "1";
            const path = data.id ? `/api/admin/accounts/${data.id}` : "/api/admin/accounts";
            const method = data.id ? "PUT" : "POST";
            await api(path, { method, body: data });
            state.accountEdit = null;
            await renderAdminAccounts();
        }
        if (kind === "course") {
            const data = formData(form);
            data.is_active = data.is_active === "1";
            data.prerequisite_ids = [...form.querySelectorAll("input[name='prerequisite_ids']:checked")].map((item) => item.value);
            const path = data.id ? `/api/admin/courses/${data.id}` : "/api/admin/courses";
            const method = data.id ? "PUT" : "POST";
            await api(path, { method, body: data });
            state.courseEdit = null;
            await renderAdminCourses();
        }
        if (kind === "section") {
            const data = formData(form);
            const path = data.id ? `/api/admin/sections/${data.id}` : "/api/admin/sections";
            const method = data.id ? "PUT" : "POST";
            await api(path, { method, body: data });
            state.sectionEdit = null;
            await renderAdminSections();
        }
        if (kind === "admin-enrollment") {
            const data = formData(form);
            data.force = data.force === "1";
            await api("/api/admin/enrollments", { method: "POST", body: data });
            await renderAdminEnrollments();
        }
        showToast("Đã lưu thay đổi.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function handleClick(event) {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    try {
        if (action === "show-forgot") {
            document.getElementById("login-form").classList.add("hidden");
            document.getElementById("forgot-form").classList.remove("hidden");
        }
        if (action === "show-login") {
            document.getElementById("forgot-form").classList.add("hidden");
            document.getElementById("login-form").classList.remove("hidden");
        }
        if (action === "logout") {
            await api("/api/logout", { method: "POST" });
            state.user = null;
            setAuthVisible(true);
        }
        if (action === "nav") {
            await setView(button.dataset.view);
        }
        if (action === "load-sections") {
            await loadStudentSections(button.dataset.courseId);
        }
        if (action === "section-detail") {
            await showSectionDetail(button.dataset.sectionId);
        }
        if (action === "register-section") {
            await api("/api/student/register", {
                method: "POST",
                body: { section_id: button.dataset.sectionId },
            });
            showToast("Đăng ký thành công.");
            await renderStudentRegistered();
            state.view = "student-registered";
            renderShell();
        }
        if (action === "cancel-registration") {
            if (!window.confirm("Hủy đăng ký học phần này?")) return;
            await api("/api/student/cancel", {
                method: "POST",
                body: { enrollment_id: button.dataset.enrollmentId },
            });
            await renderStudentRegistered();
            showToast("Đã hủy đăng ký.");
        }
        if (action === "edit-account") {
            state.accountEdit = state.accounts.find((item) => String(item.id) === button.dataset.id);
            await renderAdminAccounts();
        }
        if (action === "clear-account-edit") {
            state.accountEdit = null;
            await renderAdminAccounts();
        }
        if (action === "disable-account") {
            if (!window.confirm("Vô hiệu hóa tài khoản này?")) return;
            await api(`/api/admin/accounts/${button.dataset.id}`, { method: "DELETE" });
            await renderAdminAccounts();
        }
        if (action === "edit-course") {
            state.courseEdit = state.adminCourses.find((item) => String(item.id) === button.dataset.id);
            await renderAdminCourses();
        }
        if (action === "clear-course-edit") {
            state.courseEdit = null;
            await renderAdminCourses();
        }
        if (action === "delete-course") {
            if (!window.confirm("Ẩn học phần khỏi danh sách đăng ký?")) return;
            await api(`/api/admin/courses/${button.dataset.id}`, { method: "DELETE" });
            await renderAdminCourses();
        }
        if (action === "edit-section") {
            state.sectionEdit = state.adminSections.find((item) => String(item.id) === button.dataset.id);
            await renderAdminSections();
        }
        if (action === "clear-section-edit") {
            state.sectionEdit = null;
            await renderAdminSections();
        }
        if (action === "delete-section") {
            if (!window.confirm("Chuyển lớp học phần sang trạng thái đã hủy?")) return;
            await api(`/api/admin/sections/${button.dataset.id}`, { method: "DELETE" });
            await renderAdminSections();
        }
        if (action === "admin-cancel-enrollment") {
            if (!window.confirm("Hủy đăng ký này?")) return;
            await api(`/api/admin/enrollments/${button.dataset.id}`, { method: "DELETE" });
            await renderAdminEnrollments();
        }
        if (action === "save-tuition") {
            const row = document.querySelector(`[data-enrollment-row="${button.dataset.id}"]`);
            const body = {
                tuition_fee: row.querySelector("[name='tuition_fee']").value,
                payment_deadline: row.querySelector("[name='payment_deadline']").value,
                is_paid: row.querySelector("[name='is_paid']").value === "1",
            };
            await api(`/api/admin/enrollments/${button.dataset.id}/tuition`, {
                method: "PUT",
                body,
            });
            showToast("Đã cập nhật học phí.");
        }
    } catch (error) {
        showToast(error.message, "error");
    }
}

document.addEventListener("submit", handleSubmit);
document.addEventListener("click", handleClick);
document.addEventListener("DOMContentLoaded", bootstrap);
