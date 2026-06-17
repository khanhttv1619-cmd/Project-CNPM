import base64
import hashlib
import hmac
import os
import secrets
import string
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:  # The README explains how to install this dependency.
    mysql = None

    class MySQLError(Exception):
        pass

from flask import Flask, g, jsonify, render_template, request, session


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key-for-production")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
DEFAULT_PAYMENT_DAYS = int(os.getenv("DEFAULT_PAYMENT_DAYS", "30"))
EMAIL_DOMAIN = "@ut.edu.vn"


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"ok": False, "message": error.message}), error.status


@app.errorhandler(MySQLError)
def handle_mysql_error(error):
    return jsonify({"ok": False, "message": f"Loi co so du lieu: {error}"}), 500


def get_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "course_registration"),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
    }


def get_db():
    if mysql is None:
        raise ApiError(
            "Chua cai mysql-connector-python. Hay chay: pip install -r requirements.txt",
            500,
        )
    if "db" not in g:
        g.db = mysql.connector.connect(**get_db_config())
        g.db.autocommit = True
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def cursor():
    return get_db().cursor(dictionary=True)


def fetch_one(sql, params=None):
    cur = cursor()
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    return row


def fetch_all(sql, params=None):
    cur = cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows


def execute(sql, params=None):
    cur = cursor()
    cur.execute(sql, params or ())
    row_id = cur.lastrowid
    cur.close()
    get_db().commit()
    return row_id


def execute_many(sql, values):
    cur = cursor()
    cur.executemany(sql, values)
    cur.close()
    get_db().commit()


def to_json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def clean_row(row):
    return {key: to_json_value(value) for key, value in row.items()}


def clean_rows(rows):
    return [clean_row(row) for row in rows]


def ok(data=None, message="OK"):
    payload = {"ok": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload)


def hash_password(password, iterations=260000):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return (
        f"pbkdf2_sha256${iterations}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def normalize_text(value):
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = "".join(char for char in value.lower() if char.isalnum() or char == " ")
    return " ".join(value.split())


def make_student_email(full_name, student_code):
    parts = normalize_text(full_name).split()
    if not parts or not student_code:
        raise ApiError("Can ho ten va ma sinh vien de tao email sinh vien.")
    first_name = parts[-1]
    surname_initial = parts[0][0] if parts else ""
    middle_initial = parts[1][0] if len(parts) > 2 else ""
    return f"{first_name}{surname_initial}{middle_initial}{student_code[-4:]}{EMAIL_DOMAIN}"


def validate_email_domain(email):
    if not email.lower().endswith(EMAIL_DOMAIN):
        raise ApiError(f"Email bat buoc phai co duoi {EMAIL_DOMAIN}.")


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    row = fetch_one(
        """
        SELECT u.id, u.username, u.email, u.role, u.is_active,
               s.id AS student_id, s.student_code, s.full_name
        FROM users u
        LEFT JOIN students s ON s.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    return clean_row(row) if row else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user["is_active"]:
            raise ApiError("Vui long dang nhap lai.", 401)
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if g.current_user["role"] not in roles:
                raise ApiError("Ban khong co quyen thuc hien chuc nang nay.", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.before_request
def enforce_session_timeout():
    if request.path.startswith("/static") or request.path == "/":
        return
    if request.path in {"/api/login", "/api/forgot-password"}:
        return
    if "user_id" not in session:
        return
    last_seen = session.get("last_seen")
    now = datetime.utcnow()
    if last_seen:
        last_seen_dt = datetime.fromisoformat(last_seen)
        if now - last_seen_dt > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            session.clear()
            raise ApiError("Phien dang nhap da het han sau 15 phut khong hoat dong.", 401)
    session["last_seen"] = now.isoformat()


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    login_id = (data.get("login") or "").strip()
    password = data.get("password") or ""
    if not login_id or not password:
        raise ApiError("Vui long nhap tai khoan va mat khau.")
    user = fetch_one(
        """
        SELECT u.*, s.id AS student_id, s.student_code, s.full_name
        FROM users u
        LEFT JOIN students s ON s.user_id = u.id
        WHERE u.email = %s OR u.username = %s OR s.student_code = %s
        LIMIT 1
        """,
        (login_id, login_id, login_id),
    )
    if not user or not user["is_active"] or not verify_password(password, user["password_hash"]):
        raise ApiError("Thong tin dang nhap khong dung.", 401)
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["last_seen"] = datetime.utcnow().isoformat()
    return ok(
        {
            "user": clean_row(
                {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "student_id": user.get("student_id"),
                    "student_code": user.get("student_code"),
                    "full_name": user.get("full_name"),
                }
            )
        },
        "Dang nhap thanh cong.",
    )


@app.post("/api/logout")
def logout():
    session.clear()
    return ok(message="Da dang xuat.")


@app.get("/api/me")
@login_required
def me():
    return ok({"user": g.current_user})


@app.post("/api/change-password")
@login_required
def change_password():
    data = request.get_json(force=True)
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    if len(new_password) < 6:
        raise ApiError("Mat khau moi phai co it nhat 6 ky tu.")
    row = fetch_one("SELECT password_hash FROM users WHERE id = %s", (g.current_user["id"],))
    if not verify_password(current_password, row["password_hash"]):
        raise ApiError("Mat khau hien tai khong dung.")
    execute(
        "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
        (hash_password(new_password), g.current_user["id"]),
    )
    return ok(message="Da doi mat khau.")


@app.post("/api/forgot-password")
def forgot_password():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    if email:
        validate_email_domain(email)
    user = fetch_one("SELECT id, email, is_active FROM users WHERE email = %s", (email,))
    if not user or not user["is_active"]:
        raise ApiError("Email khong ton tai hoac tai khoan da bi vo hieu hoa.", 404)
    alphabet = string.ascii_letters + string.digits
    temp_password = "".join(secrets.choice(alphabet) for _ in range(10))
    cur = cursor()
    cur.execute(
        "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
        (hash_password(temp_password), user["id"]),
    )
    cur.execute(
        """
        INSERT INTO password_reset_logs (user_id, delivered_to, requested_at)
        VALUES (%s, %s, NOW())
        """,
        (user["id"], user["email"]),
    )
    cur.close()
    get_db().commit()
    return ok(
        {"temporary_password": temp_password},
        "Da tao mat khau tam thoi. Ban demo hien thi mat khau tren man hinh thay cho email.",
    )


def current_student_id():
    student_id = g.current_user.get("student_id")
    if not student_id:
        raise ApiError("Tai khoan hien tai khong phai sinh vien.", 403)
    return student_id


@app.get("/api/student/profile")
@role_required("student")
def student_profile():
    row = fetch_one(
        """
        SELECT s.id, s.student_code, s.full_name, s.phone, s.gender, s.date_of_birth,
               s.major, s.class_name, u.email, u.username
        FROM students s
        JOIN users u ON u.id = s.user_id
        WHERE s.id = %s
        """,
        (current_student_id(),),
    )
    return ok({"profile": clean_row(row)})


@app.put("/api/student/profile")
@role_required("student")
def update_student_profile():
    data = request.get_json(force=True)
    execute(
        """
        UPDATE students
        SET full_name = %s, phone = %s, gender = %s, date_of_birth = %s,
            major = %s, class_name = %s
        WHERE id = %s
        """,
        (
            (data.get("full_name") or "").strip(),
            (data.get("phone") or "").strip(),
            data.get("gender") or "other",
            data.get("date_of_birth") or None,
            (data.get("major") or "").strip(),
            (data.get("class_name") or "").strip(),
            current_student_id(),
        ),
    )
    return ok(message="Da cap nhat thong tin ca nhan.")


@app.get("/api/student/courses")
@role_required("student")
def student_courses():
    rows = fetch_all(
        """
        SELECT c.id, c.course_code, c.course_name, c.credits, c.tuition_per_credit,
               c.description,
               GROUP_CONCAT(p.course_code ORDER BY p.course_code SEPARATOR ', ') AS prerequisites
        FROM courses c
        LEFT JOIN course_prerequisites cp ON cp.course_id = c.id
        LEFT JOIN courses p ON p.id = cp.prerequisite_course_id
        WHERE c.is_active = 1
        GROUP BY c.id
        ORDER BY c.course_code
        """
    )
    return ok({"courses": clean_rows(rows)})


@app.get("/api/student/courses/<int:course_id>/sections")
@role_required("student")
def student_sections(course_id):
    rows = fetch_all(
        """
        SELECT cs.*, c.course_code, c.course_name, c.credits,
               (cs.max_capacity - cs.enrolled_count) AS available_seats
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        WHERE cs.course_id = %s
        ORDER BY cs.section_code
        """,
        (course_id,),
    )
    return ok({"sections": clean_rows(rows)})


@app.get("/api/student/sections/<int:section_id>")
@role_required("student")
def student_section_detail(section_id):
    row = fetch_one(
        """
        SELECT cs.*, c.course_code, c.course_name, c.credits, c.tuition_per_credit,
               GROUP_CONCAT(p.course_code ORDER BY p.course_code SEPARATOR ', ') AS prerequisites,
               (cs.max_capacity - cs.enrolled_count) AS available_seats
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        LEFT JOIN course_prerequisites cp ON cp.course_id = c.id
        LEFT JOIN courses p ON p.id = cp.prerequisite_course_id
        WHERE cs.id = %s
        GROUP BY cs.id
        """,
        (section_id,),
    )
    if not row:
        raise ApiError("Khong tim thay lop hoc phan.", 404)
    return ok({"section": clean_row(row)})


def get_registered_summary(student_id):
    rows = fetch_all(
        """
        SELECT e.id AS enrollment_id, e.registered_at, e.tuition_fee,
               e.payment_deadline, e.is_paid, e.status AS enrollment_status,
               cs.id AS section_id, cs.section_code, cs.expected_class_code,
               cs.semester, cs.academic_year, cs.day_of_week, cs.start_period,
               cs.end_period, cs.building, cs.room, cs.status AS section_status,
               c.course_code, c.course_name, c.credits
        FROM enrollments e
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        WHERE e.student_id = %s AND e.status = 'registered'
        ORDER BY e.registered_at DESC
        """,
        (student_id,),
    )
    total_credits = sum(row["credits"] for row in rows)
    total_tuition = sum(Decimal(row["tuition_fee"]) for row in rows)
    unpaid_total = sum(
        Decimal(row["tuition_fee"]) for row in rows if not row["is_paid"]
    )
    return {
        "items": clean_rows(rows),
        "total_credits": total_credits,
        "total_tuition": float(total_tuition),
        "unpaid_total": float(unpaid_total),
    }


@app.get("/api/student/registered")
@role_required("student")
def student_registered():
    return ok(get_registered_summary(current_student_id()))


def validate_registration(cur, student_id, section_id, force=False):
    cur.execute(
        """
        SELECT cs.*, c.course_code, c.course_name, c.credits, c.tuition_per_credit
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        WHERE cs.id = %s
        FOR UPDATE
        """,
        (section_id,),
    )
    section = cur.fetchone()
    if not section:
        raise ApiError("Khong tim thay lop hoc phan.", 404)
    if section["status"] == "closed":
        raise ApiError("Lop hoc phan dang khoa dang ky.")
    if section["status"] == "cancelled":
        raise ApiError("Lop hoc phan da bi huy.")
    if section["status"] != "open":
        raise ApiError("Lop hoc phan khong o trang thai mo dang ky.")
    if section["enrolled_count"] >= section["max_capacity"]:
        raise ApiError("Class is full.")

    cur.execute(
        """
        SELECT e.id
        FROM enrollments e
        JOIN class_sections cs ON cs.id = e.section_id
        WHERE e.student_id = %s AND e.status = 'registered' AND cs.course_id = %s
        LIMIT 1
        """,
        (student_id, section["course_id"]),
    )
    if cur.fetchone():
        raise ApiError("Sinh vien da dang ky mot lop cua hoc phan nay.")

    if not force:
        cur.execute(
            """
            SELECT p.course_code
            FROM course_prerequisites cp
            JOIN courses p ON p.id = cp.prerequisite_course_id
            LEFT JOIN completed_courses cc
                   ON cc.course_id = cp.prerequisite_course_id
                  AND cc.student_id = %s
            WHERE cp.course_id = %s AND cc.course_id IS NULL
            """,
            (student_id, section["course_id"]),
        )
        missing = [row["course_code"] for row in cur.fetchall()]
        if missing:
            raise ApiError(f"Prerequisite Missing: can hoan thanh {', '.join(missing)}.")

    cur.execute(
        """
        SELECT c.course_code, c.course_name, cs.section_code
        FROM enrollments e
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        WHERE e.student_id = %s
          AND e.status = 'registered'
          AND cs.day_of_week = %s
          AND NOT (%s < cs.start_period OR %s > cs.end_period)
        LIMIT 1
        """,
        (
            student_id,
            section["day_of_week"],
            section["end_period"],
            section["start_period"],
        ),
    )
    conflict = cur.fetchone()
    if conflict:
        raise ApiError(
            "Schedule conflict detected: trung lich voi "
            f"{conflict['course_code']} - {conflict['section_code']}."
        )
    return section


def create_registration(student_id, section_id, force=False):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        section = validate_registration(cur, student_id, section_id, force=force)
        tuition_fee = Decimal(section["credits"]) * Decimal(section["tuition_per_credit"])
        payment_deadline = date.today() + timedelta(days=DEFAULT_PAYMENT_DAYS)
        cur.execute(
            """
            INSERT INTO enrollments
                (student_id, section_id, registered_at, tuition_fee,
                 payment_deadline, is_paid, status)
            VALUES (%s, %s, NOW(), %s, %s, 0, 'registered')
            """,
            (student_id, section_id, tuition_fee, payment_deadline),
        )
        cur.execute(
            """
            UPDATE class_sections
            SET enrolled_count = enrolled_count + 1
            WHERE id = %s
            """,
            (section_id,),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


@app.post("/api/student/register")
@role_required("student")
def register_class():
    data = request.get_json(force=True)
    section_id = int(data.get("section_id") or 0)
    create_registration(current_student_id(), section_id)
    return ok(get_registered_summary(current_student_id()), "Registration successful.")


def cancel_registration_for_student(student_id, enrollment_id, allow_locked=False):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        cur.execute(
            """
            SELECT e.*, cs.status AS section_status
            FROM enrollments e
            JOIN class_sections cs ON cs.id = e.section_id
            WHERE e.id = %s AND e.student_id = %s AND e.status = 'registered'
            FOR UPDATE
            """,
            (enrollment_id, student_id),
        )
        row = cur.fetchone()
        if not row:
            raise ApiError("Khong tim thay dang ky hop le.", 404)
        if not allow_locked and row["section_status"] != "open":
            raise ApiError("Lop da khoa, khong the huy dang ky.")
        cur.execute(
            """
            UPDATE enrollments
            SET status = 'cancelled', cancelled_at = NOW()
            WHERE id = %s
            """,
            (enrollment_id,),
        )
        cur.execute(
            """
            UPDATE class_sections
            SET enrolled_count = GREATEST(enrolled_count - 1, 0)
            WHERE id = %s
            """,
            (row["section_id"],),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


@app.post("/api/student/cancel")
@role_required("student")
def cancel_registration():
    data = request.get_json(force=True)
    enrollment_id = int(data.get("enrollment_id") or 0)
    cancel_registration_for_student(current_student_id(), enrollment_id)
    return ok(get_registered_summary(current_student_id()), "Da huy dang ky.")


@app.get("/api/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM users WHERE is_active = 1) AS active_accounts,
            (SELECT COUNT(*) FROM courses WHERE is_active = 1) AS active_courses,
            (SELECT COUNT(*) FROM class_sections WHERE status = 'open') AS open_sections,
            (SELECT COUNT(*) FROM enrollments WHERE status = 'registered') AS active_enrollments,
            (SELECT COALESCE(SUM(tuition_fee), 0) FROM enrollments
             WHERE status = 'registered' AND is_paid = 0) AS unpaid_total
        """
    )
    sections = fetch_all(
        """
        SELECT cs.id, cs.section_code, c.course_code, c.course_name,
               cs.enrolled_count, cs.max_capacity, cs.status
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        ORDER BY (cs.enrolled_count / GREATEST(cs.max_capacity, 1)) DESC, cs.section_code
        LIMIT 8
        """
    )
    return ok({"stats": clean_row(stats), "sections": clean_rows(sections)})


@app.get("/api/admin/accounts")
@role_required("admin")
def admin_accounts():
    rows = fetch_all(
        """
        SELECT u.id, u.username, u.email, u.role, u.is_active, u.created_at,
               s.id AS student_id, s.student_code, s.full_name, s.phone,
               s.gender, s.date_of_birth, s.major, s.class_name
        FROM users u
        LEFT JOIN students s ON s.user_id = u.id
        ORDER BY u.role, u.id
        """
    )
    return ok({"accounts": clean_rows(rows)})


@app.post("/api/admin/accounts")
@role_required("admin")
def create_account():
    data = request.get_json(force=True)
    role = data.get("role") or "student"
    if role not in {"admin", "student"}:
        raise ApiError("Vai tro khong hop le.")
    full_name = (data.get("full_name") or "").strip()
    student_code = (data.get("student_code") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if role == "student" and not email:
        email = make_student_email(full_name, student_code)
    username = (data.get("username") or student_code or email).strip()
    password = data.get("password") or "student123"
    if not email or not username:
        raise ApiError("Can username va email.")
    validate_email_domain(email)
    if fetch_one("SELECT id FROM users WHERE email = %s OR username = %s", (email, username)):
        raise ApiError("Username hoac email da ton tai.")
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (
                username,
                email,
                hash_password(password),
                role,
                1 if data.get("is_active", True) else 0,
            ),
        )
        user_id = cur.lastrowid
        if role == "student":
            if not student_code or not full_name:
                raise ApiError("Tai khoan sinh vien can ma sinh vien va ho ten.")
            cur.execute(
                """
                INSERT INTO students
                    (user_id, student_code, full_name, phone, gender,
                     date_of_birth, major, class_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    student_code,
                    full_name,
                    (data.get("phone") or "").strip(),
                    data.get("gender") or "other",
                    data.get("date_of_birth") or None,
                    (data.get("major") or "").strip(),
                    (data.get("class_name") or "").strip(),
                ),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
    return ok(message="Da tao tai khoan.")


@app.put("/api/admin/accounts/<int:user_id>")
@role_required("admin")
def update_account(user_id):
    data = request.get_json(force=True)
    user = fetch_one("SELECT role FROM users WHERE id = %s", (user_id,))
    if not user:
        raise ApiError("Khong tim thay tai khoan.", 404)
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    validate_email_domain(email)
    existing = fetch_one(
        "SELECT id FROM users WHERE (email = %s OR username = %s) AND id <> %s",
        (email, username, user_id),
    )
    if existing:
        raise ApiError("Username hoac email da ton tai.")
    fields = [username, email, 1 if data.get("is_active", True) else 0, user_id]
    execute(
        """
        UPDATE users
        SET username = %s, email = %s, is_active = %s, updated_at = NOW()
        WHERE id = %s
        """,
        fields,
    )
    if data.get("password"):
        execute(
            "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
            (hash_password(data["password"]), user_id),
        )
    if user["role"] == "student":
        execute(
            """
            UPDATE students
            SET full_name = %s, phone = %s, gender = %s, date_of_birth = %s,
                major = %s, class_name = %s
            WHERE user_id = %s
            """,
            (
                (data.get("full_name") or "").strip(),
                (data.get("phone") or "").strip(),
                data.get("gender") or "other",
                data.get("date_of_birth") or None,
                (data.get("major") or "").strip(),
                (data.get("class_name") or "").strip(),
                user_id,
            ),
        )
    return ok(message="Da cap nhat tai khoan.")


@app.delete("/api/admin/accounts/<int:user_id>")
@role_required("admin")
def disable_account(user_id):
    if user_id == g.current_user["id"]:
        raise ApiError("Khong the vo hieu hoa tai khoan dang dang nhap.")
    execute("UPDATE users SET is_active = 0, updated_at = NOW() WHERE id = %s", (user_id,))
    return ok(message="Da vo hieu hoa tai khoan.")


def sync_prerequisites(cur, course_id, prerequisite_ids):
    cur.execute("DELETE FROM course_prerequisites WHERE course_id = %s", (course_id,))
    values = [
        (course_id, int(prerequisite_id))
        for prerequisite_id in prerequisite_ids
        if int(prerequisite_id) != course_id
    ]
    if values:
        cur.executemany(
            """
            INSERT INTO course_prerequisites (course_id, prerequisite_course_id)
            VALUES (%s, %s)
            """,
            values,
        )


@app.get("/api/admin/courses")
@role_required("admin")
def admin_courses():
    rows = fetch_all(
        """
        SELECT c.*,
               GROUP_CONCAT(p.id ORDER BY p.course_code SEPARATOR ',') AS prerequisite_ids,
               GROUP_CONCAT(p.course_code ORDER BY p.course_code SEPARATOR ', ') AS prerequisites
        FROM courses c
        LEFT JOIN course_prerequisites cp ON cp.course_id = c.id
        LEFT JOIN courses p ON p.id = cp.prerequisite_course_id
        GROUP BY c.id
        ORDER BY c.course_code
        """
    )
    return ok({"courses": clean_rows(rows)})


@app.post("/api/admin/courses")
@role_required("admin")
def create_course():
    data = request.get_json(force=True)
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        cur.execute(
            """
            INSERT INTO courses
                (course_code, course_name, credits, tuition_per_credit,
                 description, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                (data.get("course_code") or "").strip().upper(),
                (data.get("course_name") or "").strip(),
                int(data.get("credits") or 0),
                Decimal(str(data.get("tuition_per_credit") or 0)),
                (data.get("description") or "").strip(),
                1 if data.get("is_active", True) else 0,
            ),
        )
        course_id = cur.lastrowid
        sync_prerequisites(cur, course_id, data.get("prerequisite_ids") or [])
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
    return ok(message="Da tao hoc phan.")


@app.put("/api/admin/courses/<int:course_id>")
@role_required("admin")
def update_course(course_id):
    data = request.get_json(force=True)
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        cur.execute(
            """
            UPDATE courses
            SET course_code = %s, course_name = %s, credits = %s,
                tuition_per_credit = %s, description = %s, is_active = %s
            WHERE id = %s
            """,
            (
                (data.get("course_code") or "").strip().upper(),
                (data.get("course_name") or "").strip(),
                int(data.get("credits") or 0),
                Decimal(str(data.get("tuition_per_credit") or 0)),
                (data.get("description") or "").strip(),
                1 if data.get("is_active", True) else 0,
                course_id,
            ),
        )
        sync_prerequisites(cur, course_id, data.get("prerequisite_ids") or [])
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
    return ok(message="Da cap nhat hoc phan.")


@app.delete("/api/admin/courses/<int:course_id>")
@role_required("admin")
def delete_course(course_id):
    execute("UPDATE courses SET is_active = 0 WHERE id = %s", (course_id,))
    return ok(message="Da an hoc phan khoi danh sach dang ky.")


@app.get("/api/admin/sections")
@role_required("admin")
def admin_sections():
    rows = fetch_all(
        """
        SELECT cs.*, c.course_code, c.course_name, c.credits,
               (cs.max_capacity - cs.enrolled_count) AS available_seats
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        ORDER BY cs.section_code
        """
    )
    return ok({"sections": clean_rows(rows)})


def validate_section_payload(data):
    start_period = int(data.get("start_period") or 0)
    end_period = int(data.get("end_period") or 0)
    max_capacity = int(data.get("max_capacity") or 0)
    if start_period < 1 or end_period < start_period:
        raise ApiError("Tiet hoc khong hop le.")
    if max_capacity < 1:
        raise ApiError("Suc chua phai lon hon 0.")
    return start_period, end_period, max_capacity


@app.post("/api/admin/sections")
@role_required("admin")
def create_section():
    data = request.get_json(force=True)
    start_period, end_period, max_capacity = validate_section_payload(data)
    execute(
        """
        INSERT INTO class_sections
            (course_id, section_code, expected_class_code, semester, academic_year,
             day_of_week, start_period, end_period, building, room, lecturer,
             max_capacity, enrolled_count, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s)
        """,
        (
            int(data.get("course_id") or 0),
            (data.get("section_code") or "").strip().upper(),
            (data.get("expected_class_code") or "").strip().upper(),
            (data.get("semester") or "").strip(),
            (data.get("academic_year") or "").strip(),
            int(data.get("day_of_week") or 2),
            start_period,
            end_period,
            (data.get("building") or "").strip(),
            (data.get("room") or "").strip(),
            (data.get("lecturer") or "").strip(),
            max_capacity,
            data.get("status") or "open",
        ),
    )
    return ok(message="Da tao lop hoc phan.")


@app.put("/api/admin/sections/<int:section_id>")
@role_required("admin")
def update_section(section_id):
    data = request.get_json(force=True)
    start_period, end_period, max_capacity = validate_section_payload(data)
    current = fetch_one(
        "SELECT enrolled_count FROM class_sections WHERE id = %s", (section_id,)
    )
    if not current:
        raise ApiError("Khong tim thay lop hoc phan.", 404)
    if max_capacity < current["enrolled_count"]:
        raise ApiError("Suc chua khong duoc nho hon so sinh vien da dang ky.")
    execute(
        """
        UPDATE class_sections
        SET course_id = %s, section_code = %s, expected_class_code = %s,
            semester = %s, academic_year = %s, day_of_week = %s,
            start_period = %s, end_period = %s, building = %s, room = %s,
            lecturer = %s, max_capacity = %s, status = %s
        WHERE id = %s
        """,
        (
            int(data.get("course_id") or 0),
            (data.get("section_code") or "").strip().upper(),
            (data.get("expected_class_code") or "").strip().upper(),
            (data.get("semester") or "").strip(),
            (data.get("academic_year") or "").strip(),
            int(data.get("day_of_week") or 2),
            start_period,
            end_period,
            (data.get("building") or "").strip(),
            (data.get("room") or "").strip(),
            (data.get("lecturer") or "").strip(),
            max_capacity,
            data.get("status") or "open",
            section_id,
        ),
    )
    return ok(message="Da cap nhat lop hoc phan.")


@app.delete("/api/admin/sections/<int:section_id>")
@role_required("admin")
def delete_section(section_id):
    execute(
        "UPDATE class_sections SET status = 'cancelled' WHERE id = %s",
        (section_id,),
    )
    return ok(message="Da chuyen lop sang trang thai da huy.")


@app.get("/api/admin/enrollments")
@role_required("admin")
def admin_enrollments():
    rows = fetch_all(
        """
        SELECT e.id, e.registered_at, e.tuition_fee, e.payment_deadline,
               e.is_paid, e.status, e.cancelled_at,
               s.id AS student_id, s.student_code, s.full_name,
               cs.id AS section_id, cs.section_code, cs.expected_class_code,
               c.course_code, c.course_name, c.credits
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        ORDER BY e.registered_at DESC
        """
    )
    students = fetch_all(
        "SELECT id, student_code, full_name FROM students ORDER BY student_code"
    )
    sections = fetch_all(
        """
        SELECT cs.id, cs.section_code, c.course_code, c.course_name,
               cs.enrolled_count, cs.max_capacity, cs.status
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        ORDER BY cs.section_code
        """
    )
    return ok(
        {
            "enrollments": clean_rows(rows),
            "students": clean_rows(students),
            "sections": clean_rows(sections),
        }
    )


@app.post("/api/admin/enrollments")
@role_required("admin")
def admin_create_enrollment():
    data = request.get_json(force=True)
    create_registration(
        int(data.get("student_id") or 0),
        int(data.get("section_id") or 0),
        force=bool(data.get("force")),
    )
    return ok(message="Da them dang ky cho sinh vien.")


@app.delete("/api/admin/enrollments/<int:enrollment_id>")
@role_required("admin")
def admin_cancel_enrollment(enrollment_id):
    row = fetch_one("SELECT student_id FROM enrollments WHERE id = %s", (enrollment_id,))
    if not row:
        raise ApiError("Khong tim thay dang ky.", 404)
    cancel_registration_for_student(row["student_id"], enrollment_id, allow_locked=True)
    return ok(message="Da huy dang ky.")


@app.put("/api/admin/enrollments/<int:enrollment_id>/tuition")
@role_required("admin")
def admin_update_tuition(enrollment_id):
    data = request.get_json(force=True)
    execute(
        """
        UPDATE enrollments
        SET tuition_fee = %s, payment_deadline = %s, is_paid = %s
        WHERE id = %s
        """,
        (
            Decimal(str(data.get("tuition_fee") or 0)),
            data.get("payment_deadline") or None,
            1 if data.get("is_paid") else 0,
            enrollment_id,
        ),
    )
    return ok(message="Da cap nhat hoc phi.")


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_RUN_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )
