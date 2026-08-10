import re

with open("openloader.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
if "QTabWidget" not in content:
    content = content.replace(
        "from PySide6.QtWidgets import (",
        "from PySide6.QtWidgets import (\n    QDialog, QTabWidget, QFormLayout, QGroupBox, QComboBox as QComboBoxClass, QSpinBox, QFontComboBox,"
    )

# 2. Add SettingsDialog class before MainWindow
settings_dialog_code = '''

class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("⚙️ Cài đặt hệ thống")
        self.setMinimumSize(700, 500)
        
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QWidget { color: #1e293b; font-size: 13px; font-family: 'Segoe UI'; }
            QGroupBox { border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 10px; padding-top: 15px; font-weight: bold; color: #2d3a8c; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 16px; font-weight: 500; }
            QPushButton:hover { background-color: #f1f5f9; border-color: #94a3b8; }
            QPushButton#primaryBtn { background-color: #2d3a8c; color: white; border: none; }
            QPushButton#primaryBtn:hover { background-color: #1e2865; }
            QPushButton#dangerBtn { color: #e52b2d; border-color: #e52b2d; }
            QPushButton#dangerBtn:hover { background-color: #fef2f2; }
            QLineEdit, QComboBox, QSpinBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px; }
            QLineEdit:focus { border-color: #2d3a8c; }
        """)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 16px; background: #e2e8f0; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; } QTabBar::tab:selected { background: #ffffff; border: 1px solid #cbd5e1; border-bottom: none; font-weight: bold; color: #2d3a8c; } QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; }")
        
        # Tab AI
        self.tab_ai = QWidget()
        self.setup_ai_tab()
        self.tabs.addTab(self.tab_ai, "🤖 Quản lý cấu hình AI")
        
        # Tab UI
        self.tab_ui = QWidget()
        self.setup_ui_tab()
        self.tabs.addTab(self.tab_ui, "🎨 Giao diện")
        
        layout.addWidget(self.tabs)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btnSave = QPushButton("💾 Lưu & Đóng")
        self.btnSave.setObjectName("primaryBtn")
        self.btnSave.clicked.connect(self.save_and_close)
        btn_layout.addWidget(self.btnSave)
        layout.addLayout(btn_layout)
        
        self.load_data()

    def setup_ai_tab(self):
        layout = QVBoxLayout(self.tab_ai)
        
        # Default AI Selector
        top_group = QGroupBox("Trợ lý AI Mặc định")
        top_layout = QHBoxLayout(top_group)
        top_layout.addWidget(QLabel("Cấu hình ưu tiên:"))
        self.default_ai_combo = QComboBox()
        self.default_ai_combo.setMinimumWidth(300)
        top_layout.addWidget(self.default_ai_combo)
        top_layout.addStretch()
        layout.addWidget(top_group)
        
        # Profiles Editor
        self.profiles_group = QGroupBox("Danh sách cấu hình")
        self.profiles_layout = QVBoxLayout(self.profiles_group)
        self.profile_widgets = []
        layout.addWidget(self.profiles_group)
        
        add_btn = QPushButton("➕ Thêm cấu hình mới")
        add_btn.clicked.connect(lambda: self.add_profile_ui({}))
        layout.addWidget(add_btn, alignment=Qt.AlignLeft)
        layout.addStretch()

    def add_profile_ui(self, profile_data):
        from PySide6.QtWidgets import QFrame
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #e2e8f0; border-radius: 6px; background-color: #f8fafc; padding: 5px; } QLabel { border: none; background: transparent; } QLineEdit { background: #ffffff; }")
        flayout = QFormLayout(frame)
        
        name_edit = QLineEdit(profile_data.get("name", "Cấu hình mới"))
        api_type = QComboBox()
        api_type.addItems(["Google Gemini", "OpenAI-Compatible (OpenAI, Claude...)"])
        api_type.setCurrentIndex(0 if profile_data.get("api_type", "gemini") == "gemini" else 1)
        
        base_url = QLineEdit(profile_data.get("base_url", "https://generativelanguage.googleapis.com/v1beta"))
        model_name = QLineEdit(profile_data.get("model", "gemini-2.5-flash"))
        api_key = QLineEdit(profile_data.get("api_key", ""))
        api_key.setEchoMode(QLineEdit.Password)
        headers_edit = QLineEdit(profile_data.get("headers", "{}"))
        
        del_btn = QPushButton("🗑 Xóa")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(lambda: self.remove_profile(frame))
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(del_btn)
        
        flayout.addRow(header_layout)
        flayout.addRow("Tên hiển thị:", name_edit)
        flayout.addRow("Chuẩn kết nối:", api_type)
        flayout.addRow("Base URL:", base_url)
        flayout.addRow("Tên Model:", model_name)
        flayout.addRow("API Key:", api_key)
        flayout.addRow("Custom Headers (JSON):", headers_edit)
        
        frame.data_widgets = {
            "name": name_edit,
            "api_type": api_type,
            "base_url": base_url,
            "model": model_name,
            "api_key": api_key,
            "headers": headers_edit
        }
        
        self.profiles_layout.addWidget(frame)
        self.profile_widgets.append(frame)
        self.update_default_combo()
        name_edit.textChanged.connect(self.update_default_combo)

    def remove_profile(self, frame):
        self.profiles_layout.removeWidget(frame)
        self.profile_widgets.remove(frame)
        frame.deleteLater()
        self.update_default_combo()

    def update_default_combo(self):
        current_idx = self.default_ai_combo.currentIndex()
        self.default_ai_combo.clear()
        for frame in self.profile_widgets:
            name = frame.data_widgets["name"].text()
            self.default_ai_combo.addItem(name)
        if current_idx >= 0 and current_idx < self.default_ai_combo.count():
            self.default_ai_combo.setCurrentIndex(current_idx)

    def setup_ui_tab(self):
        layout = QFormLayout(self.tab_ui)
        self.font_combo = QFontComboBox()
        self.font_size = QSpinBox()
        self.font_size.setRange(9, 24)
        
        layout.addRow("Font chữ hiển thị:", self.font_combo)
        layout.addRow("Cỡ chữ (px):", self.font_size)

    def load_data(self):
        ai_profiles = self.config.get("ai_profiles", [])
        if not ai_profiles:
            ai_profiles = [{
                "id": "default",
                "name": "Google Gemini (Mặc định)",
                "api_type": "gemini",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model": "gemini-2.5-flash",
                "api_key": "",
                "headers": "{}"
            }]
        
        for p in ai_profiles:
            self.add_profile_ui(p)
            
        active_idx = 0
        active_id = self.config.get("active_ai_profile_id", "")
        for i, p in enumerate(ai_profiles):
            if p.get("id") == active_id:
                active_idx = i
                break
        self.default_ai_combo.setCurrentIndex(active_idx)
        
        ui_set = self.config.get("ui_settings", {})
        self.font_combo.setCurrentFont(QFont(ui_set.get("font_family", "Segoe UI")))
        self.font_size.setValue(ui_set.get("font_size", 13))

    def save_and_close(self):
        profiles = []
        for i, frame in enumerate(self.profile_widgets):
            w = frame.data_widgets
            profiles.append({
                "id": f"profile_{i}",
                "name": w["name"].text(),
                "api_type": "gemini" if w["api_type"].currentIndex() == 0 else "openai",
                "base_url": w["base_url"].text(),
                "model": w["model"].text(),
                "api_key": w["api_key"].text(),
                "headers": w["headers"].text()
            })
        
        active_idx = self.default_ai_combo.currentIndex()
        active_id = profiles[active_idx]["id"] if profiles and active_idx >= 0 else ""
        
        self.config["ai_profiles"] = profiles
        self.config["active_ai_profile_id"] = active_id
        
        self.config["ui_settings"] = {
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.font_size.value()
        }
        
        self.accept()
'''

if "class SettingsDialog(QDialog):" not in content:
    content = content.replace("class FileDropZone(QFrame):", settings_dialog_code + "\nclass FileDropZone(QFrame):")

# 3. Update validate API & ocr_page
ocr_code = '''
def validate_ai_profile(profile):
    """Validate AI profile by making a small request based on API type."""
    try:
        api_type = profile.get("api_type", "gemini")
        api_key = profile.get("api_key", "")
        base_url = profile.get("base_url", "")
        
        if not api_key:
            return False, "API Key trống"
            
        if api_type == "gemini":
            url = f"{base_url.rstrip('/')}/models?key={api_key}"
            req = urllib.request.Request(url)
        else:
            url = f"{base_url.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            try:
                import json
                custom_h = json.loads(profile.get("headers", "{}"))
                headers.update(custom_h)
            except:
                pass
            req = urllib.request.Request(url, headers=headers)
            
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, "Kết nối thành công!"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"

def ocr_page_with_ai(image_path, profile, max_retries=3):
    """Sends document page image to AI API (Gemini or OpenAI-compatible)."""
    api_type = profile.get("api_type", "gemini")
    api_key = profile.get("api_key", "")
    base_url = profile.get("base_url", "").rstrip("/")
    model = profile.get("model", "gemini-2.5-flash")
    
    import base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
    prompt = ("Hãy chuyển đổi hình ảnh trang tài liệu này thành nội dung văn bản dưới định dạng Markdown. "
              "Giữ nguyên cấu trúc định dạng chữ, tiêu đề, danh sách, vẽ lại chính xác bảng biểu bằng bảng Markdown. "
              "Chỉ trả về Markdown thô, không thêm giải thích.")
              
    headers = {"Content-Type": "application/json"}
    try:
        import json
        custom_h = json.loads(profile.get("headers", "{}"))
        headers.update(custom_h)
    except:
        pass
        
    if api_type == "gemini":
        url = f"{base_url}/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/png", "data": image_data}}]}]
        }
    else:
        url = f"{base_url}/chat/completions"
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]}
            ]
        }
        
    import json
    data_bytes = json.dumps(payload).encode("utf-8")
    
    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                try:
                    if api_type == "gemini":
                        text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        text = res_data["choices"][0]["message"]["content"]
                        
                    if text.startswith("```markdown"): text = text[len("```markdown"):].strip()
                    if text.startswith("```"): text = text[3:].strip()
                    if text.endswith("```"): text = text[:-3].strip()
                    return text
                except (KeyError, IndexError):
                    raise Exception("Phản hồi AI không hợp lệ: " + json.dumps(res_data))
        except urllib.error.HTTPError as http_err:
            last_error = http_err
            if http_err.code in (429, 500, 502, 503):
                wait_time = (2 ** attempt) * 2
                try: print(f"AI API error {http_err.code}, retrying...")
                except: pass
                import time
                time.sleep(wait_time)
                continue
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                import time
                time.sleep((2 ** attempt) * 2)
                continue
            raise
            
    raise Exception(f"AI API failed after {max_retries} attempts: {str(last_error)}")
'''

# Replace the old validate_gemini_key and ocr_page_with_gemini
content = re.sub(r'def validate_gemini_key.*?return False, f"Không thể kết nối tới Gemini API: \{str\(e\)\}"', '', content, flags=re.DOTALL)
content = re.sub(r'def ocr_page_with_gemini.*?raise Exception\(f"Gemini API failed after \{max_retries\} attempts\. Last error: \{str\(last_error\)\}"\)', ocr_code, content, flags=re.DOTALL)

# 4. Modify ConversionWorker
content = content.replace(
    'def __init__(self, input_paths, formats, output_dir, ocr_mode="none", gemini_key=""):',
    'def __init__(self, input_paths, formats, output_dir, ocr_mode="none", ai_profile=None):'
)
content = content.replace('self.gemini_key = gemini_key', 'self.ai_profile = ai_profile or {}')
content = content.replace('ocr_page_with_gemini(str(img_path), self.gemini_key)', 'ocr_page_with_ai(str(img_path), self.ai_profile)')
content = content.replace('Lỗi Gemini API trang', 'Lỗi AI API trang')
content = content.replace('OCR Gemini thành công', 'OCR AI thành công')

# 5. Modify MainWindow init & Settings Button
if "self.btnSettings =" not in content:
    content = content.replace(
        'self.ocrCombo.currentIndexChanged.connect(self.toggle_gemini_input)',
        'self.ocrCombo.currentIndexChanged.connect(self.toggle_gemini_input)\n        self.btnSettings = QPushButton("⚙️ Cài đặt")\n        self.btnSettings.clicked.connect(self.open_settings)\n        config_layout.addWidget(self.btnSettings, 1, 2)'
    )

# Replace gemini input with AI Profile Label
content = content.replace('self.geminiKeyLabel = QLabel("<b>Gemini API Key:</b>", self)', 'self.geminiKeyLabel = QLabel("<b>Cấu hình AI:</b>", self)')
content = content.replace('self.geminiKeyEdit = QLineEdit(self)', 'self.geminiKeyEdit = QLabel("Chưa chọn cấu hình", self)\n        self.geminiKeyEdit.setStyleSheet("color: #2d3a8c; font-weight: bold;")')
content = content.replace('self.geminiKeyEdit.setPlaceholderText("Nhập mã API Key của Gemini tại đây để quét tài liệu...")\n        self.geminiKeyEdit.setEchoMode(QLineEdit.EchoMode.Password)', '')


content = content.replace('gemini_key = self.geminiKeyEdit.text().strip()', 'gemini_key = "profile"')
content = content.replace('if not gemini_key:\n                QMessageBox.warning(self, "Thiếu API Key", "Vui lòng nhập Gemini API Key để thực hiện quét tài liệu.")\n                return', 'active_profile = self.get_active_ai_profile()\n            if not active_profile.get("api_key"):\n                QMessageBox.warning(self, "Chưa cấu hình AI", "Vui lòng vào Cài đặt để thêm và chọn cấu hình AI.")\n                return')

content = content.replace('validate_gemini_key(gemini_key)', 'validate_ai_profile(active_profile)')
content = content.replace('gemini_key=gemini_key', 'ai_profile=active_profile')

# Update load_config and setup_styles dynamically
extra_methods = '''
    def open_settings(self):
        dialog = SettingsDialog(self, self.app_config)
        if dialog.exec():
            self.save_config()
            self.apply_config_ui()
            
    def get_active_ai_profile(self):
        active_id = self.app_config.get("active_ai_profile_id", "")
        for p in self.app_config.get("ai_profiles", []):
            if p.get("id") == active_id:
                return p
        return {}

    def apply_config_ui(self):
        ui_set = self.app_config.get("ui_settings", {})
        font_family = ui_set.get("font_family", "Segoe UI")
        font_size = ui_set.get("font_size", 13)
        self.setStyleSheet(self.styleSheet().replace("font-family: 'Segoe UI'", f"font-family: '{font_family}'").replace("font-size: 13px;", f"font-size: {font_size}px;"))
        
        p = self.get_active_ai_profile()
        self.geminiKeyEdit.setText(p.get("name", "Chưa cấu hình"))
'''
if "def open_settings" not in content:
    content = content.replace('def toggle_gemini_input(self, index):', extra_methods + '\n    def toggle_gemini_input(self, index):')

content = content.replace('def load_config(self):\n        """Load user configuration from JSON file."""\n        try:', 'def load_config(self):\n        """Load user configuration from JSON file."""\n        self.app_config = {}\n        try:')
content = content.replace('config = json.load(f)', 'self.app_config = json.load(f)\n                config = self.app_config\n                self.apply_config_ui()')

content = content.replace('def save_config(self):\n        """Save current configuration to JSON file."""\n        try:\n            config = {', 'def save_config(self):\n        """Save current configuration to JSON file."""\n        try:\n            config = getattr(self, "app_config", {})\n            config.update({')


with open("openloader.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Success")
