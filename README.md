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
- ⚙️ **AI Profile Management**: Store and switch between multiple API configurations effortlessly, complete with instant API connection testing.
- 🎯 **Prompt Engineering**: Highly customizable prompts to guide the AI for specialized extraction or on-the-fly translation.
- 📑 **Page Range Selection**: Process specific pages (e.g., `1-5, 10`) to save time and reduce API costs.
- 🎨 **Modern UI/UX**: Built on `PySide6` featuring a sleek flat design, drag-and-drop file support, and hot-swappable Light/Dark themes.
- 👀 **Live Preview**: Integrated Markdown/HTML renderer to preview output results instantly within the app.

### Architecture & Tech Stack
- **Framework**: `PySide6` (Qt for Python)
- **Core Dependencies**: `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`
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
- ⚙️ **Quản lý Cấu hình AI (Profile)**: Lưu trữ và chuyển đổi linh hoạt giữa nhiều cấu hình API khác nhau, hỗ trợ kiểm tra kết nối API tức thì.
- 🎯 **Prompt Engineering**: Cho phép tùy biến câu lệnh (prompt) linh hoạt để điều hướng AI trong việc trích xuất chuyên sâu hoặc dịch thuật ngay lập tức.
- 📑 **Chọn vùng trang (Page Range)**: Xử lý chính xác các trang mong muốn (VD: `1-5, 10`) giúp tiết kiệm thời gian và chi phí gọi API.
- 🎨 **Giao diện Hiện đại (UI/UX)**: Xây dựng bằng `PySide6` với thiết kế phẳng (Flat Design), hỗ trợ kéo thả tệp và chuyển đổi nóng giao diện Sáng/Tối (Light/Dark Theme).
- 👀 **Xem trước trực tiếp (Live Preview)**: Tích hợp bộ kết xuất Markdown/HTML ngay trong ứng dụng để xem trước kết quả nhanh chóng.

### Kiến trúc & Công nghệ
- **Nền tảng giao diện**: `PySide6`
- **Thư viện lõi**: `PyMuPDF` (fitz), `pytesseract`, `Pillow`, `mammoth`, `markdownify`, `markdown`
- **Xử lý đa luồng**: Ứng dụng mô hình `QThread` (`ConversionWorker`) để xử lý các tác vụ nặng (OCR, gọi API) dưới nền, đảm bảo giao diện phần mềm luôn mượt mà.

---

### Acknowledgments / Ghi nhận
This project is a modified/derivative work based on the original [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) developed by Hancom, Inc., licensed under the Apache License 2.0.

---
*Built with ❤️ for better document management.*
