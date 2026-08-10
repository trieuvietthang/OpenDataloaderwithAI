# AI CODING RULES & WORKFLOW GUIDELINES

Tệp này định nghĩa các quy tắc bắt buộc (Mandatory Rules) dành cho các Agent AI khi làm việc với dự án OpenDataLoader PDF.

## 1. Context Retrieval (Lấy Context)
Mỗi khi bắt đầu một phiên nói chuyện mới, AI **PHẢI** tự động sử dụng công cụ để đọc các tệp sau trước khi trả lời người dùng hoặc sửa code:
1. `PROJECT_SPEC.md`: Để hiểu chức năng, kiến trúc, và màu sắc giao diện phần mềm.
2. `PROGRESS.md`: Để biết dự án đang ở giai đoạn nào, các lỗi nào đã được fix, tránh lặp lại công việc đã hoàn thành.
3. `TESTING_SCENARIOS.md`: Để hiểu cách kiểm thử hệ thống.

## 2. Quy tắc Coding (Coding Rules)
- **UI/UX Consistency**: Luôn duy trì phong cách Flat Design. Bất kỳ widget mới nào được thêm vào đều phải tuân thủ bảng màu ở `PROJECT_SPEC.md` (Xanh đậm `#2d3a8c`, Đỏ `#e52b2d`, Vàng `#ffe700`).
- **Thread Safety**: KHÔNG BAO GIỜ được gọi các tác vụ chặn (blocking tasks) như I/O, OCR, hoặc network request trên Main Thread (GUI Thread). Mọi tác vụ xử lý phải đẩy vào `ConversionWorker`.
- **Lập trình an toàn (Defensive Programming)**: Khi giao tiếp với các APIs bên ngoài (như Gemini AI) hoặc gọi subprocess (như Tesseract), luôn phải có cơ chế `try...except`, in log lỗi rõ ràng tiếng Anh (để tránh lỗi mã hóa Unicode trên Windows) và có cơ chế Retry (với lỗi 5xx, 429).
- **Nguyên tắc "Do No Harm"**: Giữ nguyên các chức năng đang hoạt động tốt. Khi sửa một lỗi cục bộ, không làm phá vỡ kiến trúc tổng thể.

## 3. Quy tắc Kiểm thử (Testing Workflow)
- **Tự động kiểm thử**: TRƯỚC KHI đề nghị người dùng nghiệm thu, AI phải TỰ ĐỘNG chạy ứng dụng bằng công cụ `run_command` (hoặc viết script tự động test nếu cần thiết) để xác nhận lỗi đã được khắc phục.
- **Khởi chạy phiên kiểm thử cho người dùng**: Sau khi AI xác nhận code đã chạy được, AI phải DÙNG LỆNH để mở sẵn ứng dụng (`python openloader.py`) để người dùng chỉ việc thao tác trực quan (Click / Kéo thả) mà không cần phải tự gõ lệnh trên terminal.
- Tuân thủ các kịch bản kiểm thử cốt lõi đã được định nghĩa trong `TESTING_SCENARIOS.md`.
