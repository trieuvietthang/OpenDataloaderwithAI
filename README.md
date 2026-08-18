# OpenDataLoader PDF (V2.0 Pro Edition) 📄✨

*Read this in other languages: [English](#english) | [Tiếng Việt](#tiếng-việt)*

---

<a name="english"></a>
## 🇬🇧 English

### Overview
**OpenDataLoader PDF** is a professional desktop application designed primarily for office environments (especially bailiff offices and legal practices) to extract, convert, and digitize documents. It seamlessly converts **PDF** and **DOCX** files into structured **Markdown, HTML, or plain Text**.

### Core Features
- 🚀 **Standard Extraction**: Lightning-fast text extraction from native PDF and DOCX files using `PyMuPDF` and `mammoth`.
- 🔍 **Local OCR**: Built-in support for Tesseract OCR to recognize text from scanned images and image-based PDFs, with excellent support for the Vietnamese language.
- 🧠 **Cloud AI Vision OCR**: Advanced processing for complex layouts, tables, and formatting using state-of-the-art Vision AI models (Google Gemini, OpenAI, Claude, OpenRouter).
- 📊 **Docling OCR (Offline Layout + TableFormer)**: Structure-aware offline OCR that preserves table layouts, powered by Docling's Layout Analysis and TableFormer models, tuned for Vietnamese (`vie+eng`).
- 🛡️ **Advanced Watermark Removal**: Clean up deeply embedded or rasterized watermarks using a dual-mode system (Vector-Level removal for text-based watermarks + advanced Pixel Filtering). Supports adaptive morphology and contrast enhancement for massive opaque stamps, all while keeping file size tiny via 1-bit monochrome/CCITT optimization.
- ⚙️ **AI Profile Management**: Store and switch between multiple API configurations effortlessly, complete with instant API connection testing.
- 🎯 **Prompt Engineering**: Highly customizable prompts to guide the AI for specialized extraction or on-the-fly translation.
- 📑 **Page Range Selection**: Process specific pages (e.g., `1-5, 10`) to save time and reduce API costs.
- 🎨 **Modern UI/UX**: Built on `PySide6` featuring a sleek flat design, drag-and-drop file support, and hot-swappable Light/Dark themes.


### Architecture & Tech Stack
- **Framework**: `PySide6` (Qt for Python)
- **Core Dependencies**: `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`
- **Optional**: `docling` (structure-aware offline OCR; auto-downloads its models on first use)
- **Concurrency**: `QThread` based background processing (`ConversionWorker`) to keep the UI responsive during heavy OCR/API tasks.

---

<a name="tiếng-việt"></a>
## 🇻🇳 Tiếng Việt

### Tổng quan
**OpenDataLoader PDF** là một ứng dụng desktop chuyên nghiệp dành cho khối văn phòng (đặc biệt phù hợp với Văn phòng Thừa phát lại, Pháp lý) dùng để trích xuất và số hóa tài liệu. Phần mềm cho phép chuyển đổi mượt mà các tệp định dạng **PDF** và **DOCX** sang định dạng có cấu trúc như **Markdown, HTML, hoặc Text thuần**.

### Tính năng cốt lõi
- 🚀 **Trích xuất tiêu chuẩn**: Trích xuất văn bản cực nhanh từ file PDF/DOCX gốc bằng `PyMuPDF` và `mammoth`.
- 🔍 **OCR cục bộ**: Tích hợp Tesseract OCR để nhận diện chữ từ tài liệu scan và file ảnh, hỗ trợ xuất sắc nhận diện tiếng Việt.
- 🧠 **OCR Đám mây (AI Vision)**: Xử lý hoàn hảo các định dạng phức tạp và bảng biểu nhờ vào sức mạnh của các mô hình AI tiên tiến (Google Gemini, OpenAI, Claude, OpenRouter).
- 📊 **Docling OCR (Ngoại tuyến - Layout + TableFormer)**: Chế độ OCR ngoại tuyến hiểu cấu trúc tài liệu, giữ nguyên bảng biểu nhờ mô hình Layout Analysis và TableFormer của Docling, đã tinh chỉnh riêng cho tiếng Việt (`vie+eng`).
- 🛡️ **Xóa Watermark & Tiền Xử Lý (Tiên tiến)**: Tự động loại bỏ Watermark với hệ thống 2 chế độ (Phẫu thuật mã nguồn Vector cho chữ chéo + Lọc điểm ảnh nâng cao). Tích hợp cơ chế vá nét gãy (Morphology) và đẩy tương phản chuyên biệt cho các con dấu/Watermark đục lớn. Tối ưu cực độ không gian lưu trữ bằng ảnh nén 1-bit Monochrome CCITT G4.
- ⚙️ **Quản lý Cấu hình AI (Profile)**: Lưu trữ và chuyển đổi linh hoạt giữa nhiều cấu hình API khác nhau, hỗ trợ kiểm tra kết nối API tức thì.
- 🎯 **Prompt Engineering**: Cho phép tùy biến câu lệnh (prompt) linh hoạt để điều hướng AI trong việc trích xuất chuyên sâu hoặc dịch thuật ngay lập tức.
- 📑 **Chọn vùng trang (Page Range)**: Xử lý chính xác các trang mong muốn (VD: `1-5, 10`) giúp tiết kiệm thời gian và chi phí gọi API.
- 🎨 **Giao diện Hiện đại (UI/UX)**: Xây dựng bằng `PySide6` với thiết kế phẳng (Flat Design), hỗ trợ kéo thả tệp và chuyển đổi nóng giao diện Sáng/Tối (Light/Dark Theme).


### Kiến trúc & Công nghệ
- **Nền tảng giao diện**: `PySide6`
- **Thư viện lõi**: `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`
- **Tùy chọn**: `docling` (OCR ngoại tuyến hiểu cấu trúc; tự động tải model trong lần sử dụng đầu tiên)
- **Xử lý đa luồng**: Ứng dụng mô hình `QThread` (`ConversionWorker`) để xử lý các tác vụ nặng (OCR, gọi API) dưới nền, đảm bảo giao diện phần mềm luôn mượt mà.

---

### Acknowledgments / Ghi nhận
This project is a modified/derivative work based on the original [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) developed by Hancom, Inc., licensed under the Apache License 2.0.

---
*Built with ❤️ for better document management.*
