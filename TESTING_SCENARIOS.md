# KỊCH BẢN KIỂM THỬ (TESTING SCENARIOS)

Dưới đây là các kịch bản kiểm thử cốt lõi (Core Test Scenarios) mà AI và Người dùng cần thực hiện để đảm bảo tính ổn định của phần mềm.

## Kịch bản 1: Kiểm tra tính ổn định của luồng OCR với API Cloud (Gemini)
**Mục đích:** Xác minh ứng dụng có thể gửi ảnh lên Gemini, xử lý phản hồi, và không bị đơ giao diện.
- **Bước 1:** Khởi chạy phần mềm.
- **Bước 2:** Kéo & thả 1 tệp PDF (có chứa hình ảnh hoặc scan).
- **Bước 3:** Nhập API Key hợp lệ của Gemini. Chọn Phương thức OCR là "Gemini AI (Chính xác cao)".
- **Bước 4:** Bấm "CHUYỂN ĐỔI".
- **Kết quả mong đợi (Expected):**
  - Thanh tiến độ chạy mượt mà, log hiển thị trạng thái đang xử lý từng trang.
  - Sau khi xong, thư mục đầu ra chứa file `.md` với nội dung text được bảo toàn định dạng, tiếng Việt không bị lỗi font chữ.

## Kịch bản 2: Kiểm tra khả năng chịu lỗi (Fault Tolerance) & Tự động thử lại
**Mục đích:** Đảm bảo ứng dụng không bị Crash (văng) khi gặp lỗi bên thứ 3 (API quá tải hoặc Tesseract mất dữ liệu).
- **Bước 1:** Chuẩn bị 1 API Key bị sai hoặc tắt mạng internet (để giả lập lỗi 503 / 500 / Network Error).
- **Bước 2:** Chạy tiến trình chuyển đổi bằng Gemini.
- **Kết quả mong đợi:**
  - Ứng dụng ghi nhận lỗi trong Nhật ký, tự động thử lại (Retry) 3 lần với thời gian chờ tăng dần (Exponential backoff: 2s -> 4s -> 8s).
  - Kết thúc 3 lần, nếu vẫn lỗi, phần mềm báo thất bại rõ ràng (Chữ đỏ), tổng kết (0/1 tệp thành công) và không bị crash app.

## Yêu cầu đối với AI
- AI cần chủ động giả lập môi trường hoặc đọc log đầu ra để xác minh Kịch bản 2 đã qua (Pass) trước khi yêu cầu người dùng thao tác.
- Luôn mở sẵn ứng dụng cho người dùng để test Kịch bản 1.
