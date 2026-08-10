import sys
import re

with open("openloader.py", "r", encoding="utf-8") as f:
    content = f.read()

# --- 1. Custom Prompt ---
content = content.replace(
    '''    prompt = ("Hãy chuyển đổi hình ảnh trang tài liệu này thành nội dung văn bản dưới định dạng Markdown. "
              "Giữ nguyên cấu trúc định dạng chữ, tiêu đề, danh sách, vẽ lại chính xác bảng biểu bằng bảng Markdown. "
              "Chỉ trả về Markdown thô, không thêm giải thích.")''',
    '''    default_prompt = ("Hãy chuyển đổi hình ảnh trang tài liệu này thành nội dung văn bản dưới định dạng Markdown. "
              "Giữ nguyên cấu trúc định dạng chữ, tiêu đề, danh sách, vẽ lại chính xác bảng biểu bằng bảng Markdown. "
              "Chỉ trả về Markdown thô, không thêm giải thích.")
    prompt = profile.get("prompt", "").strip()
    if not prompt:
        prompt = default_prompt'''
)

content = content.replace(
    'api_key.setEchoMode(QLineEdit.Password)\n        headers_edit = QLineEdit(profile_data.get("headers", "{}"))',
    '''api_key.setEchoMode(QLineEdit.Password)
        
        from PySide6.QtWidgets import QTextEdit
        prompt_edit = QTextEdit()
        prompt_edit.setPlaceholderText("Để trống sẽ dùng lệnh mặc định của phần mềm. Ví dụ: Dịch tài liệu này sang tiếng Việt...")
        prompt_edit.setText(profile_data.get("prompt", ""))
        prompt_edit.setMaximumHeight(60)
        
        headers_edit = QLineEdit(profile_data.get("headers", "{}"))'''
)
content = content.replace('flayout.addRow("API Key:", api_key)\n        flayout.addRow("Custom Headers (JSON):", headers_edit)',
                          'flayout.addRow("API Key:", api_key)\n        flayout.addRow("Lệnh AI (Prompt):", prompt_edit)\n        flayout.addRow("Custom Headers (JSON):", headers_edit)')
content = content.replace('"api_key": api_key,\n            "headers": headers_edit',
                          '"api_key": api_key,\n            "prompt": prompt_edit,\n            "headers": headers_edit')

content = content.replace('"api_key": w["api_key"].text().strip(),\n            "headers": w["headers"].text().strip()',
                          '"api_key": w["api_key"].text().strip(),\n            "prompt": w["prompt"].toPlainText(),\n            "headers": w["headers"].text().strip()')
content = content.replace('"api_key": w["api_key"].text(),\n                "headers": w["headers"].text()',
                          '"api_key": w["api_key"].text(),\n                "prompt": w["prompt"].toPlainText(),\n                "headers": w["headers"].text()')


# --- 2. Page Range ---
content = content.replace('self.outPathEdit = QLineEdit(self)\n        self.outPathEdit.setPlaceholderText("Thư mục đầu ra (Mặc định: Cùng thư mục với file gốc)")\n        self.outPathEdit.setReadOnly(True)',
'''self.outPathEdit = QLineEdit(self)
        self.outPathEdit.setPlaceholderText("Thư mục đầu ra (Mặc định: Cùng thư mục với file gốc)")
        self.outPathEdit.setReadOnly(True)
        
        self.pageRangeEdit = QLineEdit(self)
        self.pageRangeEdit.setPlaceholderText("Khoảng trang (Vd: 1-5, 10) - Bỏ trống để quét toàn bộ")
        self.pageRangeEdit.setToolTip("Chỉ áp dụng cho tính năng OCR PDF. Ví dụ: 1-5, 10, 15-20")'''
)
content = content.replace('output_layout.addWidget(self.btnBrowseFolder)\n        main_layout.addLayout(output_layout)',
'''output_layout.addWidget(self.btnBrowseFolder)
        
        page_range_layout = QHBoxLayout()
        page_range_label = QLabel("Trang cần quét:")
        page_range_label.setStyleSheet("font-weight: bold;")
        page_range_layout.addWidget(page_range_label)
        page_range_layout.addWidget(self.pageRangeEdit)
        
        main_layout.addLayout(output_layout)
        main_layout.addLayout(page_range_layout)'''
)

content = content.replace('"output_dir": self.outPathEdit.text(),',
                          '"output_dir": self.outPathEdit.text(),\n                "page_range": self.pageRangeEdit.text(),')
content = content.replace('if output_dir:\n                self.outPathEdit.setText(output_dir)',
                          'if output_dir:\n                self.outPathEdit.setText(output_dir)\n            \n            page_range = config.get("page_range", "")\n            if page_range:\n                self.pageRangeEdit.setText(page_range)')

content = content.replace('def __init__(self, input_paths, formats, output_dir, ocr_mode, ai_profile=None):',
                          'def __init__(self, input_paths, formats, output_dir, ocr_mode, ai_profile=None, page_range=""):')
content = content.replace('self.ai_profile = ai_profile', 'self.ai_profile = ai_profile\n        self.page_range = page_range')

# Be careful with the worker instantiation
content = content.replace('''        self.worker = ConversionWorker(
            input_paths=self.input_paths,
            formats=formats,
            output_dir=output_dir,
            ocr_mode=ocr_mode,
            ai_profile=active_profile
        )''',
'''        self.worker = ConversionWorker(
            input_paths=self.input_paths,
            formats=formats,
            output_dir=output_dir,
            ocr_mode=ocr_mode,
            ai_profile=active_profile,
            page_range=self.pageRangeEdit.text()
        )''')

page_range_logic = '''
        def parse_page_range(range_str, max_pages):
            if not range_str.strip():
                return set(range(max_pages))
            pages = set()
            for part in range_str.split(","):
                part = part.strip()
                if not part: continue
                if "-" in part:
                    try:
                        start, end = map(int, part.split("-"))
                        pages.update(range(max(0, start - 1), min(max_pages, end)))
                    except: pass
                else:
                    try:
                        pages.add(int(part) - 1)
                    except: pass
            return pages
            
        target_pages = parse_page_range(getattr(self, "page_range", ""), doc.page_count)
'''
content = content.replace('doc = fitz.open(file_path)\n        total_pages = doc.page_count',
'''doc = fitz.open(file_path)
        total_pages = doc.page_count
''' + page_range_logic)

content = content.replace('for page_num in range(total_pages):',
                          'for page_num in range(total_pages):\n            if page_num not in target_pages:\n                continue')


with open("openloader.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Phase 1 & 2 applied.")
