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
6. [x] **Xóa Watermark & Tiền Xử Lý (Đột phá - Tiên tiến)**:
   - **Xóa mác OCG Layer:** Tích hợp tính năng xóa Watermark ẩn với `pikepdf`.
   - **Lọc Pixel Phân Loại (Tùy chọn 2 nhánh):** Xây dựng thuật toán phân loại và tách nhánh xử lý cho 2 nhóm Watermark khác nhau:
     - *Chế độ cơ bản:* Dành cho Watermark xám/nhỏ, lọc gắt (ngưỡng 130) kết hợp Morphology nhẹ giữ nét chữ cực kỳ sắc bén và thanh mảnh.
     - *Chế độ bảo vệ nét giao cắt:* Dành cho Watermark đục/to/màu. Áp dụng kỹ thuật ép tương phản (Contrast 2.0) để đẩy các điểm giao cắt về màu đen, kết hợp với ngưỡng bảo vệ cao (160) giúp phục hồi chữ bị đứt lấp hoàn hảo mà không để lại vệt trắng.
   - **Phẫu Thuật Mã Nguồn (Vector-Level Diagonal Surgery):** Can thiệp thẳng vào mảng `\Contents` của PDF (thông qua luồng Regex) để săn tìm và tiêu diệt các khối chữ được vẽ chéo (bằng ma trận `Tm`), xóa Watermark từ trong trứng nước trước cả khi PDF biến thành ảnh (Rasterization). Giúp bảo toàn nét 100%.
   - **Nén dung lượng siêu nhỏ:** Kết hợp định dạng ảnh 1-bit Monochrome với chuẩn nén CCITT Group 4 của định dạng TIFF, sau đó nhúng ngược lại vào PDF, giúp giảm dung lượng đầu ra cực sâu so với ảnh gốc, tối ưu tối đa cho lưu trữ.
7. [x] **Đóng gói (Packaging)**:
   - Biên dịch thành công ứng dụng ra file `.exe` bằng PyInstaller (Chế độ `--onedir`).

### Hạng mục tiếp theo (To-do / Backlog):
- [ ] Bổ sung kịch bản tự động hóa Unit Test (PyTest).
- [ ] Cải thiện hiển thị thanh tiến độ xử lý trang song song (Multi-threading cho từng trang).
- [ ] Đóng gói lại thành file `.exe` phiên bản V2 (Sau khi người dùng hoàn tất kiểm thử nội bộ).
