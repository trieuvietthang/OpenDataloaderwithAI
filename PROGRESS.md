# TIẾN ĐỘ DỰ ÁN (PROJECT PROGRESS)

## Giai đoạn hiện tại: [Hoàn thành Version 2.1 - Docling OCR & Tối ưu tiếng Việt]

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
   - ~~**Trình Xem Trước (Preview)**: Bổ sung QTabWidget chia 2 khung Nhật ký xử lý & Xem trước kết quả~~ *(Đã gỡ bỏ để tối ưu hóa hiệu suất và chống treo UI theo luật Simplicity First).*
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
8. [x] **Tích hợp Docling OCR (Layout + TableFormer)**:
   - **Bổ sung chế độ OCR thứ 4:** Docling sử dụng mô hình Layout Analysis + TableFormer để giữ nguyên cấu trúc bảng biểu — điểm yếu cố hữu của Tesseract thuần.
   - **Fix lỗi kết quả rỗng (Root cause):** Docling mặc định `lang=['fra','deu','spa','eng']` — hoàn toàn không có tiếng Việt. Đã ép rõ `lang=["vie","eng"]` kèm `path` trỏ tới thư mục `tessdata` cục bộ.
   - **Chuyển sang `TesseractCliOcrOptions`:** Thay cho `TesseractOcrOptions` (vốn đòi hỏi C-binding `tesserocr` phải biên dịch thủ công). Bản CLI gọi thẳng binary Tesseract nên chạy được ngay.
   - **Fix crash `InvalidCxxCompiler`:** Docling chạy mô hình layout qua `torch.compile`, đòi hỏi trình biên dịch MSVC `cl` mà đa số máy Windows không có. Đã set `TORCHDYNAMO_DISABLE=1` **trước mọi import** để vô hiệu hóa.
   - **Fix lỗi "Model not found":** Chỉ gán `artifacts_path` khi thư mục model thực sự có dữ liệu; nếu rỗng thì để Docling tự tải về (trước đây trỏ vào thư mục rỗng gây lỗi thay vì auto-download).
   - **Fix nút "Cài đặt Docling" không tải model:** Bản cũ chỉ khởi tạo đối tượng `DocumentConverter` (không hề tải gì). Đã gọi đúng `download_models()`.
   - **Tự động tải `vie.traineddata`** nếu thiếu, dùng chung logic với chế độ Tesseract.
   - **Dọn rác đầu ra:** Xuất Markdown với `image_placeholder=""` và tự xóa thư mục `{stem}_images/` sau khi ghi file, tránh để lại thư mục ảnh thừa.
9. [x] **Sửa lỗi phần mở rộng tệp đầu ra (`.markdown` → `.md`)**:
   - Nguyên nhân: code ghép chuỗi `f"{base_name}.{fmt}"` với `fmt="markdown"`.
   - Khắc phục: bổ sung hằng số `FORMAT_EXTENSIONS = {"markdown": "md", "text": "txt"}` và áp dụng cho cả 2 luồng xuất (PDF OCR và DOCX).
10. [x] **Gỡ bỏ VietOCR (Quyết định kỹ thuật)**:
    - Lý do: `vietocr==0.3.13` ghim cứng `pillow==10.2.0`; Python 3.13 không có wheel dựng sẵn nên pip buộc phải build từ source và thất bại (`KeyError: '__version__'`).
    - Theo luật **Simplicity First**, đã gỡ bỏ toàn bộ tính năng thay vì cố vá một phụ thuộc đã lỗi thời, tránh làm mất ổn định các chế độ OCR đang chạy tốt.

### Hạng mục tiếp theo (To-do / Backlog):
- [x] Bổ sung kịch bản tự động hóa Unit Test (PyTest) — hiện có `tests/` với 4 test PASS.
- [x] **Cải thiện hiển thị thanh tiến độ xử lý trang song song (Multi-threading cho từng trang)**.
- [x] Đóng gói lại thành file cài đặt `.exe` phiên bản V2 (OpenDataLoader_Setup_V2.1.exe).

---

## Giai đoạn tiếp theo: V2.2 (Backlog)

Toàn bộ mục tiêu V2.1 ở trên đã hoàn thành. Backlog dưới đây là các hướng đã chốt với người dùng cho giai đoạn kế tiếp, xếp theo thứ tự ưu tiên đề xuất (nền tảng ổn định trước, tính năng mới sau):

1. [x] **Mở rộng bộ test & CI**: Thêm test cho `parse_page_range`, retry/backoff của `ocr_page_with_ai` (mock HTTP), và `convert_docx` (format branching) — hiện có 25 test PASS. Đã thêm GitHub Actions (`.github/workflows/tests.yml`) chạy `pytest` tự động trên `windows-latest` mỗi lần push/PR vào `main`.
2. [ ] **Tăng độ ổn định & test coverage sâu hơn**: Bổ sung test cho luồng Docling và Tesseract (mock subprocess/model calls), và các đường lỗi khi thiếu Java/Tesseract/model (thông báo lỗi rõ ràng thay vì crash).
3. [ ] **Tái cấu trúc `openloader.py`**: Tách file ~2.800 dòng hiện tại thành các module riêng (vd: `ui/`, `workers/`, `ocr/`, `utils/`) để dễ bảo trì. Đây là thay đổi kiến trúc lớn — cần lên kế hoạch chi tiết (thứ tự tách, cách giữ tương thích `config.json`/import) và xác nhận với người dùng từng bước trước khi thực hiện, tránh phá vỡ chức năng đang chạy tốt (nguyên tắc "Do No Harm").
4. [x] **Tính năng: Xóa định danh cá nhân khi convert (PII Redaction)**:
   - **Cách thay thế:** Thay bằng nhãn cho biết đã ẩn loại gì — `[ĐÃ ẨN: CCCD]`, `[ĐÃ ẨN: SĐT]`... giữ được ngữ cảnh tài liệu để rà soát lại.
   - **Nhận diện bằng regex (mọi luồng):** CCCD/CMND, SĐT, Email, Số tài khoản, Mã số thuế, Ngày sinh, Biển số xe.
   - **Chống ẩn nhầm:** Ngày sinh / STK / MST / CMND chỉ ẩn khi có từ khóa ngữ cảnh đứng trước (vd `sinh ngày 01/01/1990`, `STK: ...`). Nếu bắt mọi dãy số thì ngày lập văn bản, số tiền, số hợp đồng cũng bị ẩn nhầm làm hỏng hồ sơ.
   - **Chịu được lỗi rơi dấu của OCR:** Từ khóa ngữ cảnh khớp cả bản có dấu lẫn không dấu (`Số tài khoản` = `So tai khoan`) — bản scan qua Tesseract hay mất dấu, nếu không xử lý thì thông tin cá nhân sẽ lọt ra ngoài.
   - **Nhờ AI ẩn thêm họ tên & địa chỉ:** Ở chế độ OCR Trí tuệ nhân tạo, chèn thêm chỉ dẫn vào prompt để AI ẩn hai loại mà regex không nhận ra được.
   - **Đã nối vào cả 4 luồng:** OCR (Tesseract/AI), Docling, DOCX, và Standard (luồng này do thư viện ngoài tự ghi file nên phải xử lý sau khi ghi).
   - **UI:** Thêm ô chọn "Ẩn thông tin định danh cá nhân" ở mục Bảo mật, trạng thái được ghi nhớ trong `config.json`.
5. [ ] **Tính năng mới khác cho người dùng**: Ví dụ xuất nhiều định dạng cùng lúc trong 1 lần chạy, khôi phục Preview ở dạng nhẹ (không chặn UI), auto-update, cải thiện installer (`installer.iss`).
