# ĐẶC TẢ DỰ ÁN (PROJECT SPECIFICATION)

## 1. Tổng quan
- **Tên phần mềm:** OpenDataLoader PDF (Bộ Chuyển Đổi Tài Liệu PDF & DOCX)
- **Phiên bản hiện tại:** V2.0 (Pro Edition)
- **Mục tiêu:** Ứng dụng desktop chuyên nghiệp cho khối văn phòng (đặc biệt: Văn phòng Thừa phát lại) dùng để trích xuất, chuyển đổi định dạng tài liệu PDF, DOCX sang Markdown, HTML, Text.
- **Tính năng cốt lõi:**
  1. Trích xuất text thuần từ PDF/DOCX (dùng PyMuPDF, mammoth).
  2. OCR cục bộ: Sử dụng Tesseract OCR để nhận diện chữ từ ảnh (hỗ trợ tiếng Việt).
  3. OCR đám mây (Vision API): Xử lý bảng biểu, định dạng phức tạp với AI. Hỗ trợ đa dạng nền tảng: Google Gemini, OpenAI, Claude, OpenRouter.
  4. Quản lý AI Profile: Lưu trữ nhiều cấu hình API khác nhau, kiểm tra kết nối API tức thì.
  5. Prompt Engineering: Tùy biến câu lệnh (prompt) dịch thuật/trích xuất theo ý muốn.
  6. Xử lý chính xác (Page Range): Cho phép chọn khoảng trang PDF (VD: 1-5, 10) để tiết kiệm thời gian và chi phí API.

## 2. Giao diện (UI/UX)
- **Công nghệ:** PySide6.
- **Phong cách:** Flat Design (Thiết kế phẳng), Hỗ trợ Light Theme & Dark Theme (Chuyển đổi nóng).
- **Màu sắc Thương hiệu (Brand Colors - Light Mode):**
  - Màu nền (Background): Trắng / Xám nhạt sáng (`#f8fafc`, `#ffffff`)
  - Màu chủ đạo (Primary - Text/Buttons): Xanh đậm (`#2d3a8c`)
  - Màu cảnh báo/Hành động mạnh (Accent): Đỏ (`#e52b2d`)
  - Màu nhấn/Tiến độ (Highlight): Vàng (`#ffe700`)
- **Trình Xem Trước (Preview):** Tích hợp QTextBrowser render HTML Markdown để xem trước kết quả trực tiếp.

## 3. Kiến trúc kỹ thuật
- **File chính:** `openloader.py` (Chứa toàn bộ UI và Logic).
- **Thành phần UI:** 
  - `MainWindow`: Cửa sổ chính chứa hệ thống đổi Theme.
  - `SettingsDialog`: Hộp thoại quản lý Cấu hình hệ thống và AI.
  - `FileDropZone`: Lớp tùy biến từ QFrame hỗ trợ nhận diện thao tác drag-and-drop.
- **Xử lý bất đồng bộ:** 
  - `ConversionWorker`: Kế thừa QThread. Xử lý các tác vụ nặng (chuyển đổi, OCR, gọi API) dưới background.
- **Dependencies chính:** `PySide6`, `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`.
