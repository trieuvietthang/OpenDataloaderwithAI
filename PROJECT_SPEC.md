# ĐẶC TẢ DỰ ÁN (PROJECT SPECIFICATION)

## 1. Tổng quan
- **Tên phần mềm:** LexGuard (Bộ Chuyển Đổi & Bảo Mật Tài Liệu PDF & DOCX) — trước đây tên là "OpenDataLoader PDF", đổi tên ở V2.2 để phản ánh đúng 2 trụ cột: xử lý tài liệu pháp lý (Lex) và bảo vệ dữ liệu cá nhân (Guard).
- **Phiên bản hiện tại:** V2.2
- **Mục tiêu:** Ứng dụng desktop chuyên nghiệp cho khối văn phòng (đặc biệt: Văn phòng Thừa phát lại) dùng để trích xuất, chuyển đổi định dạng tài liệu PDF, DOCX sang Markdown, HTML, Text, đồng thời ẩn thông tin cá nhân nhạy cảm khi cần.
- **Tính năng cốt lõi:**
  1. Trích xuất text thuần từ PDF/DOCX (dùng PyMuPDF, mammoth).
  2. OCR cục bộ: Sử dụng Tesseract OCR để nhận diện chữ từ ảnh (hỗ trợ tiếng Việt).
  3. OCR đám mây (Vision API): Xử lý bảng biểu, định dạng phức tạp với AI. Hỗ trợ đa dạng nền tảng: Google Gemini, OpenAI, Claude, OpenRouter.
  4. Docling OCR: OCR ngoại tuyến hiểu cấu trúc (Layout + TableFormer).
  5. Quản lý AI Profile: Lưu trữ nhiều cấu hình API khác nhau, kiểm tra kết nối API tức thì.
  6. Prompt Engineering: Tùy biến câu lệnh (prompt) dịch thuật/trích xuất theo ý muốn.
  7. Xử lý chính xác (Page Range): Cho phép chọn khoảng trang PDF (VD: 1-5, 10) để tiết kiệm thời gian và chi phí API.
  8. Xóa Watermark (2 chế độ: phẫu thuật vector + lọc pixel).
  9. **Ẩn thông tin định danh cá nhân (PII Redaction):** CCCD/CMND, SĐT, email, STK, MST, ngày sinh, biển số xe — theo Nghị định 13/2023/NĐ-CP; chế độ OCR AI còn ẩn thêm họ tên/địa chỉ.
  10. **Lịch sử xử lý:** Lưu lại các lần chuyển đổi (tên tệp, thời gian, định dạng, trạng thái, PII đã ẩn), xuất được báo cáo CSV.

## 2. Giao diện (UI/UX)
- **Công nghệ:** PySide6.
- **Phong cách:** Flat Design (Thiết kế phẳng), Hỗ trợ Light Theme & Dark Theme (Chuyển đổi nóng).
- **Bố cục (từ V2.2):** Cửa sổ chính chia 4 tab thay cho 1 trang cuộn dọc duy nhất trước đây:
  - **Chuyển đổi:** vùng thả tệp thu gọn + cấu hình theo từng lô (định dạng, chế độ OCR, trang trích xuất, watermark/PII nhanh) + nhật ký xử lý.
  - **Xem trước:** xem nội dung tệp vừa chuyển đổi dạng văn bản thô/markdown (không render HTML, tránh treo UI).
  - **Lịch sử:** bảng tra cứu các lần xử lý trước, kèm tổng hợp PII đã ẩn, xuất CSV.
  - **Cài đặt:** quản lý đầy đủ cấu hình AI Profile, tinh chỉnh watermark nâng cao, DPI/hiệu năng OCR, giao diện — thay cho hộp thoại nhỏ 700×500 trước đây.
- **Màu sắc Thương hiệu (Brand Colors - Light Mode):**
  - Màu nền (Background): Trắng / Xám nhạt sáng (`#f8fafc`, `#ffffff`)
  - Màu chủ đạo (Primary - Text/Buttons): Xanh đậm (`#2d3a8c`)
  - Màu cảnh báo/Hành động mạnh (Accent): Đỏ (`#e52b2d`)
  - Màu nhấn/Tiến độ (Highlight): Vàng (`#ffe700`)

## 3. Kiến trúc kỹ thuật
- **File chính:** `openloader.py` (Chứa toàn bộ UI và Logic).
- **Thành phần UI:** 
  - `MainWindow`: Cửa sổ chính, chứa `QTabWidget` (4 tab) và hệ thống đổi Theme. Các tab được dựng bằng các phương thức `_build_convert_tab`/`_build_preview_tab`/`_build_history_tab`/`_build_settings_tab`.
  - `FileDropZone`: Lớp tùy biến từ QFrame hỗ trợ nhận diện thao tác drag-and-drop.
- **Xử lý bất đồng bộ:** 
  - `ConversionWorker`: Kế thừa QThread. Xử lý các tác vụ nặng (chuyển đổi, OCR, gọi API) dưới background, phát tín hiệu `fileProcessed` sau mỗi tệp để cập nhật tab Lịch sử/Xem trước.
- **Lưu trữ cục bộ:** `config.json` (cấu hình + AI profiles), `lich_su.json` (lịch sử xử lý, tối đa 500 mục gần nhất).
- **Dependencies chính:** `PySide6`, `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`.
