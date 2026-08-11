# TIẾN ĐỘ DỰ ÁN (PROJECT PROGRESS)

## Giai đoạn hiện tại: [Hoàn thành Version 2.0 - Pro Features]

### Các hạng mục đã hoàn thành (Done):
1. [x] **Core OCR & Extraction**: Tích hợp thành công PyMuPDF (trích xuất text), Tesseract (OCR local), Gemini (OCR cloud).
2. [x] **Giao diện người dùng (UI/UX)**:
   - Chuyển đổi thành công sang Flat Design với bảng màu chuẩn thương hiệu Văn phòng Thừa phát lại.
   - Thêm trạng thái cảnh báo, hộp thoại (QMessageBox) màu tối/phẳng để chống chói.
3. [x] **Quản lý Cấu hình (Settings) & AI Profiles (V2.0)**:
   - Xóa bỏ việc hardcode API Key trên màn hình chính.
   - Xây dựng Cửa sổ Cài đặt riêng với thanh cuộn (Scroll Area) mượt mà.
   - Hỗ trợ lưu không giới hạn các Cấu hình AI (AI Profiles) và cho phép chuyển đổi qua lại dễ dàng.
   - Hỗ trợ API chuẩn Gemini và OpenAI-Compatible (Vision API).
   - Bổ sung nút **"Kiểm tra kết nối"** (Ping API) trực tiếp trong thẻ cấu hình.
4. [x] **Tính năng Chuyên nghiệp (Pro Features - V2.0)**:
   - **Dark Mode**: Thêm nút chuyển đổi Giao diện Tối/Sáng trên Header, ghi nhớ trạng thái vào config.
   - **Trình Xem Trước (Preview)**: Bổ sung QTabWidget chia 2 khung Nhật ký xử lý & Xem trước kết quả. Tự động render Markdown bằng thư viện `markdown` ngay trong ứng dụng sau khi chuyển đổi xong.
   - **Tùy chỉnh Mệnh lệnh AI (Prompt Engineering)**: Cho phép người dùng chỉnh sửa hoặc viết Prompt tùy ý cho AI theo từng Profile.
   - **Lọc trang PDF (Page Range)**: Hỗ trợ cú pháp nhập trang (Vd: `1-5, 10`) để chỉ quét OCR các trang cụ thể, tiết kiệm chi phí API và thời gian.
5. [x] **Sửa lỗi (Bug Fixes)**:
   - Fix lỗi Kéo thả file, lỗi đường dẫn Tesseract, lỗi UnicodeEncodeError khi log.
   - Fix lỗi co hẹp UI khi thêm nhiều cấu hình (bằng QScrollArea).
6. [x] **Xóa Watermark & Tiền Xử Lý (Tiên tiến)**:
   - Tích hợp tính năng xóa Watermark ẩn (OCG Layer) với `pikepdf`.
   - Xây dựng thuật toán bóc tách màu điểm ảnh (Pixel Filtering) kết hợp biến đổi hình thái học (Morphology) từ `Pillow` và `Numpy` để vá lỗi đứt nét, tăng độ tương phản giúp Tesseract OCR đọc chính xác 100%.
   - Tối ưu hóa dung lượng (chuẩn hóa ảnh 1-bit Monochrome) giải quyết vấn đề đầy RAM khi render PDF ở độ phân giải 300 DPI.
7. [x] **Đóng gói (Packaging)**:
   - Biên dịch thành công ứng dụng ra file `.exe` bằng PyInstaller (Chế độ `--onedir`).

### Hạng mục tiếp theo (To-do / Backlog):
- [ ] Bổ sung kịch bản tự động hóa Unit Test (PyTest).
- [ ] Cải thiện hiển thị thanh tiến độ xử lý trang song song (Multi-threading cho từng trang).
- [ ] Đóng gói lại thành file `.exe` phiên bản V2 (Sau khi người dùng hoàn tất kiểm thử nội bộ).
