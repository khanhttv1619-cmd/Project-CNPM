import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
import re

# Cấu hình giao diện mặc định
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# ==========================================
# 0. HELPER FUNCTIONS (XỬ LÝ LOGIC PHỤ TRỢ)
# ==========================================
def remove_accents(input_str):
    """Xóa dấu tiếng Việt để tạo email"""
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝỲĂĐĨŨƠƯàáâãèéêìíòóôõùúýỳăđĩũơư'
    s0 = u'AAAAEEEIIOOOOUUYADIUOOUaaaaeeeiioooouuyadiuoou'
    s = ''
    for c in input_str:
        s += s0[s1.index(c)] if c in s1 else c
    return s

def generate_email(full_name, student_id):
    """Tạo email tự động: Tên + Ký tự đầu của họ, đệm + 4 số cuối MSSV + @ut.edu.vn"""
    if not full_name or not student_id: return ""
    clean_name = remove_accents(full_name).lower().strip()
    parts = clean_name.split()
    if len(parts) == 0: return ""
    
    first_name = parts[-1]
    initials = "".join([p[0] for p in parts[:-1]])
    last4 = student_id[-4:] if len(student_id) >= 4 else student_id
    return f"{first_name}{initials}{last4}@ut.edu.vn"

def check_schedule_conflict(sched1, sched2):
    """Kiểm tra trùng lịch học. Ví dụ: 'Thứ 5, tiết 2-4'"""
    pattern = r'Thứ\s*(\d+),\s*tiết\s*(\d+)-(\d+)'
    m1 = re.search(pattern, sched1, re.IGNORECASE)
    m2 = re.search(pattern, sched2, re.IGNORECASE)
    if not m1 or not m2: return False 
    
    day1, s1, e1 = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
    day2, s2, e2 = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    
    if day1 == day2:
        # Kiểm tra khoảng thời gian có giao nhau không (start1 <= end2 và start2 <= end1)
        if max(s1, s2) <= min(e1, e2):
            return True
    return False

# ==========================================
# 1. DATABASE SETUP & CONNECTION
# ==========================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678' # Mật khẩu của bạn
}

def setup_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS CourseRegDB")
        cursor.execute("USE CourseRegDB")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS User (
            userID INT AUTO_INCREMENT PRIMARY KEY, userName VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(50) NOT NULL, role VARCHAR(20) NOT NULL)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS Student (
            studentID VARCHAR(20) PRIMARY KEY, userID INT, studentName VARCHAR(50),
            email VARCHAR(50), phone VARCHAR(20), gender VARCHAR(10), birthdate DATE,
            major VARCHAR(50), className VARCHAR(20), FOREIGN KEY (userID) REFERENCES User(userID) ON DELETE CASCADE)""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS Courses (
            courseCode VARCHAR(20) PRIMARY KEY, courseName VARCHAR(100),
            credit INT, fee DECIMAL(10, 0), prerequisites VARCHAR(50))""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS ClassSection (
            sectionCode VARCHAR(20) PRIMARY KEY, courseCode VARCHAR(20),
            schedule VARCHAR(50), room VARCHAR(20), maxEnroll INT, currentEnroll INT, status VARCHAR(20),
            FOREIGN KEY (courseCode) REFERENCES Courses(courseCode) ON DELETE CASCADE)""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS Enrollment (
            enrollID INT AUTO_INCREMENT PRIMARY KEY, studentID VARCHAR(20), sectionCode VARCHAR(20),
            feeCollectionStatus BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (studentID) REFERENCES Student(studentID) ON DELETE CASCADE,
            FOREIGN KEY (sectionCode) REFERENCES ClassSection(sectionCode) ON DELETE CASCADE)""")

        cursor.execute("SELECT COUNT(*) FROM User")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO User (userName, password, role) VALUES ('admin@ut.edu.vn', 'admin123', 'admin')")
            cursor.execute("INSERT INTO User (userName, password, role) VALUES ('2251120001', '123456', 'student')")
            uid = cursor.lastrowid
            cursor.execute("INSERT INTO Student (studentID, userID, studentName, email, phone, gender, birthdate, major, className) VALUES ('2251120001', %s, 'Trần Nguyễn Minh An', 'antn0001@ut.edu.vn', '0901000001', 'Nam', '2005-03-14', 'Cong nghe phan mem', 'CNPM01')", (uid,))
            
            courses = [('AI101', 'Tri tue nhan tao nhap mon', 3, 520000, 'CS102, MATH101'), ('CS101', 'Nhap mon lap trinh', 3, 450000, 'Khong'), ('CS102', 'Cau truc du lieu', 3, 450000, 'CS101'), ('MATH101', 'Toan roi rac', 3, 450000, 'Khong'), ('ENG101', 'Tieng Anh chuyen nganh CNTT', 2, 380000, 'Khong')]
            cursor.executemany("INSERT INTO Courses VALUES (%s, %s, %s, %s, %s)", courses)

            sections = [('AI101-01', 'AI101', 'Thứ 5, tiết 2-4', 'C C302', 40, 1, 'Mở đăng ký'), ('CS101-01', 'CS101', 'Thứ 2, tiết 1-3', 'A A101', 40, 40, 'Khóa đăng ký'), ('CS102-01', 'CS102', 'Thứ 3, tiết 1-3', 'A A102', 40, 10, 'Mở đăng ký'), ('MATH101-01', 'MATH101', 'Thứ 4, tiết 1-3', 'A A103', 40, 5, 'Mở đăng ký')]
            cursor.executemany("INSERT INTO ClassSection VALUES (%s, %s, %s, %s, %s, %s, %s)", sections)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Lỗi DB:", e)

# ==========================================
# 2. MAIN APP
# ==========================================
class CourseRegApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ thống Đăng ký học phần - UTH")
        self.geometry("1100x750")
        self.current_user = None 
        self.current_student_id = None

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#ffffff", foreground="#333333", rowheight=35, fieldbackground="#ffffff", bordercolor="#e2e8f0", borderwidth=1, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#0f6466", foreground="white", font=("Arial", 11, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", "#3b82f6")])
        style.map("Treeview.Heading", background=[("active", "#0b4b4d")])

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        # Khởi tạo tất cả các màn hình
        for F in (LoginFrame, ForgotPasswordFrame, DashboardFrame, AdminDashboardFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame(LoginFrame)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if hasattr(frame, 'update_data'):
            frame.update_data()

    def get_db_connection(self):
        DB_CONFIG['database'] = 'CourseRegDB'
        return mysql.connector.connect(**DB_CONFIG)

# ==========================================
# 3. AUTHENTICATION (LOGIN & FORGOT PASS)
# ==========================================
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e0eafc")
        self.controller = controller

        box = ctk.CTkFrame(self, width=400, height=420, corner_radius=15, fg_color="white")
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text="UNIVERSITY COURSE REGISTRATION", text_color="#0f6466", font=("Arial", 10, "bold")).place(x=40, y=30)
        ctk.CTkLabel(box, text="Đăng ký học phần", font=("Arial", 26, "bold")).place(x=40, y=50)

        ctk.CTkLabel(box, text="Tài khoản", font=("Arial", 12, "bold")).place(x=40, y=110)
        self.e_user = ctk.CTkEntry(box, width=320, height=40, placeholder_text="MSSV hoặc Email")
        self.e_user.place(x=40, y=135)

        ctk.CTkLabel(box, text="Mật khẩu", font=("Arial", 12, "bold")).place(x=40, y=190)
        self.e_pass = ctk.CTkEntry(box, width=320, height=40, placeholder_text="Nhập mật khẩu", show="*")
        self.e_pass.place(x=40, y=215)

        btn_login = ctk.CTkButton(box, text="Đăng nhập", width=320, height=45, fg_color="#0f6466", font=("Arial", 14, "bold"), command=self.login)
        btn_login.place(x=40, y=280)

        btn_forgot = ctk.CTkButton(box, text="Quên mật khẩu?", width=320, height=30, fg_color="transparent", text_color="#0f6466", hover_color="#f1f5f9", command=lambda: self.controller.show_frame(ForgotPasswordFrame))
        btn_forgot.place(x=40, y=340)

    def login(self):
        usr, pwd = self.e_user.get(), self.e_pass.get()
        try:
            conn = self.controller.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM User WHERE userName=%s AND password=%s", (usr, pwd))
            user = cursor.fetchone()
            if user:
                self.controller.current_user = user
                self.e_user.delete(0, 'end'); self.e_pass.delete(0, 'end')
                if user['role'] == 'admin':
                    self.controller.show_frame(AdminDashboardFrame)
                else:
                    cursor.execute("SELECT studentID FROM Student WHERE userID=%s", (user['userID'],))
                    self.controller.current_student_id = cursor.fetchone()['studentID']
                    self.controller.show_frame(DashboardFrame)
            else:
                messagebox.showerror("Lỗi", "Tài khoản hoặc mật khẩu sai!")
            cursor.close(); conn.close()
        except Exception as e: messagebox.showerror("Lỗi DB", str(e))

class ForgotPasswordFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e0eafc")
        self.controller = controller

        box = ctk.CTkFrame(self, width=400, height=350, corner_radius=15, fg_color="white")
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text="Khôi phục mật khẩu", font=("Arial", 22, "bold")).place(x=40, y=40)
        ctk.CTkLabel(box, text="Nhập Tên đăng nhập (MSSV) của bạn:", font=("Arial", 12)).place(x=40, y=100)
        
        self.e_usr = ctk.CTkEntry(box, width=320, height=40, placeholder_text="Mã sinh viên")
        self.e_usr.place(x=40, y=130)

        ctk.CTkButton(box, text="Gửi mật khẩu mới (Mô phỏng Email)", width=320, height=45, fg_color="#d97706", font=("Arial", 14, "bold"), command=self.reset_pass).place(x=40, y=200)
        ctk.CTkButton(box, text="Quay lại Đăng nhập", width=320, height=30, fg_color="transparent", text_color="#0f6466", command=lambda: self.controller.show_frame(LoginFrame)).place(x=40, y=260)

    def reset_pass(self):
        usr = self.e_usr.get()
        if not usr: return
        try:
            conn = self.controller.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM User WHERE userName=%s", (usr,))
            if cursor.fetchone():
                cursor.execute("UPDATE User SET password='123' WHERE userName=%s", (usr,))
                conn.commit()
                messagebox.showinfo("Thành công", "Mật khẩu mới đã được gửi vào Email của bạn là: 123")
                self.controller.show_frame(LoginFrame)
            else:
                messagebox.showerror("Lỗi", "Tài khoản không tồn tại!")
            cursor.close(); conn.close()
        except Exception as e: messagebox.showerror("Lỗi DB", str(e))

# ==========================================
# 4. STUDENT DASHBOARD
# ==========================================
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e293b")
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="Menu Sinh Viên", font=("Arial", 18, "bold"), text_color="white").pack(pady=30)

        btns = [("Học phần", CourseListFrame), ("Đã đăng ký", RegisteredFrame), 
                ("Hồ sơ cá nhân", ProfileFrame), ("Đổi mật khẩu", ChangePassFrame)]
        for txt, frm in btns:
            ctk.CTkButton(self.sidebar, text=txt, fg_color="transparent", hover_color="#334155", anchor="w", font=("Arial", 14), command=lambda f=frm: self.show_page(f)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.sidebar, text="Đăng xuất", fg_color="transparent", hover_color="#ef4444", text_color="#fca5a5", anchor="w", font=("Arial", 14), command=self.logout).pack(side="bottom", fill="x", padx=10, pady=20)

        self.content_area = ctk.CTkFrame(self, fg_color="#f1f5f9")
        self.content_area.pack(side="right", fill="both", expand=True)

        self.pages = {}
        for F in (ProfileFrame, CourseListFrame, RegisteredFrame, ChangePassFrame):
            p = F(self.content_area, self.controller)
            self.pages[F] = p
            p.place(relwidth=1, relheight=1)

    def show_page(self, page_class):
        self.pages[page_class].tkraise()
        if hasattr(self.pages[page_class], 'update_data'): self.pages[page_class].update_data()
    def update_data(self): self.show_page(ProfileFrame)
    def logout(self):
        self.controller.current_user = None; self.controller.current_student_id = None
        self.controller.show_frame(LoginFrame)

class ProfileFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Hồ sơ cá nhân", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        frm = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=820, height=450)
        frm.place(x=30, y=70)

        labels = [("Mã sinh viên", 0, 0), ("Email (Tự động tạo)", 0, 1), ("Họ và Tên", 2, 0), ("Số điện thoại", 2, 1), 
                  ("Giới tính", 4, 0), ("Ngày sinh (YYYY-MM-DD)", 4, 1), ("Ngành học", 6, 0), ("Lớp", 6, 1)]
        self.entries = {}
        for txt, r, c in labels:
            ctk.CTkLabel(frm, text=txt, font=("Arial", 12, "bold")).grid(row=r, column=c, padx=30, pady=(20,5), sticky="w")
            if txt == "Giới tính":
                e = ctk.CTkComboBox(frm, values=["Nam", "Nữ", "Khác"], width=320, height=35)
            else:
                e = ctk.CTkEntry(frm, width=320, height=35)
            e.grid(row=r+1, column=c, padx=30, pady=0)
            self.entries[txt] = e

        ctk.CTkButton(self, text="Cập nhật & Tạo Email", fg_color="#0f6466", font=("Arial", 14, "bold"), command=self.save_profile, width=220, height=45).place(x=30, y=540)

    def update_data(self):
        if not self.controller.current_student_id: return
        conn = self.controller.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Student WHERE studentID=%s", (self.controller.current_student_id,))
        student = cursor.fetchone()
        if student:
            for k in self.entries:
                self.entries[k].configure(state="normal")
                if isinstance(self.entries[k], ctk.CTkEntry): self.entries[k].delete(0, 'end')
            
            self.entries["Mã sinh viên"].insert(0, student['studentID'])
            self.entries["Email (Tự động tạo)"].insert(0, student['email'] if student['email'] else "")
            self.entries["Họ và Tên"].insert(0, student['studentName'] if student['studentName'] else "")
            self.entries["Số điện thoại"].insert(0, student['phone'] if student['phone'] else "")
            self.entries["Giới tính"].set(student['gender'] if student['gender'] else "Nam")
            self.entries["Ngày sinh (YYYY-MM-DD)"].insert(0, str(student['birthdate']) if student['birthdate'] else "")
            self.entries["Ngành học"].insert(0, student['major'] if student['major'] else "")
            self.entries["Lớp"].insert(0, student['className'] if student['className'] else "")

            self.entries["Mã sinh viên"].configure(state="disabled")
            self.entries["Email (Tự động tạo)"].configure(state="disabled")
        cursor.close(); conn.close()

    def save_profile(self):
        full_name = self.entries["Họ và Tên"].get()
        student_id = self.controller.current_student_id
        new_email = generate_email(full_name, student_id) # Sinh email tự động
        dob = self.entries["Ngày sinh (YYYY-MM-DD)"].get()
        
        try:
            conn = self.controller.get_db_connection()
            cursor = conn.cursor()
            query = "UPDATE Student SET studentName=%s, phone=%s, gender=%s, birthdate=%s, major=%s, className=%s, email=%s WHERE studentID=%s"
            values = (full_name, self.entries["Số điện thoại"].get(), self.entries["Giới tính"].get(), 
                      dob if dob else None, self.entries["Ngành học"].get(), self.entries["Lớp"].get(), new_email, student_id)
            cursor.execute(query, values)
            conn.commit(); cursor.close(); conn.close()
            messagebox.showinfo("Thành công", f"Cập nhật thành công!\nEmail hệ thống của bạn là: {new_email}")
            self.update_data()
        except Exception as e: messagebox.showerror("Lỗi Cập nhật", str(e))

class ChangePassFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Đổi Mật Khẩu", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        frm = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=500, height=350)
        frm.place(x=30, y=70)

        ctk.CTkLabel(frm, text="Mật khẩu cũ", font=("Arial", 12, "bold")).place(x=40, y=30)
        self.e_old = ctk.CTkEntry(frm, width=420, height=40, show="*"); self.e_old.place(x=40, y=60)
        ctk.CTkLabel(frm, text="Mật khẩu mới", font=("Arial", 12, "bold")).place(x=40, y=120)
        self.e_new = ctk.CTkEntry(frm, width=420, height=40, show="*"); self.e_new.place(x=40, y=150)
        ctk.CTkLabel(frm, text="Xác nhận mật khẩu", font=("Arial", 12, "bold")).place(x=40, y=210)
        self.e_cf = ctk.CTkEntry(frm, width=420, height=40, show="*"); self.e_cf.place(x=40, y=240)

        ctk.CTkButton(frm, text="Xác nhận đổi", fg_color="#0f6466", font=("Arial", 14, "bold"), command=self.change_pass, width=420, height=45).place(x=40, y=300)

    def change_pass(self):
        o, n, c = self.e_old.get(), self.e_new.get(), self.e_cf.get()
        if not o or not n or not c: return
        if n != c:
            messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp!"); return
        usr = self.controller.current_user['userName']
        try:
            conn = self.controller.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT password FROM User WHERE userName=%s", (usr,))
            real_old = cursor.fetchone()['password']
            if o != real_old:
                messagebox.showerror("Lỗi", "Mật khẩu cũ không chính xác!")
            else:
                cursor.execute("UPDATE User SET password=%s WHERE userName=%s", (n, usr))
                conn.commit()
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!"); 
                self.e_old.delete(0,'end'); self.e_new.delete(0,'end'); self.e_cf.delete(0,'end')
            cursor.close(); conn.close()
        except Exception as e: messagebox.showerror("Lỗi", str(e))

class CourseListFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Đăng ký học phần", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        # Bảng môn học
        self.tree = ttk.Treeview(self, columns=("Mã HP", "Tên HP", "Tín chỉ", "Tiên quyết"), show="headings", height=5)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.column("Mã HP", width=80, anchor="center"); self.tree.column("Tên HP", width=300)
        self.tree.column("Tín chỉ", width=70, anchor="center"); self.tree.column("Tiên quyết", width=150)
        self.tree.place(x=30, y=70, width=820, height=200)
        self.tree.bind('<<TreeviewSelect>>', self.on_course_select)

        # Bảng Lớp học phần
        ctk.CTkLabel(self, text="Lớp học phần khả dụng", font=("Arial", 14, "bold")).place(x=30, y=290)
        self.tree_sec = ttk.Treeview(self, columns=("Mã Lớp", "Lịch học", "Sĩ số", "Trạng thái"), show="headings", height=5)
        for c in self.tree_sec["columns"]: self.tree_sec.heading(c, text=c)
        self.tree_sec.column("Mã Lớp", width=100, anchor="center"); self.tree_sec.column("Lịch học", width=250)
        self.tree_sec.column("Sĩ số", width=100, anchor="center"); self.tree_sec.column("Trạng thái", width=120, anchor="center")
        self.tree_sec.place(x=30, y=320, width=820, height=200)

        ctk.CTkButton(self, text="Kiểm tra & Đăng ký", fg_color="#0f6466", font=("Arial", 14, "bold"), command=self.register_class, width=220, height=45).place(x=630, y=540)

    def update_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for row in self.tree_sec.get_children(): self.tree_sec.delete(row)
        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT courseCode, courseName, credit, prerequisites FROM Courses")
        for r in cursor.fetchall(): self.tree.insert("", "end", values=r)
        cursor.close(); conn.close()

    def on_course_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        code = self.tree.item(sel[0])['values'][0]
        for row in self.tree_sec.get_children(): self.tree_sec.delete(row)
        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT sectionCode, schedule, CONCAT(currentEnroll, '/', maxEnroll), status FROM ClassSection WHERE courseCode=%s", (code,))
        for r in cursor.fetchall(): self.tree_sec.insert("", "end", values=r)
        cursor.close(); conn.close()

    def register_class(self):
        sel = self.tree_sec.selection()
        if not sel: return messagebox.showwarning("Chú ý", "Chọn một lớp!")
        sec_code, sched_target = self.tree_sec.item(sel[0])['values'][0], self.tree_sec.item(sel[0])['values'][1]
        status = self.tree_sec.item(sel[0])['values'][3]
        if status != "Mở đăng ký": return messagebox.showerror("Lỗi", "Lớp đã khóa/đầy!")
        
        sid = self.controller.current_student_id
        try:
            conn = self.controller.get_db_connection(); cursor = conn.cursor(dictionary=True)
            
            # Trùng lặp
            cursor.execute("SELECT * FROM Enrollment WHERE studentID=%s AND sectionCode=%s", (sid, sec_code))
            if cursor.fetchone(): return messagebox.showerror("Lỗi", "Đã đăng ký lớp này rồi!")

            # Điều kiện tiên quyết
            cursor.execute("SELECT c.prerequisites FROM ClassSection cs JOIN Courses c ON cs.courseCode=c.courseCode WHERE cs.sectionCode=%s", (sec_code,))
            prereqs = cursor.fetchone()['prerequisites']
            if prereqs and prereqs.strip().lower() != 'khong':
                for req in [p.strip() for p in prereqs.split(',')]:
                    cursor.execute("SELECT * FROM Enrollment e JOIN ClassSection cs ON e.sectionCode=cs.sectionCode WHERE e.studentID=%s AND cs.courseCode=%s", (sid, req))
                    if not cursor.fetchone(): return messagebox.showerror("Lỗi", f"Chưa học môn tiên quyết: {req}")

            # Trùng lịch học (Schedule Conflict)
            cursor.execute("SELECT cs.sectionCode, cs.schedule, c.courseName FROM Enrollment e JOIN ClassSection cs ON e.sectionCode=cs.sectionCode JOIN Courses c ON cs.courseCode=c.courseCode WHERE e.studentID=%s", (sid,))
            for r in cursor.fetchall():
                if check_schedule_conflict(sched_target, r['schedule']):
                    return messagebox.showerror("Trùng lịch", f"Schedule conflict detected!\nTrùng với lớp: {r['courseName']} ({r['sectionCode']})")

            # Sức chứa
            cursor.execute("SELECT currentEnroll, maxEnroll FROM ClassSection WHERE sectionCode=%s", (sec_code,))
            cap = cursor.fetchone()
            if cap['currentEnroll'] >= cap['maxEnroll']:
                cursor.execute("UPDATE ClassSection SET status='Khóa đăng ký' WHERE sectionCode=%s", (sec_code,))
                conn.commit(); self.on_course_select(None); return messagebox.showerror("Lỗi", "Lớp đã đầy!")

            # Đăng ký
            cursor.execute("INSERT INTO Enrollment (studentID, sectionCode) VALUES (%s, %s)", (sid, sec_code))
            cursor.execute("UPDATE ClassSection SET currentEnroll=currentEnroll+1 WHERE sectionCode=%s", (sec_code,))
            if cap['currentEnroll'] + 1 == cap['maxEnroll']:
                cursor.execute("UPDATE ClassSection SET status='Khóa đăng ký' WHERE sectionCode=%s", (sec_code,))
            
            conn.commit(); messagebox.showinfo("Thành công", f"Đăng ký thành công {sec_code}"); self.on_course_select(None)
            cursor.close(); conn.close()
        except Exception as e: messagebox.showerror("Lỗi", str(e))

class RegisteredFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Học phần đã đăng ký", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        crd = ctk.CTkFrame(self, fg_color="#e0f2fe", corner_radius=10, width=820, height=60)
        crd.place(x=30, y=70)
        self.lbl_sum = ctk.CTkLabel(crd, text="Tổng tín chỉ: 0    |    Học phí: 0 VNĐ", font=("Arial", 16, "bold"), text_color="#0369a1")
        self.lbl_sum.place(relx=0.5, rely=0.5, anchor="center")

        self.tree = ttk.Treeview(self, columns=("Mã Lớp", "Môn học", "Tín chỉ", "Học phí", "Đóng tiền"), show="headings", height=10)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.column("Mã Lớp", width=100); self.tree.column("Môn học", width=280)
        self.tree.column("Tín chỉ", width=80); self.tree.column("Học phí", width=140); self.tree.column("Đóng tiền", width=120)
        self.tree.place(x=30, y=150, width=820, height=350)

        ctk.CTkButton(self, text="Hủy đăng ký", fg_color="#ef4444", command=self.cancel_class, width=200, height=45).place(x=650, y=520)

    def update_data(self):
        if not self.controller.current_student_id: return
        for row in self.tree.get_children(): self.tree.delete(row)
        conn = self.controller.get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT cs.sectionCode, c.courseName, c.credit, c.fee, e.feeCollectionStatus FROM Enrollment e JOIN ClassSection cs ON e.sectionCode=cs.sectionCode JOIN Courses c ON cs.courseCode=c.courseCode WHERE e.studentID=%s", (self.controller.current_student_id,))
        recs = cursor.fetchall(); tc, fee = 0, 0
        for r in recs:
            st = "Đã thu" if r['feeCollectionStatus'] else "Chưa nộp"
            self.tree.insert("", "end", values=(r['sectionCode'], r['courseName'], r['credit'], f"{r['fee']:,.0f}", st))
            tc += r['credit']; fee += r['fee']
        self.lbl_sum.configure(text=f"Tổng tín chỉ: {tc}    |    Học phí: {fee:,.0f} đ")
        cursor.close(); conn.close()

    def cancel_class(self):
        sel = self.tree.selection()
        if not sel: return
        sec = self.tree.item(sel[0])['values'][0]
        if not messagebox.askyesno("Xác nhận", f"Hủy lớp {sec}?"): return
        try:
            conn = self.controller.get_db_connection(); cursor = conn.cursor()
            cursor.execute("DELETE FROM Enrollment WHERE studentID=%s AND sectionCode=%s", (self.controller.current_student_id, sec))
            cursor.execute("UPDATE ClassSection SET currentEnroll=currentEnroll-1 WHERE sectionCode=%s", (sec,))
            cursor.execute("SELECT currentEnroll, maxEnroll FROM ClassSection WHERE sectionCode=%s", (sec,))
            cap = cursor.fetchone()
            if cap[0] < cap[1]: cursor.execute("UPDATE ClassSection SET status='Mở đăng ký' WHERE sectionCode=%s", (sec,))
            conn.commit(); self.update_data(); cursor.close(); conn.close()
        except Exception as e: messagebox.showerror("Lỗi", str(e))

# ==========================================
# 5. ADMIN DASHBOARD & SCREENS
# ==========================================
class AdminDashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#450a0a") 
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="Admin Panel", font=("Arial", 18, "bold"), text_color="white").pack(pady=30)

        for txt, frm in [("Quản lý Môn học", AdminCourseFrame), ("Quản lý Lớp học", AdminClassFrame), 
                         ("Quản lý Đăng ký", AdminEnrollFrame), ("Quản lý Học phí", AdminTuitionFrame), 
                         ("Quản lý Tài khoản", AdminAccountFrame)]:
            ctk.CTkButton(self.sidebar, text=txt, fg_color="transparent", hover_color="#7f1d1d", anchor="w", font=("Arial", 14), command=lambda f=frm: self.show_page(f)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.sidebar, text="Đăng xuất", fg_color="transparent", hover_color="#dc2626", text_color="#fca5a5", anchor="w", font=("Arial", 14), command=self.logout).pack(side="bottom", fill="x", padx=10, pady=20)

        self.content_area = ctk.CTkFrame(self, fg_color="#f1f5f9")
        self.content_area.pack(side="right", fill="both", expand=True)

        self.pages = {}
        for F in (AdminCourseFrame, AdminClassFrame, AdminEnrollFrame, AdminTuitionFrame, AdminAccountFrame):
            p = F(self.content_area, self.controller)
            self.pages[F] = p
            p.place(relwidth=1, relheight=1)

    def show_page(self, p_class): self.pages[p_class].tkraise(); self.pages[p_class].update_data()
    def update_data(self): self.show_page(AdminCourseFrame)
    def logout(self): self.controller.current_user = None; self.controller.show_frame(LoginFrame)

# --- 5.1 Quản lý Đăng ký (Manage Enrollment) ---
class AdminEnrollFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Quản lý Danh sách Đăng ký", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        self.tree = ttk.Treeview(self, columns=("ID", "Mã SV", "Tên Sinh viên", "Mã Lớp", "Đóng phí"), show="headings", height=15)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.column("ID", width=50); self.tree.column("Mã SV", width=120)
        self.tree.column("Tên Sinh viên", width=300); self.tree.column("Mã Lớp", width=120)
        self.tree.place(x=30, y=70, width=800, height=450)
        
        ctk.CTkButton(self, text="Xóa Đăng ký (Rút môn)", fg_color="#dc2626", command=self.delete_enroll, width=200, height=45).place(x=30, y=540)

    def update_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        try:
            conn = self.controller.get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT e.enrollID, s.studentID, s.studentName, e.sectionCode, e.feeCollectionStatus FROM Enrollment e JOIN Student s ON e.studentID=s.studentID")
            for r in cursor.fetchall(): 
                self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], "Rồi" if r[4] else "Chưa"))
            cursor.close(); conn.close()
        except: pass

    def delete_enroll(self):
        sel = self.tree.selection()
        if not sel: return
        eid, sec = self.tree.item(sel[0])['values'][0], self.tree.item(sel[0])['values'][3]
        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        cursor.execute("DELETE FROM Enrollment WHERE enrollID=%s", (eid,))
        cursor.execute("UPDATE ClassSection SET currentEnroll=currentEnroll-1, status='Mở đăng ký' WHERE sectionCode=%s", (sec,))
        conn.commit(); cursor.close(); conn.close(); self.update_data()

# --- 5.2 Quản lý Học phí (Tuition Management) ---
class AdminTuitionFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Quản lý Học phí Sinh viên", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        self.tree = ttk.Treeview(self, columns=("Mã SV", "Tên Sinh viên", "Tổng TC", "Tổng Tiền", "Trạng thái"), show="headings", height=15)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.column("Mã SV", width=120); self.tree.column("Tên Sinh viên", width=250)
        self.tree.place(x=30, y=70, width=800, height=450)
        
        ctk.CTkButton(self, text="Đánh dấu: ĐÃ THU", fg_color="#0f6466", command=self.mark_paid, width=200, height=45).place(x=30, y=540)

    def update_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        try:
            conn = self.controller.get_db_connection(); cursor = conn.cursor()
            cursor.execute("""
                SELECT s.studentID, s.studentName, SUM(c.credit), SUM(c.fee), e.feeCollectionStatus
                FROM Enrollment e JOIN Student s ON e.studentID=s.studentID JOIN ClassSection cs ON e.sectionCode=cs.sectionCode JOIN Courses c ON cs.courseCode=c.courseCode
                GROUP BY s.studentID, s.studentName, e.feeCollectionStatus
            """)
            for r in cursor.fetchall(): 
                self.tree.insert("", "end", values=(r[0], r[1], r[2], f"{r[3]:,.0f}", "Hoàn thành" if r[4] else "Chưa đóng"))
            cursor.close(); conn.close()
        except: pass

    def mark_paid(self):
        sel = self.tree.selection()
        if not sel: return
        sid = self.tree.item(sel[0])['values'][0]
        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE Enrollment SET feeCollectionStatus=1 WHERE studentID=%s", (sid,))
        conn.commit(); cursor.close(); conn.close(); self.update_data()

# --- 5.3 Quản lý Môn học, Lớp, Tài khoản (Giữ nguyên gọn gàng) ---
class AdminCourseFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Quản lý Môn học", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        
        self.tree = ttk.Treeview(self, columns=("Mã HP", "Tên HP", "TC", "Tiền", "Tiên quyết"), show="headings", height=8)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.place(x=30, y=70, width=800, height=300)

        frm = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=800, height=180)
        frm.place(x=30, y=390)
        self.es = [ctk.CTkEntry(frm, width=w) for w in [100, 220, 70, 120, 150]]
        for i, (txt, e) in enumerate(zip(["Mã HP", "Tên HP", "Tín chỉ", "Học phí", "Tiên quyết"], self.es)):
            ctk.CTkLabel(frm, text=txt, font=("Arial",12,"bold")).grid(row=0, column=i, padx=10, pady=10)
            e.grid(row=1, column=i, padx=10)
        
        ctk.CTkButton(frm, text="Lưu", fg_color="#0f6466", command=self.add).grid(row=2, column=1, pady=20)
        ctk.CTkButton(frm, text="Xóa", fg_color="#dc2626", command=self.delete).grid(row=2, column=2, pady=20)

    def update_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn=self.controller.get_db_connection(); c=conn.cursor(); c.execute("SELECT * FROM Courses")
        for r in c.fetchall(): self.tree.insert("","end",values=r)
        c.close(); conn.close()

    def add(self):
        v = [e.get() for e in self.es]
        if not v[0]: return
        conn=self.controller.get_db_connection(); c=conn.cursor()
        c.execute("INSERT INTO Courses VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE courseName=%s, credit=%s, fee=%s, prerequisites=%s", (*v, v[1], v[2], v[3], v[4]))
        conn.commit(); c.close(); conn.close(); self.update_data()
    def delete(self):
        sel=self.tree.selection()
        if sel:
            conn=self.controller.get_db_connection(); c=conn.cursor()
            c.execute("DELETE FROM Courses WHERE courseCode=%s",(self.tree.item(sel[0])['values'][0],))
            conn.commit(); c.close(); conn.close(); self.update_data()

class AdminClassFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Quản lý Lớp", font=("Arial", 24, "bold")).place(x=30, y=20)
        self.tree = ttk.Treeview(self, columns=("Lớp", "Môn", "Lịch", "Phòng", "Sĩ số", "TT"), show="headings", height=8)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.place(x=30, y=70, width=800, height=300)
        
        frm = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=800, height=180)
        frm.place(x=30, y=390)
        self.es = [ctk.CTkEntry(frm, width=w) for w in [100, 100, 200, 80, 50]]
        self.es.append(ctk.CTkComboBox(frm, values=["Mở đăng ký", "Khóa đăng ký", "Đã hủy"], width=120))
        for i, (txt, e) in enumerate(zip(["Mã Lớp", "Môn", "Lịch (Thứ X, tiết Y-Z)", "Phòng", "Max", "Status"], self.es)):
            ctk.CTkLabel(frm, text=txt, font=("Arial",12,"bold")).grid(row=0, column=i, padx=5, pady=10)
            e.grid(row=1, column=i, padx=5)
        ctk.CTkButton(frm, text="Lưu", fg_color="#0f6466", command=self.add).grid(row=2, column=2, pady=20)
        ctk.CTkButton(frm, text="Xóa", fg_color="#dc2626", command=self.delete).grid(row=2, column=3, pady=20)

    def update_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn=self.controller.get_db_connection(); c=conn.cursor()
        c.execute("SELECT sectionCode, courseCode, schedule, room, CONCAT(currentEnroll,'/',maxEnroll), status FROM ClassSection")
        for r in c.fetchall(): self.tree.insert("","end",values=r)
        c.close(); conn.close()
    def add(self):
        v = [e.get() for e in self.es]
        if not v[0]: return
        conn=self.controller.get_db_connection(); c=conn.cursor()
        c.execute("INSERT INTO ClassSection VALUES (%s,%s,%s,%s,%s,0,%s) ON DUPLICATE KEY UPDATE courseCode=%s, schedule=%s, room=%s, maxEnroll=%s, status=%s", (*v, v[1], v[2], v[3], v[4], v[5]))
        conn.commit(); c.close(); conn.close(); self.update_data()
    def delete(self):
        sel=self.tree.selection()
        if sel:
            conn=self.controller.get_db_connection(); c=conn.cursor()
            c.execute("DELETE FROM ClassSection WHERE sectionCode=%s",(self.tree.item(sel[0])['values'][0],))
            conn.commit(); c.close(); conn.close(); self.update_data()

class AdminAccountFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Quản lý Tài khoản", font=("Arial", 24, "bold")).place(x=30, y=20)
        self.tree = ttk.Treeview(self, columns=("User", "Role"), show="headings", height=8)
        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        self.tree.place(x=30, y=70, width=800, height=300)

        frm = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=800, height=180)
        frm.place(x=30, y=390)
        self.u, self.p = ctk.CTkEntry(frm, width=200), ctk.CTkEntry(frm, width=200)
        self.r = ctk.CTkComboBox(frm, values=["student", "admin"], width=100)
        for i, (txt, e) in enumerate(zip(["User (MSSV)", "Pass", "Role"], [self.u, self.p, self.r])):
            ctk.CTkLabel(frm, text=txt, font=("Arial",12,"bold")).grid(row=0, column=i, padx=20, pady=10)
            e.grid(row=1, column=i, padx=20)
        ctk.CTkButton(frm, text="Tạo", fg_color="#0f6466", command=self.add).grid(row=2, column=0, pady=20)
        ctk.CTkButton(frm, text="Reset Pass", fg_color="#d97706", command=self.reset).grid(row=2, column=1, pady=20)
        ctk.CTkButton(frm, text="Xóa", fg_color="#dc2626", command=self.delete).grid(row=2, column=2, pady=20)

    def update_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn=self.controller.get_db_connection(); c=conn.cursor()
        c.execute("SELECT userName, role FROM User")
        for r in c.fetchall(): self.tree.insert("","end",values=r)
        c.close(); conn.close()
    def add(self):
        u,p,r = self.u.get(), self.p.get(), self.r.get()
        if not u: return
        conn=self.controller.get_db_connection(); c=conn.cursor()
        c.execute("INSERT INTO User (userName, password, role) VALUES (%s,%s,%s)", (u,p,r))
        if r=='student': c.execute("INSERT INTO Student (studentID, userID, email) VALUES (%s,%s,%s)", (u, c.lastrowid, u))
        conn.commit(); c.close(); conn.close(); self.update_data()
    def reset(self):
        sel=self.tree.selection(); p=self.p.get()
        if sel and p:
            conn=self.controller.get_db_connection(); c=conn.cursor()
            c.execute("UPDATE User SET password=%s WHERE userName=%s",(p, self.tree.item(sel[0])['values'][0]))
            conn.commit(); c.close(); conn.close(); messagebox.showinfo("OK", "Đã reset!")
    def delete(self):
        sel=self.tree.selection()
        if sel:
            conn=self.controller.get_db_connection(); c=conn.cursor()
            c.execute("DELETE FROM User WHERE userName=%s",(self.tree.item(sel[0])['values'][0],))
            conn.commit(); c.close(); conn.close(); self.update_data()

if __name__ == "__main__":
    setup_database() 
    app = CourseRegApp()
    app.mainloop()
