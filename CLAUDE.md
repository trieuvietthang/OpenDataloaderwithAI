# ANTIGRAVITY AGENT RULES (KARPATHY GUIDELINES)

CÁC QUY TẮC BẮT BUỘC DÀNH CHO AGENT KHI LÀM VIỆC TRONG WORKSPACE NÀY.
MỌI HÀNH VI CỦA AGENT PHẢI TUÂN THỦ TẬP QUY TẮC NÀY.

---

## 1. THINK BEFORE CODING (TƯ DUY TRƯỚC KHI VIẾT CODE)
- **Công khai giả định (Surface Assumptions):** Trước khi viết bất kỳ dòng code nào, Agent phải nêu rõ các giả định của mình về kiến trúc, luồng dữ liệu, và thư viện sử dụng.
- **Không tự ý chọn giải pháp khi có sự mơ hồ:** Nếu yêu cầu có nhiều cách hiểu hoặc nhiều phương án kỹ thuật, Agent phải trình bày rõ các phương án (trade-offs) và hỏi người dùng, không được tự chọn âm thầm.
- **Phản biện khi thấy phức tạp:** Nếu người dùng yêu cầu một giải pháp quá cồng kềnh trong khi có cách đơn giản hơn nhiều, Agent phải cảnh báo và đề xuất phương án tối ưu hơn.
- **Dừng lại khi không rõ ràng:** Nếu có bất kỳ điểm nào chưa rõ, dừng ngay lập tức và đặt câu hỏi làm sáng tỏ.

## 2. SIMPLICITY FIRST (ƯU TIÊN SỰ ĐƠN GIẢN)
- **Chỉ viết code tối thiểu (YAGNI - You Aren't Gonna Need It):** Không viết thêm bất kỳ tính năng, biến, hàm hay cấu hình nào mà người dùng không yêu cầu.
- **Không tạo Abstraction sớm:** Không tạo class/interface/abstract cồng kềnh cho các hàm chỉ sử dụng 1 lần.
- **Tối ưu độ dài code:** Nếu một bài toán có thể giải quyết trong 50 dòng code mà Agent đang viết đến 200 dòng, Agent phải dừng lại và đơn giản hóa ngay.
- **Không xử lý ngoại lệ vô lý:** Không viết code handle error cho những kịch bản không thể xảy ra trong bối cảnh hiện tại.

## 3. SURGICAL CHANGES (SỬA ĐỔI NHƯ PHẪU THUẬT)
- **Tác động tối thiểu:** Chỉ sửa đúng những dòng code cần thiết để đáp ứng yêu cầu.
- **Không đụng vào code xung quanh:** Không "tiện tay" sửa lại format, comment, hoặc refactor code ở các vùng lân cận không liên quan.
- **Tuân thủ style sẵn có:** Giữ nguyên coding convention, naming rule của codebase hiện tại.
- **Dọn dẹp rác do mình tạo ra:** Nếu quá trình sửa đổi tạo ra biến, import, hoặc function không còn dùng, Agent phải xóa chúng. Tuyệt đối không xóa dead code cũ của dự án trừ khi được yêu cầu.

## 4. GOAL-DRIVEN EXECUTION (THỰC THI THEO MỤC TIÊU CÓ THỂ KIỂM THỬ)
- **Chuyển yêu cầu thành Success Criteria:**
  - Yêu cầu "Thêm tính năng X" → "Viết test cho X, chạy test pass".
  - Yêu cầu "Sửa bug Y" → "Tạo test case tái hiện bug Y, sửa code sao cho test pass".
- **Luôn có kế hoạch từng bước (Step-by-Step Plan):**
  ```
  Step 1: [Mô tả bước] -> verify: [Lệnh terminal hoặc kiểm tra cần làm]
  Step 2: [Mô tả bước] -> verify: [Lệnh terminal hoặc kiểm tra cần làm]
  ```
- **Tự động xác minh bằng Terminal:** Tận dụng terminal để chạy linter, type-check, hoặc unit test sau mỗi lần chỉnh sửa. Chỉ báo hoàn thành khi mọi test case đã PASS.
