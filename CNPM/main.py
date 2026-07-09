#-------------------------------------------------------------------------------------------
#kiểm tra xem lịch học của lớp mà sinh viên muốn đăng ký có bị trùng với lịch của các lớp mà sinh viên đã đăng ký trước đó hay không.
def check_schedule_conflict(sched1, sched2):
    """Kiểm tra trùng lịch học. Ví dụ: 'Thứ 5, tiết 2-4'"""
    pattern = r'Thứ\s*(\d+),\s*tiết\s*(\d+)-(\d+)'
    # Định nghĩa biểu thức chính quy để trích ngày và tiết.

    m1 = re.search(pattern, sched1, re.IGNORECASE)
    m2 = re.search(pattern, sched2, re.IGNORECASE)
    #Tìm kiếm mẫu trong sched1 và sched2.
    # re.IGNORECASE cho phép không phân biệt hoa thường.

    if not m1 or not m2: return False 
    # Nếu một trong hai lịch không khớp định dạng mẫu, trả về False.
    # Nghĩa là không coi là trùng lịch nếu không xác định được ngày-tiết rõ ràng.

    day1, s1, e1 = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
    day2, s2, e2 = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    # Chuyển đổi ngày và tiết thành số nguyên để so sánh.
    
    if day1 == day2:
        # Kiểm tra khoảng thời gian có giao nhau không (start1 <= end2 và start2 <= end1)
        if max(s1, s2) <= min(e1, e2): # Nếu có giao nhau, tức là trùng lịch.
            return True
    return False
#Việc tách hàm này riêng biệt giúp mã nguồn dễ tái sử dụng và dễ bảo trì hơn, vì mỗi lần cần kiểm tra lịch học chỉ cần gọi lại hàm này.
#---------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------------------------------------
#class quản lý giao diện đăng ký học phần cho sinh viên

class CourseListFrame(ctk.CTkFrame): #Khai báo Class & Constructor
#Định nghĩa lớp CourseListFrame kế thừa từ ctk.CTkFrame (khung giao diện CustomTkinter)

    def __init__(self, parent, controller):
    #Constructor khởi tạo đối tượng
    #lưu đối tượng controller, giúp giao diện có thể kết nối cơ sở dữ liệu, lấy thông tin sinh viên đang đăng nhập và chuyển đổi giữa các màn hình.
        super().__init__(parent, fg_color="transparent")
        #super().__init__(): Gọi hàm khởi tạo của lớp cha với nền trong suốt (fg_color="transparent")

        self.controller = controller 
        #Lưu trữ tham chiếu controller để sử dụng sau này (gọi hàm kết nối DB, lấy thông tin user...)

        #Phần 1: Tiêu đề & Bảng Môn Học
        ctk.CTkLabel(self, text="Đăng ký học phần", font=("Arial", 24, "bold"), text_color="#1e293b").place(x=30, y=20)
        #Tạo nhãn tiêu đề "Đăng ký học phần"
        #Vị trí: x=30px, y=20px
        #Font: Arial 24, bold, màu xanh đậm (#1e293b)
        
        self.tree = ttk.Treeview(self, columns=("Mã HP", "Tên HP", "Tín chỉ", "Tiên quyết"), show="headings", height=5)
        # Tạo bảng Treeview để hiển thị danh sách môn học, height=5: hiển thị 5 dòng

        for c in self.tree["columns"]: self.tree.heading(c, text=c)
        # Thiết lập tiêu đề cột cho bảng Treeview dựa trên danh sách cột đã khai báo

        self.tree.column("Mã HP", width=80, anchor="center"); self.tree.column("Tên HP", width=300)
        self.tree.column("Tín chỉ", width=70, anchor="center"); self.tree.column("Tiên quyết", width=150)
        # Định nghĩa độ rộng và căn chỉnh cho từng cột trong bảng Treeview

        self.tree.place(x=30, y=70, width=820, height=200)
        # Đặt vị trí và kích thước của bảng Treeview trên giao diện: x=30px, y=70px, width=820px, height=200px
        
        self.tree.bind('<<TreeviewSelect>>', self.on_course_select)
        # Khi người dùng chọn một dòng trong bảng → gọi hàm on_course_select()
        # Liên kết sự kiện chọn dòng trong bảng Treeview với hàm on_course_select để xử lý khi người dùng chọn một môn học.

        # Phần hai: Bảng Lớp học phần
        ctk.CTkLabel(self, text="Lớp học phần khả dụng", font=("Arial", 14, "bold")).place(x=30, y=290)
        # Tạo nhãn tiêu đề "Lớp học phần khả dụng" phía trên bảng lớp học phần

        self.tree_sec = ttk.Treeview(self, columns=("Mã Lớp", "Lịch học", "Sĩ số", "Trạng thái"), show="headings", height=5)
        # Tạo bảng Treeview để hiển thị danh sách lớp học phần, height=5: hiển thị 5 dòng

        for c in self.tree_sec["columns"]: self.tree_sec.heading(c, text=c)
        # Thiết lập tiêu đề cột cho bảng Treeview dựa trên danh sách cột đã khai báo

        self.tree_sec.column("Mã Lớp", width=100, anchor="center"); self.tree_sec.column("Lịch học", width=250)
        self.tree_sec.column("Sĩ số", width=100, anchor="center"); self.tree_sec.column("Trạng thái", width=120, anchor="center")
        self.tree_sec.place(x=30, y=320, width=820, height=200)
        # Cấu hình cột và vị trí bảng

        ctk.CTkButton(self, text="Kiểm tra & Đăng ký", fg_color="#0f6466", font=("Arial", 14, "bold"), command=self.register_class, width=220, height=45).place(x=630, y=540)
        # Tạo nút "Kiểm tra & Đăng ký" để người dùng nhấn đăng ký lớp học phần đã chọn
        # Khi nhấn nút → gọi hàm register_class() để xử lý đăng ký lớp học phần.
    
    # Phần 3: Hàm update_data() - Cập nhật dữ liệu
    def update_data(self): 
    # Hàm này được gọi khi người dùng chuyển sang màn hình đăng ký học phần để load dữ liệu mới nhất từ database.    

        for row in self.tree.get_children(): self.tree.delete(row)
        for row in self.tree_sec.get_children(): self.tree_sec.delete(row)
        # Xóa tất cả các dòng hiện có trong bảng môn học và bảng lớp học phần trước khi load dữ liệu mới.

        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        # Kết nối đến cơ sở dữ liệu và tạo con trỏ để thực hiện truy vấn.

        cursor.execute("SELECT courseCode, courseName, credit, prerequisites FROM Courses")
        # Truy vấn tất cả các môn học từ bảng Courses, lấy các cột: courseCode, courseName, credit, prerequisites.

        for r in cursor.fetchall(): self.tree.insert("", "end", values=r)
        # Duyệt qua tất cả các kết quả truy vấn và chèn từng dòng vào bảng môn học (self.tree).

        cursor.close(); conn.close()
        # Đóng con trỏ và kết nối đến cơ sở dữ liệu sau khi hoàn tất việc truy vấn và chèn dữ liệu.

    # Phần 4: Hàm on_course_select() - Xử lý khi người dùng chọn một môn học
    def on_course_select(self, event):
    # Khi người dùng chọn một dòng trong bảng môn học, hàm này sẽ được gọi để hiển thị các lớp học phần khả dụng cho môn học đó.

        sel = self.tree.selection()
        # Lấy dòng đang được chọn trong bảng môn học (self.tree) bằng phương thức selection().

        if not sel: return
        # Nếu không có dòng nào được chọn, hàm sẽ dừng lại và không thực hiện gì thêm.

        code = self.tree.item(sel[0])['values'][0]
        # Lấy mã môn học (courseCode) từ dòng được chọn. sel[0] là dòng đầu tiên được chọn,
        # item(sel[0]) trả về thông tin của dòng đó, ['values'][0] lấy giá trị của cột đầu tiên (courseCode).

        for row in self.tree_sec.get_children(): self.tree_sec.delete(row)
        # Xóa tất cả các dòng hiện có trong bảng lớp học phần (self.tree_sec) trước khi load dữ liệu mới.

        conn = self.controller.get_db_connection(); cursor = conn.cursor()
        # Kết nối đến cơ sở dữ liệu và tạo con trỏ để thực hiện truy vấn.

        cursor.execute("SELECT sectionCode, schedule, CONCAT(currentEnroll, '/', maxEnroll), status FROM ClassSection WHERE courseCode=%s", (code,))
        # Truy vấn tất cả các lớp học phần từ bảng ClassSection cho môn học được chọn (courseCode=code).

        for r in cursor.fetchall(): self.tree_sec.insert("", "end", values=r)
        # Duyệt qua tất cả các kết quả truy vấn và chèn từng dòng vào bảng lớp học phần (self.tree_sec).

        cursor.close(); conn.close()
        # Đóng con trỏ và kết nối đến cơ sở dữ liệu sau khi hoàn tất việc truy vấn và chèn dữ liệu.

    #hàm xử lý khi người dùng nhấn nút “Kiểm tra & Đăng ký”.
    def register_class(self): 
        sel = self.tree_sec.selection() 
        #self.tree_sec là bảng hiển thị các lớp học phần.
        #selection() lấy dòng đang được chọn trong bảng.

        if not sel: return messagebox.showwarning("Chú ý", "Chọn một lớp!")
        #Nếu không chọn gì, hiện hộp cảnh báo: “Chọn một lớp!”.

        sec_code = self.tree_sec.item(sel[0])['values'][0]
        sched_target = self.tree_sec.item(sel[0])['values'][1]
        status = self.tree_sec.item(sel[0])['values'][3]
        #sec_code là mã lớp học phần được chọn, 
        # sched_target là lịch học của lớp đó, 
        # status là trạng thái của lớp (Mở đăng ký hoặc Khóa đăng ký).

        if status != "Mở đăng ký": return messagebox.showerror("Lỗi", "Lớp đã khóa/đầy!")
        #Nếu trạng thái không phải “Mở đăng ký”, tức là lớp đã khóa hoặc đầy thì không cho đăng ký.
        #Hàm dừng lại và hiện thông báo lỗi.

        sid = self.controller.current_student_id
        #self.controller là tham chiếu đến đối tượng CourseRegApp,
        #current_student_id là thuộc tính lưu trữ mã sinh viên hiện tại đang đăng nhập.
        #Giá trị này sẽ được dùng để kiểm tra đăng ký của sinh viên đó.

        try: #Mở kết nối database
            conn = self.controller.get_db_connection(); cursor = conn.cursor(dictionary=True)
            #Mở kết nối đến cơ sở dữ liệu 
            #cursor dùng để truy vấn dữ liệu.
            #dictionary=True để kết quả trả về dưới dạng dictionary thay vì tuple, giúp truy cập dữ liệu dễ dàng hơn.

            # Trùng lặp (Kiểm tra xem sinh viên đã đăng ký lớp này chưa)
            cursor.execute("SELECT * FROM Enrollment WHERE studentID=%s AND sectionCode=%s", (sid, sec_code))
            # Truy vấn bảng Enrollment để xem có dòng nào ghi rằng sinh viên này đã đăng ký lớp này chưa.

            if cursor.fetchone(): return messagebox.showerror("Lỗi", "Đã đăng ký lớp này rồi!")
            #fetchone lấy dòng kết quả đầu tiên từ truy vấn. 
            # Nếu có kết quả trả về (tức là sinh viên đã đăng ký lớp này), hiện thông báo lỗi: “Đã đăng ký lớp này rồi!” và dừng hàm.

            # Điều kiện tiên quyết
            cursor.execute("SELECT c.prerequisites FROM ClassSection cs JOIN Courses c ON cs.courseCode=c.courseCode WHERE cs.sectionCode=%s", (sec_code,))
            prereqs = cursor.fetchone()['prerequisites']
            #Truy vấn lấy thông tin môn tiên quyết của lớp này từ bảng Courses
            #prereqs là danh sách các môn tiên quyết, có thể là một chuỗi các mã môn học, hoặc 'khong' nếu không có môn tiên quyết.

            if prereqs and prereqs.strip().lower() != 'khong':
            # Nếu có tiên quyết và nó không phải là “khong” thì bắt đầu kiểm tra.

                for req in [p.strip() for p in prereqs.split(',')]:
                #Tách chuỗi tiên quyết thành từng môn riêng lẻ.

                    cursor.execute("SELECT * FROM Enrollment e JOIN ClassSection cs ON e.sectionCode=cs.sectionCode WHERE e.studentID=%s AND cs.courseCode=%s", (sid, req))
                    #Truy vấn tất cả các lớp mà sinh viên đã đăng ký.

                    if not cursor.fetchone(): return messagebox.showerror("Lỗi", f"Chưa học môn tiên quyết: {req}")
                    # Nếu không tìm thấy môn tiên quyết trong danh sách đã đăng ký, hiển thị lỗi.

            # Trùng lịch học (Schedule Conflict)
            cursor.execute("SELECT cs.sectionCode, cs.schedule, c.courseName FROM Enrollment e JOIN ClassSection cs ON e.sectionCode=cs.sectionCode JOIN Courses c ON cs.courseCode=c.courseCode WHERE e.studentID=%s", (sid,))
            #Truy vấn tất cả các lớp mà sinh viên đã đăng ký để kiểm tra trùng lịch học.

            for r in cursor.fetchall():
                #Duyệt qua từng lớp đã đăng ký.
                
                if check_schedule_conflict(sched_target, r['schedule']):
                    #Nếu lịch học của lớp đang đăng ký (sched_target) trùng với lịch học của lớp đã đăng ký (r['schedule']), hiển thị thông báo lỗi với tên môn học và mã lớp bị trùng.
                    #Gọi hàm check_schedule_conflict() để kiểm tra xem lịch mới có trùng với lịch cũ không.

                    return messagebox.showerror("Trùng lịch", f"Schedule conflict detected!\nTrùng với lớp: {r['courseName']} ({r['sectionCode']})")
                    # Nếu không có trùng lịch, tiếp tục kiểm tra các điều kiện khác.

            # Sức chứa
            cursor.execute("SELECT currentEnroll, maxEnroll FROM ClassSection WHERE sectionCode=%s", (sec_code,))
            # Lấy thông tin số lượng sinh viên hiện tại đã đăng ký (currentEnroll) và số lượng tối đa (maxEnroll) của lớp học phần đang đăng ký.

            cap = cursor.fetchone()
            # Nếu số lượng sinh viên hiện tại đã đăng ký >= số lượng tối đa, tức là lớp đã đầy, thì cập nhật trạng thái lớp thành “Khóa đăng ký” và hiển thị thông báo lỗi.

            if cap['currentEnroll'] >= cap['maxEnroll']:
            # Kiểm tra nếu số sinh viên đã đăng ký (currentEnroll) lớn hơn hoặc bằng sức chứa tối đa (maxEnroll).

                cursor.execute("UPDATE ClassSection SET status='Khóa đăng ký' WHERE sectionCode=%s", (sec_code,))
                # Nếu đầy, cập nhật trạng thái lớp trong bảng ClassSection thành "Khóa đăng ký".
                conn.commit(); self.on_course_select(None); return messagebox.showerror("Lỗi", "Lớp đã đầy!")
                # Nếu lớp đã đầy, commit thay đổi, gọi lại hàm on_course_select để refresh bảng lớp học phần, và hiển thị thông báo lỗi: “Lớp đã đầy!”

            # Đăng ký
            cursor.execute("INSERT INTO Enrollment (studentID, sectionCode) VALUES (%s, %s)", (sid, sec_code))
            # Thêm một dòng mới vào bảng Enrollment để ghi nhận sinh viên đã đăng ký lớp học phần này.

            cursor.execute("UPDATE ClassSection SET currentEnroll=currentEnroll+1 WHERE sectionCode=%s", (sec_code,))
            # Cập nhật số lượng sinh viên hiện tại đã đăng ký (currentEnroll) tăng lên 1.

            if cap['currentEnroll'] + 1 == cap['maxEnroll']:
            # Nếu sau khi đăng ký, số lượng sinh viên hiện tại bằng sức chứa tối đa, cập nhật trạng thái lớp thành “Khóa đăng ký”.

                cursor.execute("UPDATE ClassSection SET status='Khóa đăng ký' WHERE sectionCode=%s", (sec_code,))
                # Cập nhật trạng thái lớp học phần trong bảng ClassSection thành "Khóa đăng ký" nếu lớp đã đầy sau khi đăng ký.

            conn.commit(); messagebox.showinfo("Thành công", f"Đăng ký thành công {sec_code}"); self.on_course_select(None)
            # Commit các thay đổi vào cơ sở dữ liệu, hiển thị thông báo thành công với mã lớp học phần đã đăng ký, và gọi lại hàm on_course_select để refresh bảng lớp học phần.

            cursor.close(); conn.close()
            # Đóng con trỏ và kết nối đến cơ sở dữ liệu sau khi hoàn tất việc đăng ký.

        except Exception as e: messagebox.showerror("Lỗi", str(e))
        # Nếu có lỗi xảy ra trong quá trình đăng ký (ví dụ: lỗi kết nối cơ sở dữ liệu, lỗi truy vấn SQL), hiển thị thông báo lỗi với nội dung của ngoại lệ.

#-----------------------------------------------------------------------------------------------------------