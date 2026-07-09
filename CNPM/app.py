@app.post("/api/student/register") # khai báo route HTTP POST cho URL đó.
@role_required("student") 
# kiểm tra vai trò của người dùng hiện tại, chỉ cho phép sinh viên thực hiện đăng ký lớp học phần.

def register_class():
    # Lấy dữ liệu JSON từ yêu cầu HTTP POST và ép kiểu dữ liệu về dạng JSON.
    data = request.get_json(force=True)
    # force=True ép Flask parse body thành JSON ngay cả khi header không phải application/json.

    section_id = int(data.get("section_id") or 0)
    # Lấy giá trị section_id từ dữ liệu JSON, nếu không có thì mặc định là 0, chuyen đổi sang kiểu int.

    create_registration(current_student_id(), section_id)
    # Gọi hàm create_registration để thực hiện đăng ký lớp học phần cho sinh viên hiện tại với section_id đã lấy được.
    # current_student_id() trả về ID sinh viên đang đăng nhập, section_id là mã lớp cần đăng ký.

    return ok(get_registered_summary(current_student_id()), "Registration successful.")
    # Trả về phản hồi JSON với thông tin tổng quan về các lớp học phần đã đăng ký của sinh viên hiện tại, cùng với thông báo "Registration successful."
    # Trả về phản hồi HTTP thành công.
    # get_registered_summary(current_student_id()) lấy lại thông tin đăng ký mới nhất của sinh viên.
    # ok(...) có thể là helper tạo response chuẩn cùng thông điệp "Registration successful.".

def cancel_registration_for_student(student_id, enrollment_id, allow_locked=False):
# Hàm hủy đăng ký cho một sinh viên cụ thể.
# allow_locked=False nghĩa là nếu lớp đã khóa thì không được hủy.

    db = get_db()
    cur = db.cursor(dictionary=True)
    # Mở kết nối DB.
    # Tạo con trỏ trả về kết quả dưới dạng dictionary.

    try:
        db.start_transaction()
        # Bắt đầu một transaction để đảm bảo các thao tác sau được thực hiện nguyên tử.

        cur.execute(
            # Truy vấn để lấy thông tin đăng ký và trạng thái lớp học phần liên quan.
            """
            SELECT e.*, cs.status AS section_status
            FROM enrollments e
            JOIN class_sections cs ON cs.id = e.section_id
            WHERE e.id = %s AND e.student_id = %s AND e.status = 'registered'
            FOR UPDATE
            """,
            (enrollment_id, student_id),
            # Truy vấn bản ghi đăng ký cụ thể đang ở trạng thái registered.
            # Đồng thời join với class_sections để lấy trạng thái lớp.
            # FOR UPDATE khóa dòng này để tránh race condition khi nhiều người sửa cùng lúc.
        )

        row = cur.fetchone()
        if not row:
            raise ApiError("Khong tim thay dang ky hop le.", 404)
        # Lấy kết quả.
        # Nếu không tìm được, ném lỗi API 404: không tìm thấy đăng ký hợp lệ.

        if not allow_locked and row["section_status"] != "open":
            raise ApiError("Lop da khoa, khong the huy dang ky.")
        # Nếu allow_locked=False và trạng thái lớp không phải là open, ném lỗi API: "Lop da khoa, khong the huy dang ky."
        
        cur.execute(
            """
            UPDATE enrollments
            SET status = 'cancelled', cancelled_at = NOW()
            WHERE id = %s
            """,
            (enrollment_id,),
        )
        # Cập nhật trạng thái đăng ký thành 'cancelled' và ghi thời gian hủy.

        cur.execute(
            """
            UPDATE class_sections
            SET enrolled_count = GREATEST(enrolled_count - 1, 0)
            WHERE id = %s
            """,
            (row["section_id"],),
        )
        # Cập nhật số lượng sinh viên đã đăng ký trong lớp học phần, đảm bảo không âm.
        # Giảm số lượng đăng ký của lớp đi 1.
        # Dùng GREATEST(..., 0) để đảm bảo không âm nếu có lỗi số học.
        
        db.commit() # Commit transaction nếu không có lỗi.

    except Exception:
        db.rollback()
        raise
    # Nếu bất kỳ lỗi nào xảy ra, rollback để không giữ trạng thái nửa vời.
    # Rethrow lỗi cho bên trên xử lý.

    finally:
        cur.close() # Đóng con trỏ sau khi xong.
