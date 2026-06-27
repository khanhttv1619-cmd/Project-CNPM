-- ====================================================
-- SCRIPT KHỞI TẠO CƠ SỞ DỮ LIỆU ĐĂNG KÝ HỌC PHẦN
-- Dự án: Course Registration System - Nhóm 01 (UTH)
-- ====================================================

-- 1. Xóa Database nếu đã tồn tại và tạo mới
DROP DATABASE IF EXISTS CourseRegDB;
CREATE DATABASE CourseRegDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE CourseRegDB;

-- 2. Tạo bảng User (Tài khoản người dùng)
CREATE TABLE User (
    userID INT AUTO_INCREMENT PRIMARY KEY,
    userName VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL
);

-- 3. Tạo bảng Student (Thông tin sinh viên)
CREATE TABLE Student (
    studentID VARCHAR(20) PRIMARY KEY,
    userID INT,
    studentName VARCHAR(50),
    email VARCHAR(50),
    phone VARCHAR(20),
    gender VARCHAR(10),
    birthdate DATE,
    major VARCHAR(50),
    className VARCHAR(20),
    FOREIGN KEY (userID) REFERENCES User(userID) ON DELETE CASCADE
);

-- 4. Tạo bảng Courses (Danh mục Môn học)
CREATE TABLE Courses (
    courseCode VARCHAR(20) PRIMARY KEY,
    courseName VARCHAR(100),
    credit INT,
    fee DECIMAL(10, 0),
    prerequisites VARCHAR(50)
);

-- 5. Tạo bảng ClassSection (Danh sách Lớp học phần)
CREATE TABLE ClassSection (
    sectionCode VARCHAR(20) PRIMARY KEY,
    courseCode VARCHAR(20),
    schedule VARCHAR(50),
    room VARCHAR(20),
    maxEnroll INT,
    currentEnroll INT,
    status VARCHAR(20),
    FOREIGN KEY (courseCode) REFERENCES Courses(courseCode) ON DELETE CASCADE
);

-- 6. Tạo bảng Enrollment (Lịch sử Đăng ký & Học phí)
CREATE TABLE Enrollment (
    enrollID INT AUTO_INCREMENT PRIMARY KEY,
    studentID VARCHAR(20),
    sectionCode VARCHAR(20),
    feeCollectionStatus BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (studentID) REFERENCES Student(studentID) ON DELETE CASCADE,
    FOREIGN KEY (sectionCode) REFERENCES ClassSection(sectionCode) ON DELETE CASCADE
);

-- ====================================================
-- CHÈN DỮ LIỆU MẪU (SEED DATA)
-- ====================================================

-- Chèn tài khoản Admin (Mật khẩu: admin123)
INSERT INTO User (userName, password, role) VALUES ('admin@ut.edu.vn', 'admin123', 'admin');

-- Chèn 10 tài khoản Sinh viên (Mật khẩu mặc định: 123456)
INSERT INTO User (userName, password, role) VALUES
('2251120001', '123456', 'student'),
('2251120002', '123456', 'student'),
('2251120003', '123456', 'student'),
('2251120004', '123456', 'student'),
('2251120005', '123456', 'student'),
('2251120006', '123456', 'student'),
('2251120007', '123456', 'student'),
('2251120008', '123456', 'student'),
('2251120009', '123456', 'student'),
('2251120010', '123456', 'student');

-- Chèn thông tin cá nhân của 10 Sinh viên (Khớp với userID từ 2 đến 11)
INSERT INTO Student (studentID, userID, studentName, email, phone, gender, birthdate, major, className) VALUES
('2251120001', 2, 'Trần Nguyễn Minh An', 'antnm0001@ut.edu.vn', '0901111111', 'Nam', '2004-01-15', 'CNPM', 'CNPM01'),
('2251120002', 3, 'Lê Hoàng Bảo', 'baolh0002@ut.edu.vn', '0902222222', 'Nam', '2004-03-22', 'CNPM', 'CNPM01'),
('2251120003', 4, 'Phạm Thị Cẩm', 'campt0003@ut.edu.vn', '0903333333', 'Nữ', '2004-05-10', 'HTTT', 'HTTT01'),
('2251120004', 5, 'Vũ Đức Duy', 'duyvd0004@ut.edu.vn', '0904444444', 'Nam', '2004-07-08', 'KHMT', 'KHMT01'),
('2251120005', 6, 'Ngô Hải Yến', 'yennh0005@ut.edu.vn', '0905555555', 'Nữ', '2004-09-12', 'CNPM', 'CNPM02'),
('2251120006', 7, 'Đinh Văn Phong', 'phongdv0006@ut.edu.vn', '0906666666', 'Nam', '2004-11-20', 'HTTT', 'HTTT02'),
('2251120007', 8, 'Bùi Thanh Thảo', 'thaobt0007@ut.edu.vn', '0907777777', 'Nữ', '2004-12-05', 'KHMT', 'KHMT02'),
('2251120008', 9, 'Lý Trọng Tín', 'tinlt0008@ut.edu.vn', '0908888888', 'Nam', '2004-02-28', 'CNPM', 'CNPM01'),
('2251120009', 10, 'Hồ Mỹ Nhàn', 'nhanhm0009@ut.edu.vn', '0909999999', 'Nữ', '2004-06-16', 'HTTT', 'HTTT01'),
('2251120010', 11, 'Châu Phát Tài', 'taicp0010@ut.edu.vn', '0900000000', 'Nam', '2004-10-30', 'KHMT', 'KHMT01');

-- Chèn dữ liệu 12 Môn học
INSERT INTO Courses (courseCode, courseName, credit, fee, prerequisites) VALUES
('CS101', 'Nhập môn lập trình', 3, 450000, 'Khong'),
('CS102', 'Cấu trúc dữ liệu và giải thuật', 3, 450000, 'CS101'),
('CS201', 'Cơ sở dữ liệu', 3, 450000, 'CS102'),
('CS202', 'Mạng máy tính', 3, 450000, 'CS101'),
('SE101', 'Công nghệ phần mềm', 3, 500000, 'CS201'),
('AI101', 'Trí tuệ nhân tạo nhập môn', 3, 550000, 'CS102, MATH101'),
('AI102', 'Học máy (Machine Learning)', 3, 550000, 'AI101'),
('MATH101', 'Toán rời rạc', 3, 400000, 'Khong'),
('MATH102', 'Đại số tuyến tính', 3, 400000, 'Khong'),
('ENG101', 'Tiếng Anh chuyên ngành 1', 2, 350000, 'Khong'),
('ENG102', 'Tiếng Anh chuyên ngành 2', 2, 350000, 'ENG101'),
('PHY101', 'Vật lý đại cương', 3, 420000, 'Khong');

-- Chèn dữ liệu Lớp học phần (Lưu ý: currentEnroll đã được đếm sẵn dựa trên số sinh viên sẽ được đăng ký bên dưới)
INSERT INTO ClassSection (sectionCode, courseCode, schedule, room, maxEnroll, currentEnroll, status) VALUES
('CS101-01', 'CS101', 'Thứ 2, tiết 1-3', 'A101', 40, 2, 'Mở đăng ký'),
('CS101-02', 'CS101', 'Thứ 2, tiết 4-6', 'A102', 40, 1, 'Mở đăng ký'),
('CS101-03', 'CS101', 'Thứ 3, tiết 7-9', 'A103', 40, 0, 'Mở đăng ký'),
('CS102-01', 'CS102', 'Thứ 4, tiết 1-3', 'B201', 40, 0, 'Mở đăng ký'),
('CS102-02', 'CS102', 'Thứ 5, tiết 10-12', 'B202', 40, 0, 'Mở đăng ký'),
('CS201-01', 'CS201', 'Thứ 6, tiết 1-3', 'C301', 40, 0, 'Mở đăng ký'),
('CS202-01', 'CS202', 'Thứ 7, tiết 4-6', 'C302', 40, 0, 'Mở đăng ký'),
('SE101-01', 'SE101', 'Thứ 2, tiết 7-9', 'D401', 30, 0, 'Mở đăng ký'),
('SE101-02', 'SE101', 'Thứ 3, tiết 1-3', 'D402', 30, 0, 'Mở đăng ký'),
('AI101-01', 'AI101', 'Thứ 4, tiết 7-9', 'E501', 35, 0, 'Mở đăng ký'),
('AI102-01', 'AI102', 'Thứ 5, tiết 4-6', 'E502', 35, 0, 'Mở đăng ký'),
('MATH101-01', 'MATH101', 'Thứ 2, tiết 10-12', 'F601', 50, 1, 'Mở đăng ký'),
('MATH101-02', 'MATH101', 'Thứ 3, tiết 4-6', 'F602', 50, 1, 'Mở đăng ký'),
('MATH102-01', 'MATH102', 'Thứ 6, tiết 7-9', 'F603', 50, 0, 'Mở đăng ký'),
('ENG101-01', 'ENG101', 'Thứ 4, tiết 1-3', 'G701', 45, 1, 'Mở đăng ký'),
('ENG101-02', 'ENG101', 'Thứ 5, tiết 1-3', 'G702', 45, 0, 'Mở đăng ký'),
('ENG102-01', 'ENG102', 'Thứ 6, tiết 4-6', 'G703', 45, 0, 'Mở đăng ký'),
('PHY101-01', 'PHY101', 'Thứ 7, tiết 1-3', 'H801', 60, 2, 'Mở đăng ký');

-- Chèn dữ liệu Đăng ký ảo (Mock Enrollments) cho sinh viên test
INSERT INTO Enrollment (studentID, sectionCode, feeCollectionStatus) VALUES
-- SV 0001 (Chưa đóng học phí)
('2251120001', 'CS101-01', FALSE),
('2251120001', 'MATH101-01', FALSE),
-- SV 0002 (Đã đóng học phí)
('2251120002', 'CS101-01', TRUE),
('2251120002', 'PHY101-01', TRUE),
-- SV 0003 (Chưa đóng học phí)
('2251120003', 'ENG101-01', FALSE),
-- SV 0004 (Đã đóng học phí full 3 môn)
('2251120004', 'CS101-02', TRUE),
('2251120004', 'MATH101-02', TRUE),
('2251120004', 'PHY101-01', TRUE);