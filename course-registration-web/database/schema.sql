CREATE DATABASE IF NOT EXISTS course_registration
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE course_registration;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS password_reset_logs;
DROP TABLE IF EXISTS completed_courses;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS class_sections;
DROP TABLE IF EXISTS course_prerequisites;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'student') NOT NULL DEFAULT 'student',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    student_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(160) NOT NULL,
    phone VARCHAR(30) NULL,
    gender ENUM('male', 'female', 'other') NOT NULL DEFAULT 'other',
    date_of_birth DATE NULL,
    major VARCHAR(160) NULL,
    class_name VARCHAR(80) NULL,
    CONSTRAINT fk_students_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(30) NOT NULL UNIQUE,
    course_name VARCHAR(180) NOT NULL,
    credits INT NOT NULL,
    tuition_per_credit DECIMAL(12,2) NOT NULL DEFAULT 0,
    description TEXT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_courses_credits CHECK (credits > 0),
    CONSTRAINT chk_courses_tuition CHECK (tuition_per_credit >= 0)
) ENGINE=InnoDB;

CREATE TABLE course_prerequisites (
    course_id INT NOT NULL,
    prerequisite_course_id INT NOT NULL,
    PRIMARY KEY (course_id, prerequisite_course_id),
    CONSTRAINT fk_prereq_course
        FOREIGN KEY (course_id) REFERENCES courses(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_prereq_required_course
        FOREIGN KEY (prerequisite_course_id) REFERENCES courses(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_prereq_not_self CHECK (course_id <> prerequisite_course_id)
) ENGINE=InnoDB;

CREATE TABLE class_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    section_code VARCHAR(40) NOT NULL UNIQUE,
    expected_class_code VARCHAR(40) NOT NULL,
    semester VARCHAR(30) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    day_of_week TINYINT NOT NULL,
    start_period TINYINT NOT NULL,
    end_period TINYINT NOT NULL,
    building VARCHAR(80) NULL,
    room VARCHAR(80) NULL,
    lecturer VARCHAR(160) NULL,
    max_capacity INT NOT NULL,
    enrolled_count INT NOT NULL DEFAULT 0,
    status ENUM('open', 'closed', 'cancelled') NOT NULL DEFAULT 'open',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sections_courses
        FOREIGN KEY (course_id) REFERENCES courses(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_sections_day CHECK (day_of_week BETWEEN 2 AND 8),
    CONSTRAINT chk_sections_period CHECK (start_period >= 1 AND end_period >= start_period),
    CONSTRAINT chk_sections_capacity CHECK (max_capacity > 0 AND enrolled_count >= 0 AND enrolled_count <= max_capacity)
) ENGINE=InnoDB;

CREATE TABLE enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tuition_fee DECIMAL(12,2) NOT NULL DEFAULT 0,
    payment_deadline DATE NULL,
    is_paid TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('registered', 'cancelled') NOT NULL DEFAULT 'registered',
    cancelled_at DATETIME NULL,
    CONSTRAINT fk_enrollments_students
        FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_enrollments_sections
        FOREIGN KEY (section_id) REFERENCES class_sections(id)
        ON DELETE RESTRICT,
    INDEX idx_enrollments_student_status (student_id, status),
    INDEX idx_enrollments_section_status (section_id, status)
) ENGINE=InnoDB;

CREATE TABLE completed_courses (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    completed_at DATE NULL,
    PRIMARY KEY (student_id, course_id),
    CONSTRAINT fk_completed_students
        FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_completed_courses
        FOREIGN KEY (course_id) REFERENCES courses(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE password_reset_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    delivered_to VARCHAR(120) NOT NULL,
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reset_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT INTO users (id, username, email, password_hash, role, is_active, created_at) VALUES
(1, 'admin', 'admin@ut.edu.vn', 'pbkdf2_sha256$260000$sS3q8CDVuNYs/MN5Dgoawg==$4K5PkF1Nmsw8cba+c8D3kD7B5GdeGZGGY7tnNigNdas=', 'admin', 1, NOW()),
(2, 'phongdaotao', 'phongdaotao@ut.edu.vn', 'pbkdf2_sha256$260000$sS3q8CDVuNYs/MN5Dgoawg==$4K5PkF1Nmsw8cba+c8D3kD7B5GdeGZGGY7tnNigNdas=', 'admin', 1, NOW()),
(3, '2251120001', 'antn0001@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(4, '2251120002', 'binhtv0002@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(5, '2251120003', 'chilt0003@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(6, '2251120004', 'dungpq0004@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(7, '2251120005', 'gianghm0005@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(8, '2251120006', 'hanhnt0006@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(9, '2251120007', 'khoavd0007@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(10, '2251120008', 'linhdb0008@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(11, '2251120009', 'minhbt0009@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(12, '2251120010', 'nhipy0010@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 1, NOW()),
(13, '2251120099', 'testnv0099@ut.edu.vn', 'pbkdf2_sha256$260000$8MjISRqB6cGttBx1qZFTtw==$U9GbGKIgGIEcWZDBLr0VMXk0CeNyE/+O6qcmCp302Ng=', 'student', 0, NOW());

INSERT INTO students
    (id, user_id, student_code, full_name, phone, gender, date_of_birth, major, class_name)
VALUES
(1, 3, '2251120001', 'Tran Nguyen Minh An', '0901000001', 'male', '2005-03-14', 'Cong nghe phan mem', 'CNPM01'),
(2, 4, '2251120002', 'Tran Van Binh', '0901000002', 'male', '2005-07-08', 'Cong nghe phan mem', 'CNPM01'),
(3, 5, '2251120003', 'Le Thi Mai Chi', '0901000003', 'female', '2005-01-21', 'Cong nghe phan mem', 'CNPM02'),
(4, 6, '2251120004', 'Pham Quoc Dung', '0901000004', 'male', '2004-11-09', 'He thong thong tin', 'HTTT01'),
(5, 7, '2251120005', 'Hoang Minh Giang', '0901000005', 'female', '2005-05-19', 'Mang may tinh', 'MMT01'),
(6, 8, '2251120006', 'Nguyen Thu Hanh', '0901000006', 'female', '2005-09-30', 'An toan thong tin', 'ATTT01'),
(7, 9, '2251120007', 'Vo Dang Khoa', '0901000007', 'male', '2004-12-12', 'Cong nghe phan mem', 'CNPM02'),
(8, 10, '2251120008', 'Do Bao Linh', '0901000008', 'female', '2005-04-02', 'Khoa hoc du lieu', 'KHDL01'),
(9, 11, '2251120009', 'Bui Thanh Minh', '0901000009', 'male', '2005-08-25', 'He thong thong tin', 'HTTT02'),
(10, 12, '2251120010', 'Phan Yen Nhi', '0901000010', 'female', '2005-06-17', 'Cong nghe phan mem', 'CNPM03'),
(11, 13, '2251120099', 'Nguyen Van Test', '0901000099', 'male', '2005-10-10', 'Tai khoan thu nghiem', 'TEST01');

INSERT INTO courses
    (id, course_code, course_name, credits, tuition_per_credit, description, is_active)
VALUES
(1, 'CS101', 'Nhap mon lap trinh', 3, 450000, 'Hoc phan nen tang ve tu duy lap trinh va cau truc chuong trinh.', 1),
(2, 'CS102', 'Cau truc du lieu va giai thuat', 3, 450000, 'Danh sach, ngan xep, hang doi, cay, do thi va cac giai thuat co ban.', 1),
(3, 'SE201', 'Cong nghe phan mem', 3, 500000, 'Quy trinh phat trien phan mem, phan tich yeu cau va mo hinh hoa UML.', 1),
(4, 'DB101', 'Co so du lieu', 3, 480000, 'Mo hinh quan he, SQL, thiet ke va toi uu co so du lieu.', 1),
(5, 'NET101', 'Mang may tinh', 2, 430000, 'Kien truc mang, TCP/IP, dinh tuyen va cac dich vu mang.', 1),
(6, 'AI101', 'Tri tue nhan tao nhap mon', 3, 520000, 'Tong quan ve AI, tim kiem, suy dien va ung dung hoc may co ban.', 1),
(7, 'WEB201', 'Lap trinh web', 3, 510000, 'HTML, CSS, JavaScript, Flask API va ket noi co so du lieu.', 1),
(8, 'OS201', 'He dieu hanh', 3, 470000, 'Tien trinh, bo nho, he thong tep va co che dieu phoi CPU.', 1),
(9, 'MATH101', 'Toan roi rac', 3, 420000, 'Logic, tap hop, quan he, do thi va to hop cho tin hoc.', 1),
(10, 'ENG101', 'Tieng Anh chuyen nganh CNTT', 2, 380000, 'Tu vung va ky nang doc hieu tai lieu ky thuat CNTT.', 1),
(11, 'PM301', 'Quan ly du an phan mem', 2, 500000, 'Lap ke hoach, theo doi tien do, quan tri rui ro va giao tiep du an.', 1),
(12, 'SEC201', 'An toan bao mat thong tin', 3, 530000, 'Ma hoa, xac thuc, bao mat ung dung va quan tri rui ro an ninh.', 1),
(13, 'MOB201', 'Lap trinh ung dung di dong', 3, 520000, 'Phat trien ung dung mobile, giao dien va ket noi API.', 1),
(14, 'CLOUD301', 'Dien toan dam may', 3, 560000, 'Trien khai dich vu, container, luu tru va mo hinh ha tang dam may.', 1),
(15, 'IOT201', 'Internet van vat', 3, 540000, 'Cam bien, giao thuc IoT, gateway va ung dung thuc te.', 1);

INSERT INTO course_prerequisites (course_id, prerequisite_course_id) VALUES
(2, 1),
(4, 1),
(3, 2),
(6, 2),
(6, 9),
(7, 1),
(8, 2),
(11, 3),
(12, 5),
(13, 7),
(14, 5),
(14, 8),
(15, 5);

INSERT INTO completed_courses (student_id, course_id, completed_at) VALUES
(1, 1, '2026-01-15'),
(1, 9, '2026-01-15'),
(2, 1, '2026-01-15'),
(2, 2, '2026-01-15'),
(2, 4, '2026-01-15'),
(2, 5, '2026-01-15'),
(2, 7, '2026-01-15'),
(2, 9, '2026-01-15'),
(3, 1, '2026-01-15'),
(4, 1, '2026-01-15'),
(4, 2, '2026-01-15'),
(4, 3, '2026-01-15'),
(4, 9, '2026-01-15'),
(5, 9, '2026-01-15'),
(6, 1, '2026-01-15'),
(6, 2, '2026-01-15'),
(6, 5, '2026-01-15'),
(7, 1, '2026-01-15'),
(7, 2, '2026-01-15'),
(7, 5, '2026-01-15'),
(7, 7, '2026-01-15'),
(7, 8, '2026-01-15'),
(8, 1, '2026-01-15'),
(8, 9, '2026-01-15'),
(9, 1, '2026-01-15'),
(9, 2, '2026-01-15'),
(10, 1, '2026-01-15'),
(10, 2, '2026-01-15'),
(10, 3, '2026-01-15');

INSERT INTO class_sections
    (id, course_id, section_code, expected_class_code, semester, academic_year,
     day_of_week, start_period, end_period, building, room, lecturer,
     max_capacity, enrolled_count, status)
VALUES
(1, 1, 'CS101-01', 'CNPM01', 'HK1', '2026-2027', 2, 1, 3, 'A', 'A101', 'Tran Thi My Tien', 35, 1, 'open'),
(2, 1, 'CS101-02', 'CNPM02', 'HK1', '2026-2027', 4, 4, 6, 'A', 'A104', 'Tran Thi My Tien', 35, 1, 'open'),
(3, 1, 'CS101-03', 'CNPM03', 'HK1', '2026-2027', 6, 1, 3, 'A', 'A105', 'Tran Thi My Tien', 35, 0, 'closed'),
(4, 2, 'CS102-01', 'CNPM01', 'HK1', '2026-2027', 3, 1, 3, 'A', 'A102', 'Nguyen Van Nam', 35, 0, 'open'),
(5, 2, 'CS102-02', 'CNPM02', 'HK1', '2026-2027', 5, 4, 6, 'A', 'A103', 'Nguyen Van Nam', 3, 2, 'open'),
(6, 3, 'SE201-01', 'CNPM01', 'HK1', '2026-2027', 3, 2, 4, 'B', 'B201', 'Le Minh Chau', 35, 1, 'open'),
(7, 3, 'SE201-02', 'CNPM03', 'HK1', '2026-2027', 6, 7, 9, 'B', 'B205', 'Le Minh Chau', 35, 1, 'closed'),
(8, 4, 'DB101-01', 'CNPM01', 'HK1', '2026-2027', 5, 4, 6, 'B', 'B202', 'Pham Anh Thu', 2, 2, 'open'),
(9, 4, 'DB101-02', 'CNPM02', 'HK1', '2026-2027', 7, 1, 3, 'B', 'B203', 'Pham Anh Thu', 35, 0, 'cancelled'),
(10, 5, 'NET101-01', 'MMT01', 'HK1', '2026-2027', 4, 1, 3, 'C', 'C301', 'Vo Quoc Viet', 40, 1, 'open'),
(11, 5, 'NET101-02', 'MMT02', 'HK1', '2026-2027', 2, 7, 8, 'C', 'C303', 'Vo Quoc Viet', 40, 1, 'open'),
(12, 6, 'AI101-01', 'KHDL01', 'HK1', '2026-2027', 5, 2, 4, 'C', 'C302', 'Hoang Minh Quan', 40, 1, 'open'),
(13, 6, 'AI101-02', 'KHDL02', 'HK1', '2026-2027', 6, 4, 6, 'C', 'C304', 'Hoang Minh Quan', 40, 0, 'closed'),
(14, 7, 'WEB201-01', 'CNPM01', 'HK1', '2026-2027', 3, 7, 9, 'D', 'D401', 'Do Thanh Phong', 35, 1, 'open'),
(15, 7, 'WEB201-02', 'CNPM02', 'HK1', '2026-2027', 5, 1, 3, 'D', 'D402', 'Do Thanh Phong', 35, 1, 'open'),
(16, 8, 'OS201-01', 'HTTT01', 'HK1', '2026-2027', 2, 4, 6, 'E', 'E501', 'Nguyen Hoai Nam', 35, 1, 'open'),
(17, 12, 'SEC201-01', 'ATTT01', 'HK1', '2026-2027', 4, 4, 6, 'E', 'E502', 'Le Bao Chau', 35, 1, 'open'),
(18, 13, 'MOB201-01', 'CNPM02', 'HK1', '2026-2027', 6, 1, 3, 'F', 'F601', 'Tran Duc Anh', 35, 1, 'open'),
(19, 14, 'CLOUD301-01', 'HTTT02', 'HK1', '2026-2027', 7, 4, 6, 'F', 'F602', 'Vo Minh Quan', 35, 1, 'open'),
(20, 9, 'MATH101-01', 'DAICUONG', 'HK1', '2026-2027', 2, 1, 3, 'G', 'G701', 'Pham Thanh Tung', 60, 0, 'open'),
(21, 10, 'ENG101-01', 'DAICUONG', 'HK1', '2026-2027', 3, 10, 11, 'G', 'G702', 'Nguyen Kim Anh', 60, 1, 'open'),
(22, 11, 'PM301-01', 'CNPM03', 'HK1', '2026-2027', 4, 7, 9, 'H', 'H801', 'Tran Mai Linh', 35, 1, 'open'),
(23, 15, 'IOT201-01', 'MMT01', 'HK1', '2026-2027', 5, 7, 9, 'H', 'H802', 'Dang Quoc Viet', 35, 0, 'open');

INSERT INTO enrollments
    (id, student_id, section_id, registered_at, tuition_fee, payment_deadline, is_paid, status, cancelled_at)
VALUES
(1, 1, 10, DATE_SUB(NOW(), INTERVAL 9 DAY), 860000, DATE_ADD(CURDATE(), INTERVAL 21 DAY), 0, 'registered', NULL),
(2, 1, 21, DATE_SUB(NOW(), INTERVAL 8 DAY), 760000, DATE_ADD(CURDATE(), INTERVAL 22 DAY), 1, 'registered', NULL),
(3, 2, 8, DATE_SUB(NOW(), INTERVAL 11 DAY), 1440000, DATE_ADD(CURDATE(), INTERVAL 19 DAY), 1, 'registered', NULL),
(4, 2, 12, DATE_SUB(NOW(), INTERVAL 10 DAY), 1560000, DATE_ADD(CURDATE(), INTERVAL 20 DAY), 0, 'registered', NULL),
(5, 2, 14, DATE_SUB(NOW(), INTERVAL 7 DAY), 1530000, DATE_ADD(CURDATE(), INTERVAL 23 DAY), 1, 'registered', NULL),
(6, 3, 5, DATE_SUB(NOW(), INTERVAL 6 DAY), 1350000, DATE_ADD(CURDATE(), INTERVAL 24 DAY), 0, 'registered', NULL),
(7, 3, 11, DATE_SUB(NOW(), INTERVAL 6 DAY), 860000, DATE_ADD(CURDATE(), INTERVAL 24 DAY), 0, 'registered', NULL),
(8, 4, 6, DATE_SUB(NOW(), INTERVAL 5 DAY), 1500000, DATE_ADD(CURDATE(), INTERVAL 25 DAY), 1, 'registered', NULL),
(9, 4, 22, DATE_SUB(NOW(), INTERVAL 5 DAY), 1000000, DATE_ADD(CURDATE(), INTERVAL 25 DAY), 0, 'registered', NULL),
(10, 5, 1, DATE_SUB(NOW(), INTERVAL 4 DAY), 1350000, DATE_ADD(CURDATE(), INTERVAL 26 DAY), 0, 'registered', NULL),
(11, 6, 17, DATE_SUB(NOW(), INTERVAL 4 DAY), 1590000, DATE_ADD(CURDATE(), INTERVAL 26 DAY), 0, 'registered', NULL),
(12, 6, 5, DATE_SUB(NOW(), INTERVAL 3 DAY), 1350000, DATE_ADD(CURDATE(), INTERVAL 27 DAY), 1, 'registered', NULL),
(13, 7, 19, DATE_SUB(NOW(), INTERVAL 3 DAY), 1680000, DATE_ADD(CURDATE(), INTERVAL 27 DAY), 0, 'registered', NULL),
(14, 7, 18, DATE_SUB(NOW(), INTERVAL 2 DAY), 1560000, DATE_ADD(CURDATE(), INTERVAL 28 DAY), 1, 'registered', NULL),
(15, 8, 8, DATE_SUB(NOW(), INTERVAL 2 DAY), 1440000, DATE_ADD(CURDATE(), INTERVAL 28 DAY), 0, 'registered', NULL),
(16, 9, 15, DATE_SUB(NOW(), INTERVAL 1 DAY), 1530000, DATE_ADD(CURDATE(), INTERVAL 29 DAY), 0, 'registered', NULL),
(17, 9, 16, DATE_SUB(NOW(), INTERVAL 1 DAY), 1410000, DATE_ADD(CURDATE(), INTERVAL 29 DAY), 1, 'registered', NULL),
(18, 10, 7, DATE_SUB(NOW(), INTERVAL 1 DAY), 1500000, DATE_ADD(CURDATE(), INTERVAL 29 DAY), 0, 'registered', NULL),
(19, 10, 2, NOW(), 1350000, DATE_ADD(CURDATE(), INTERVAL 30 DAY), 1, 'registered', NULL),
(20, 1, 3, DATE_SUB(NOW(), INTERVAL 20 DAY), 1350000, DATE_ADD(CURDATE(), INTERVAL 10 DAY), 0, 'cancelled', DATE_SUB(NOW(), INTERVAL 18 DAY)),
(21, 3, 2, DATE_SUB(NOW(), INTERVAL 19 DAY), 1350000, DATE_ADD(CURDATE(), INTERVAL 11 DAY), 0, 'cancelled', DATE_SUB(NOW(), INTERVAL 17 DAY)),
(22, 5, 20, DATE_SUB(NOW(), INTERVAL 18 DAY), 1260000, DATE_ADD(CURDATE(), INTERVAL 12 DAY), 0, 'cancelled', DATE_SUB(NOW(), INTERVAL 16 DAY)),
(23, 8, 9, DATE_SUB(NOW(), INTERVAL 18 DAY), 1440000, DATE_ADD(CURDATE(), INTERVAL 12 DAY), 0, 'cancelled', DATE_SUB(NOW(), INTERVAL 16 DAY));
