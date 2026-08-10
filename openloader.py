# -------------------------------------------------------------------------
# This file contains modified code based on the original OpenDataLoader PDF 
# by Hancom, Inc. (Licensed under Apache 2.0).
# Modifications by trieuvietthang (2026).
# -------------------------------------------------------------------------
import sys
import os
import subprocess
import json
import traceback
import shutil
import base64
import time
import urllib.request
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QFormLayout, QGroupBox, QComboBox as QComboBoxClass, QSpinBox, QFontComboBox,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QFileDialog, QPlainTextEdit,
    QProgressBar, QMessageBox, QFrame, QGridLayout, QLineEdit, QComboBox
)
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QDesktopServices, QPixmap

# Try to import document conversion and OCR libraries
try:
    import mammoth
except ImportError:
    mammoth = None

try:
    import markdownify
except ImportError:
    markdownify = None

try:
    import opendataloader_pdf
except ImportError:
    opendataloader_pdf = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

# Try to import markdown for proper HTML rendering
try:
    import markdown as md_lib
except ImportError:
    md_lib = None


def get_app_dir():
    """Get the application's base directory, works for both script and frozen exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


APP_DIR = get_app_dir()
CONFIG_FILE = APP_DIR / "config.json"


def _get_startupinfo():
    """Returns a STARTUPINFO object to hide console windows on Windows."""
    if os.name == 'nt':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def is_java_available():
    """Check if Java 11+ is available in the system."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True, startupinfo=_get_startupinfo()
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    return check_adoptium_java()


def get_short_path(long_path):
    """Returns the DOS 8.3 short path representation of a given path on Windows."""
    if os.name != 'nt':
        return long_path
    
    try:
        import ctypes
        abs_path = os.path.abspath(long_path)
        buf_size = 512
        buffer = ctypes.create_unicode_buffer(buf_size)
        
        GetShortPathName = ctypes.windll.kernel32.GetShortPathNameW
        result = GetShortPathName(abs_path, buffer, buf_size)
        
        if result == 0:
            return abs_path
        
        if result > buf_size:
            buffer = ctypes.create_unicode_buffer(result)
            GetShortPathName(abs_path, buffer, result)
            
        return buffer.value
    except Exception:
        return long_path





def refresh_path():
    """Reads system and user PATH variables directly from Windows Registry to update the active environment."""
    try:
        import winreg
        # Read system path
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
            sys_path, _ = winreg.QueryValueEx(key, "Path")
        # Read user path
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                user_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            user_path = ""
        
        full_path = sys_path + ";" + user_path
        expanded_paths = []
        for p in full_path.split(";"):
            if p:
                expanded_paths.append(os.path.expandvars(p))
        
        os.environ["PATH"] = ";".join(expanded_paths)
        return True
    except Exception as e:
        print(f"Error refreshing PATH: {e}")
        return False


def check_adoptium_java():
    """Scans standard installation paths of Eclipse Adoptium and appends it to PATH if found."""
    adoptium_dir = Path(r"C:\Program Files\Eclipse Adoptium")
    if adoptium_dir.exists():
        for bin_dir in adoptium_dir.rglob("bin"):
            java_exe = bin_dir / "java.exe"
            if java_exe.exists():
                path_env = os.environ.get("PATH", "")
                if str(bin_dir) not in path_env:
                    os.environ["PATH"] = str(bin_dir) + ";" + path_env
                return True
    return False


def find_tesseract_path():
    """Scans Windows directories to locate tesseract.exe and configure pytesseract path."""
    if pytesseract is None:
        return None
        
    # Check if globally available
    if shutil.which("tesseract"):
        return "tesseract"
        
    # Standard installation paths on Windows
    paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return p
    return None


def check_tesseract_vietnamese():
    """Checks if Vietnamese training data is available in system or local directories."""
    tess_path = find_tesseract_path()
    if tess_path and tess_path != "tesseract":
        sys_tessdata = Path(tess_path).parent / "tessdata"
        if sys_tessdata.exists() and (sys_tessdata / "vie.traineddata").exists():
            return True, str(sys_tessdata)
            
    local_tessdata = APP_DIR / "tessdata"
    if local_tessdata.exists() and (local_tessdata / "vie.traineddata").exists():
        return True, str(local_tessdata)
        
    return False, str(local_tessdata)



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
        
    default_prompt = ("Hãy chuyển đổi hình ảnh trang tài liệu này thành nội dung văn bản dưới định dạng Markdown. "
              "Giữ nguyên cấu trúc định dạng chữ, tiêu đề, danh sách, vẽ lại chính xác bảng biểu bằng bảng Markdown. "
              "Chỉ trả về Markdown thô, không thêm giải thích.")
    prompt = profile.get("prompt", "").strip()
    if not prompt:
        prompt = default_prompt
              
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
        from PySide6.QtWidgets import QScrollArea
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
        group_layout = QVBoxLayout(self.profiles_group)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("QWidget { background: transparent; }")
        self.profiles_layout = QVBoxLayout(self.scroll_widget)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.scroll_widget)
        
        group_layout.addWidget(self.scroll_area)
        self.profile_widgets = []
        layout.addWidget(self.profiles_group)
        
        add_btn = QPushButton("➕ Thêm cấu hình mới")
        add_btn.clicked.connect(lambda: self.add_profile_ui({}))
        layout.addWidget(add_btn, alignment=Qt.AlignLeft)

    def add_profile_ui(self, profile_data):
        from PySide6.QtWidgets import QFrame
        frame = QFrame()
        frame.setMinimumHeight(280)
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
        
        from PySide6.QtWidgets import QTextEdit
        prompt_edit = QTextEdit()
        prompt_edit.setPlaceholderText("Để trống sẽ dùng lệnh mặc định của phần mềm. Ví dụ: Dịch tài liệu này sang tiếng Việt...")
        prompt_edit.setText(profile_data.get("prompt", ""))
        prompt_edit.setMaximumHeight(60)
        
        headers_edit = QLineEdit(profile_data.get("headers", "{}"))
        
        del_btn = QPushButton("🗑 Xóa")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(lambda: self.remove_profile(frame))
        
        test_btn = QPushButton("🔄 Kiểm tra kết nối")
        test_btn.clicked.connect(lambda _, f=frame: self.test_connection(f))
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(test_btn)
        header_layout.addWidget(del_btn)
        
        flayout.addRow(header_layout)
        flayout.addRow("Tên hiển thị:", name_edit)
        flayout.addRow("Chuẩn kết nối:", api_type)
        flayout.addRow("Base URL:", base_url)
        flayout.addRow("Tên Model:", model_name)
        flayout.addRow("API Key:", api_key)
        flayout.addRow("Lệnh AI (Prompt):", prompt_edit)
        flayout.addRow("Custom Headers (JSON):", headers_edit)
        
        frame.data_widgets = {
            "name": name_edit,
            "api_type": api_type,
            "base_url": base_url,
            "model": model_name,
            "api_key": api_key,
            "prompt": prompt_edit,
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

    def test_connection(self, frame):
        from PySide6.QtWidgets import QMessageBox
        w = frame.data_widgets
        profile = {
            "api_type": "gemini" if w["api_type"].currentIndex() == 0 else "openai",
            "base_url": w["base_url"].text().strip(),
            "model": w["model"].text().strip(),
            "api_key": w["api_key"].text().strip(),
            "prompt": w["prompt"].toPlainText(),
            "headers": w["headers"].text().strip()
        }
        
        if not profile["api_key"]:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập API Key trước khi kiểm tra.")
            return
            
        valid, msg = validate_ai_profile(profile)
        if valid:
            QMessageBox.information(self, "Thành công", f"Kết nối thành công!\n\n{msg}")
        else:
            QMessageBox.warning(self, "Thất bại", f"Không thể kết nối đến AI:\n\n{msg}")
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
                "name": "AI (Mặc định)",
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
                "prompt": w["prompt"].toPlainText(),
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

class FileDropZone(QFrame):
    """Custom QFrame that handles drag and drop of files and folders."""
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.iconLabel = QLabel("📥", self)
        self.iconLabel.setObjectName("dropIcon")
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.iconLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.iconLabel)
        
        self.textLabel = QLabel("Kéo & thả tệp PDF/DOCX hoặc thư mục vào đây\nhoặc nhấp chuột để chọn", self)
        self.textLabel.setObjectName("dropText")
        self.textLabel.setAlignment(Qt.AlignCenter)
        self.textLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.textLabel)
        
        self.pathLabel = QLabel("", self)
        self.pathLabel.setObjectName("dropPath")
        self.pathLabel.setAlignment(Qt.AlignCenter)
        self.pathLabel.setWordWrap(True)
        self.pathLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.pathLabel)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragged", "true")
            self.textLabel.setText("Thả tệp ở đây để bắt đầu!")
            
            self.iconLabel.setText("📥")
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setProperty("dragged", "false")
        self.textLabel.setText("Kéo & thả tệp PDF/DOCX hoặc thư mục vào đây\nhoặc nhấp chuột để chọn")
        self.textLabel.setObjectName("dropText")
        self.iconLabel.setText("📥")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragged", "false")
        self.style().unpolish(self)
        self.style().polish(self)
        
        urls = event.mimeData().urls()
        if urls:
            paths = [url.toLocalFile() for url in urls]
            self.filesDropped.emit(paths)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            window = self.window()
            if hasattr(window, "browseInput"):
                window.browseInput()


class JavaInstallerWorker(QThread):
    """Background worker thread to run Java JDK installation via winget."""
    progress = Signal(str, str)
    finished = Signal(bool)

    def run(self):
        self.progress.emit("Đang khởi động trình cài đặt Java JDK 17 (Eclipse Temurin) qua winget...", "info")
        self.progress.emit("LƯU Ý: Vui lòng click 'Yes' nếu hộp thoại xác nhận Admin (UAC) hiển thị.", "warning")
        
        cmd = [
            "winget", "install", 
            "--id", "EclipseAdoptium.Temurin.17.JDK", 
            "--silent", 
            "--accept-package-agreements", 
            "--accept-source-agreements"
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=_get_startupinfo())
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.progress.emit("Cài đặt Java JDK 17 thành công!", "success")
                self.finished.emit(True)
            else:
                self.progress.emit(f"Cài đặt thất bại (mã lỗi: {process.returncode}).", "error")
                if stderr:
                    self.progress.emit(f"Chi tiết: {stderr.strip()}", "error")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Lỗi khi chạy lệnh winget: {str(e)}", "error")
            self.finished.emit(False)


class TesseractInstallerWorker(QThread):
    """Background worker thread to run Tesseract OCR installation via winget and download Vietnamese language pack."""
    progress = Signal(str, str)
    finished = Signal(bool)

    def __init__(self, tessdata_dir):
        super().__init__()
        self.tessdata_dir = tessdata_dir

    def run(self):
        self.progress.emit("Đang khởi động trình cài đặt Tesseract OCR qua winget...", "info")
        self.progress.emit("LƯU Ý: Vui lòng click 'Yes' nếu hộp thoại xác nhận Admin (UAC) hiển thị.", "warning")
        
        cmd = [
            "winget", "install", 
            "--id", "UB-Mannheim.TesseractOCR", 
            "--silent", 
            "--accept-package-agreements", 
            "--accept-source-agreements"
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=_get_startupinfo())
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.progress.emit("Cài đặt Tesseract OCR thành công!", "success")
                self.progress.emit("Bắt đầu tải bộ ngôn ngữ tiếng Việt (vie.traineddata) về thư mục dự án...", "info")
                try:
                    url = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/vie.traineddata"
                    os.makedirs(self.tessdata_dir, exist_ok=True)
                    dest_path = Path(self.tessdata_dir) / "vie.traineddata"
                    urllib.request.urlretrieve(url, str(dest_path))
                    self.progress.emit("Tải gói tiếng Việt thành công!", "success")
                    self.finished.emit(True)
                except Exception as down_err:
                    self.progress.emit(f"Không thể tải tự động gói tiếng Việt: {str(down_err)}", "error")
                    self.progress.emit("Bạn vẫn có thể OCR bằng tiếng Anh. Hãy tải thủ công file vie.traineddata sau.", "warning")
                    self.finished.emit(True)
            else:
                self.progress.emit(f"Cài đặt Tesseract thất bại (mã lỗi: {process.returncode}).", "error")
                if stderr:
                    self.progress.emit(f"Chi tiết: {stderr.strip()}", "error")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Lỗi khi chạy lệnh winget: {str(e)}", "error")
            self.finished.emit(False)
class ConversionWorker(QThread):
    """Background worker thread to handle document conversion with Tesseract/Gemini OCR support."""
    progress = Signal(int)
    progress_detail = Signal(str)
    log = Signal(str, str)
    finished = Signal(bool, int)

    def __init__(self, input_paths, formats, output_dir, ocr_mode="none", ai_profile=None, page_range=""):
        super().__init__()
        self.input_paths = input_paths
        self.formats = formats
        self.output_dir = output_dir
        self.ocr_mode = ocr_mode
        self.ai_profile = ai_profile
        self.page_range = page_range
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the conversion process."""
        self._cancelled = True

    def run(self):
        start_time = time.time()
        success_count = 0
        total_files = 0
        files_to_process = []

        for path_str in self.input_paths:
            path = Path(path_str)
            if path.is_file():
                if path.suffix.lower() in ['.pdf', '.docx']:
                    files_to_process.append(path)
            elif path.is_dir():
                for ext in ['*.pdf', '*.docx', '*.PDF', '*.DOCX']:
                    files_to_process.extend(path.rglob(ext))
        
        seen = set()
        files_to_process = [x for x in files_to_process if not (x in seen or seen.add(x))]
        total_files = len(files_to_process)

        if total_files == 0:
            self.log.emit("Không tìm thấy tệp PDF hoặc DOCX hợp lệ nào để chuyển đổi.", "error")
            self.finished.emit(False, 0)
            return

        self.log.emit(f"Bắt đầu chuyển đổi {total_files} tệp...", "info")
        
        for index, file_path in enumerate(files_to_process):
            # Check for cancellation
            if self._cancelled:
                self.log.emit(f"⚠️ Đã hủy bởi người dùng. Đã xử lý {success_count}/{index} tệp trước khi dừng.", "warning")
                self.finished.emit(False, success_count)
                return

            # File separator and info
            file_size_kb = file_path.stat().st_size / 1024
            self.log.emit(f"{'─' * 50}", "info")
            self.log.emit(f"📄 [{index+1}/{total_files}] {file_path.name}", "info")
            self.log.emit(f"   Kích thước: {file_size_kb:.1f} KB | Loại: {file_path.suffix.upper()}", "info")
            
            # Update progress detail
            self.progress_detail.emit(f"Đang xử lý: {file_path.name} ({index+1}/{total_files})")
            
            file_success = False
            
            current_out_dir = self.output_dir if self.output_dir else str(file_path.parent)
            os.makedirs(current_out_dir, exist_ok=True)
            
            try:
                if file_path.suffix.lower() == '.pdf':
                    # Hybrid OCR routing decision
                    if self.ocr_mode != "none":
                        file_success = self.convert_pdf_with_ocr(file_path, current_out_dir)
                    else:
                        file_success = self.convert_pdf_standard(file_path, current_out_dir)
                elif file_path.suffix.lower() == '.docx':
                    file_success = self.convert_docx(file_path, current_out_dir)
                
                if file_success:
                    success_count += 1
            except Exception as e:
                self.log.emit(f"Lỗi khi xử lý {file_path.name}: {str(e)}", "error")
                self.log.emit(traceback.format_exc(), "error")

            progress_pct = int(((index + 1) / total_files) * 100)
            self.progress.emit(progress_pct)

        # Timing stats
        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        self.log.emit(f"{'─' * 50}", "info")
        self.log.emit(f"Hoàn thành! Đã chuyển đổi thành công {success_count}/{total_files} tệp.", "success")
        self.log.emit(f"⏱️ Tổng thời gian xử lý: {minutes} phút {seconds} giây", "info")
        self.progress_detail.emit(f"Hoàn thành: {success_count}/{total_files} tệp — {minutes}p{seconds}s")
        self.finished.emit(success_count == total_files, success_count)

    def convert_pdf_standard(self, file_path, output_dir):
        """Standard PDF text extraction using opendataloader-pdf."""
        if opendataloader_pdf is None:
            self.log.emit("Lỗi: Thư viện 'opendataloader-pdf' chưa được cài đặt.", "error")
            return False
        
        if not is_java_available():
            self.log.emit("Lỗi: Không tìm thấy Java Runtime Environment (JRE). Vui lòng cài đặt Java 11 trở lên.", "error")
            return False

        original_stem = file_path.stem
        short_input = get_short_path(str(file_path))
        short_input_path = Path(short_input)
        short_stem = short_input_path.stem
        
        short_output_dir = get_short_path(output_dir)
        format_str = ",".join(self.formats)
        self.log.emit(f"-> Gọi OpenDataLoader PDF Standard (định dạng: {format_str})", "info")
        
        try:
            opendataloader_pdf.convert(
                input_path=[str(short_input_path)],
                output_dir=short_output_dir,
                format=format_str,
                quiet=True
            )
            
            if short_stem.lower() != original_stem.lower():
                self.log.emit("-> Khôi phục tên tệp nguyên bản có dấu tiếng Việt...", "info")
                out_dir_path = Path(output_dir)
                for out_file in out_dir_path.glob(f"{short_stem}.*"):
                    ext = out_file.suffix
                    new_name = f"{original_stem}{ext}"
                    new_file_path = out_dir_path / new_name
                    
                    try:
                        if new_file_path.exists():
                            os.remove(new_file_path)
                        os.rename(out_file, new_file_path)
                        self.log.emit(f"  Đã đổi tên: {out_file.name} -> {new_name}", "info")
                    except Exception as re_err:
                        self.log.emit(f"  Không thể đổi tên {out_file.name}: {str(re_err)}", "warning")

            self.log.emit(f"-> Thành công: Đã chuyển đổi {file_path.name}", "success")
            return True
        except subprocess.CalledProcessError as cpe:
            self.log.emit(f"-> Lỗi lệnh Java (Mã lỗi: {cpe.returncode}):", "error")
            if cpe.stdout:
                self.log.emit(f"Stdout:\n{cpe.stdout.strip()}", "error")
            if cpe.stderr:
                self.log.emit(f"Stderr:\n{cpe.stderr.strip()}", "error")
            return False
        except Exception as e:
            self.log.emit(f"-> Thất bại: {str(e)}", "error")
            return False

    def convert_pdf_with_ocr(self, file_path, output_dir):
        """Advanced PDF processing using OCR engine (Tesseract or Gemini) for scanned pages."""
        if fitz is None:
            self.log.emit("Lỗi: Thư viện 'PyMuPDF' (fitz) chưa được cài đặt. Không thể chạy tính năng OCR.", "error")
            return False

        tessdata_dir = None
        if self.ocr_mode == "tesseract":
            if pytesseract is None:
                self.log.emit("Lỗi: Thư viện 'pytesseract' chưa được cài đặt.", "error")
                return False
            tess_path = find_tesseract_path()
            if not tess_path:
                self.log.emit("Lỗi: Chưa cài đặt Tesseract OCR trên Windows. Vui lòng cài đặt thông qua thanh thông báo.", "error")
                return False
                
            has_viet, tessdata_dir = check_tesseract_vietnamese()
            if not has_viet:
                self.log.emit("-> Đang tải dữ liệu ngôn ngữ tiếng Việt (vie.traineddata) về thư mục dự án...", "info")
                try:
                    url = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/vie.traineddata"
                    os.makedirs(tessdata_dir, exist_ok=True)
                    dest_path = Path(tessdata_dir) / "vie.traineddata"
                    urllib.request.urlretrieve(url, str(dest_path))
                    self.log.emit("-> Tải ngôn ngữ tiếng Việt thành công!", "success")
                except Exception as down_err:
                    self.log.emit(f"-> Cảnh báo: Không thể tải gói tiếng Việt: {str(down_err)}. Tesseract sẽ chạy bằng tiếng Anh.", "warning")
                    tessdata_dir = None

        self.log.emit(f"-> Khởi chạy Hybrid OCR (Chế độ: {self.ocr_mode.upper()})", "info")
        
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
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
                
            target_pages = parse_page_range(getattr(self, "page_range", ""), total_pages)
            
            markdown_content = []
            ocr_errors = 0  # Track OCR failures per file
            
            # Temporary folder inside output dir to render page images
            temp_img_dir = Path(output_dir) / f"{file_path.stem}_ocr_images"
            os.makedirs(temp_img_dir, exist_ok=True)
            
            for page_num in range(total_pages):
                if page_num not in target_pages:
                    continue
                # Check for cancellation
                if self._cancelled:
                    doc.close()
                    return False
                    
                self.log.emit(f"  Đang xử lý trang {page_num + 1}/{total_pages}...", "info")
                page = doc.load_page(page_num)
                self.log.emit(f"    Trang {page_num + 1}: Chạy nhận diện OCR ({self.ocr_mode.upper()})...", "info")
                # Render page to high-quality image
                pix = page.get_pixmap(dpi=150)
                img_path = temp_img_dir / f"page_{page_num + 1}.png"
                pix.save(str(img_path))
                
                ocr_text = ""
                if self.ocr_mode == "tesseract":
                    if tessdata_dir:
                        os.environ["TESSDATA_PREFIX"] = tessdata_dir
                    try:
                        img = Image.open(str(img_path))
                        ocr_text = pytesseract.image_to_string(img, lang="vie")
                    except Exception as t_err:
                        self.log.emit(f"    Lỗi Tesseract (vie) trang {page_num + 1}: {str(t_err)}. Thử lại bằng tiếng Anh...", "warning")
                        try:
                            ocr_text = pytesseract.image_to_string(img, lang="eng")
                        except Exception as eng_err:
                            ocr_errors += 1
                            self.log.emit(f"    Lỗi Tesseract (eng) trang {page_num + 1}: {str(eng_err)}", "error")
                            ocr_text = (
                                f"\n\n> ⚠️ **Không thể nhận diện nội dung trang {page_num + 1}**\n"
                                f"> Nguyên nhân: Tesseract OCR không đọc được cả tiếng Việt lẫn tiếng Anh.\n"
                                f"> Gợi ý: Thử chuyển sang chế độ Gemini AI OCR để nhận diện chính xác hơn.\n\n"
                            )
                
                elif self.ocr_mode == "gemini":
                    try:
                        ocr_text = ocr_page_with_ai(str(img_path), self.ai_profile)
                        self.log.emit(f"    Trang {page_num + 1}: OCR AI thành công.", "success")
                    except Exception as g_err:
                        ocr_errors += 1
                        self.log.emit(f"    Lỗi AI API trang {page_num + 1} (sau 3 lần thử): {str(g_err)}", "error")
                        ocr_text = f"\n\n> ❌ **LỖI OCR trang {page_num + 1}**: {str(g_err)}\n\n"
                        
                markdown_content.append(f"## Trang {page_num + 1} (OCR - {self.ocr_mode.upper()})\n\n{ocr_text}\n\n")
            
            doc.close()
            
            # Remove the temporary images directory once done
            try:
                shutil.rmtree(temp_img_dir)
            except Exception:
                pass
            
            # Check if ALL pages failed OCR
            if ocr_errors == total_pages:
                self.log.emit(f"-> Thất bại: Tất cả {total_pages} trang đều lỗi OCR. Không xuất file.", "error")
                return False
            
            if ocr_errors > 0:
                self.log.emit(f"  Cảnh báo: {ocr_errors}/{total_pages} trang bị lỗi OCR.", "warning")
                
            # Combine content
            base_name = file_path.stem
            full_markdown = f"# {base_name}\n\n" + "".join(markdown_content)
            
            # Write requested formats
            for fmt in self.formats:
                out_path = Path(output_dir) / f"{base_name}.{fmt}"
                if fmt == "markdown":
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(full_markdown)
                    self.log.emit(f"  Exported: {out_path.name}", "info")
                
                elif fmt == "html":
                    if md_lib:
                        html_body = md_lib.markdown(full_markdown, extensions=['tables', 'fenced_code'])
                    else:
                        html_body = full_markdown.replace("\n", "<br>")
                    full_html = (
                        f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
                        f"<title>{base_name}</title>"
                        f"<style>"
                        f"body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}"
                        f"table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}"
                        f"th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}"
                        f"th {{ background-color: #f2f2f2; }}"
                        f"h1, h2, h3 {{ color: #333; }}"
                        f"code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}"
                        f"</style>"
                        f"</head><body>{html_body}</body></html>"
                    )
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(full_html)
                    self.log.emit(f"  Exported: {out_path.name}", "info")
                    
                elif fmt == "text":
                    with open(Path(output_dir) / f"{base_name}.txt", "w", encoding="utf-8") as f:
                        f.write(full_markdown)
                    self.log.emit(f"  Exported: {base_name}.txt", "info")
                    
                elif fmt == "json":
                    json_data = {
                        "file_name": file_path.name,
                        "file_type": "pdf_ocr",
                        "ocr_mode": self.ocr_mode,
                        "ocr_errors": ocr_errors,
                        "total_pages": total_pages,
                        "text": full_markdown
                    }
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    self.log.emit(f"  Exported: {out_path.name}", "info")
            
            self.log.emit(f"-> Thành công: Đã chuyển đổi {file_path.name}", "success")
            return True
        except Exception as e:
            self.log.emit(f"-> Thất bại OCR PDF: {str(e)}", "error")
            return False

    def convert_docx(self, file_path, output_dir):
        if mammoth is None or markdownify is None:
            self.log.emit("Lỗi: Thư viện 'mammoth' hoặc 'markdownify' chưa được cài đặt. Không thể chuyển đổi file DOCX.", "error")
            return False

        self.log.emit(f"-> Chuyển đổi DOCX bằng Mammoth & Markdownify (định dạng: {', '.join(self.formats)})", "info")
        
        try:
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
                
                for warning in result.messages:
                    self.log.emit(f"Cảnh báo DOCX: {warning.message}", "warning")

                base_name = file_path.stem
                
                for fmt in self.formats:
                    out_path = Path(output_dir) / f"{base_name}.{fmt}"
                    if fmt == "html":
                        full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{base_name}</title></head><body>{html_content}</body></html>"
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(full_html)
                        self.log.emit(f"  Exported: {out_path.name}", "info")
                    
                    elif fmt == "markdown":
                        md_content = markdownify.markdownify(html_content, heading_style="ATX")
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(md_content)
                        self.log.emit(f"  Exported: {out_path.name}", "info")
                        
                    elif fmt == "text" or fmt == "txt":
                        docx_file.seek(0)
                        text_result = mammoth.extract_raw_text(docx_file)
                        with open(Path(output_dir) / f"{base_name}.txt", "w", encoding="utf-8") as f:
                            f.write(text_result.value)
                        self.log.emit(f"  Exported: {base_name}.txt", "info")
                        
                    elif fmt == "json":
                        docx_file.seek(0)
                        text_result = mammoth.extract_raw_text(docx_file)
                        md_content = markdownify.markdownify(html_content, heading_style="ATX")
                        
                        json_data = {
                            "file_name": file_path.name,
                            "file_type": "docx",
                            "text": text_result.value,
                            "markdown": md_content,
                            "html": html_content
                        }
                        with open(out_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        self.log.emit(f"  Exported: {out_path.name}", "info")
            
            self.log.emit(f"-> Thành công: Đã chuyển đổi {file_path.name}", "success")
            return True
        except Exception as e:
            self.log.emit(f"-> Thất bại DOCX: {str(e)}", "error")
            return False

    def check_java(self):
        return is_java_available()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bộ Chuyển Đổi Tài Liệu PDF & DOCX")
        icon_path = APP_DIR / "icon.ico"
        if not icon_path.exists():
            icon_path = APP_DIR / "icon.png"
        if not icon_path.exists():
            icon_path = APP_DIR / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(750, 750)
        self.setMinimumSize(600, 650)
        
        self.input_paths = []
        self.worker = None
        self.java_installer_worker = None
        self.tesseract_installer_worker = None

        self.setup_styles()
        
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        
        central_widget = QWidget()
        central_widget.setObjectName("mainCentralWidget")
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Header Section
        header_layout = QHBoxLayout()
        
        logo_path = APP_DIR / "logo.png"
        if not logo_path.exists():
            logo_path = APP_DIR / "icon.png"
        if logo_path.exists():
            logo_label = QLabel(self)
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            header_layout.addWidget(logo_label)
            
        title_container = QVBoxLayout()
        
        self.titleLabel = QLabel("OpenDataLoader Document Converter", self)
        self.titleLabel.setObjectName("titleLabel")
        title_container.addWidget(self.titleLabel)
        
        self.subtitleLabel = QLabel("Chuyển đổi PDF và Word (DOCX) sang định dạng Markdown, JSON, HTML, Text chất lượng cao", self)
        self.subtitleLabel.setObjectName("subtitleLabel")
        title_container.addWidget(self.subtitleLabel)
        
        header_layout.addLayout(title_container)
        
        # Java indicator icon
        self.javaStatusLabel = QLabel(self)
        self.javaStatusLabel.setObjectName("javaStatus")
        header_layout.addWidget(self.javaStatusLabel)
        header_layout.setAlignment(self.javaStatusLabel, Qt.AlignVCenter)
        
        from PySide6.QtWidgets import QPushButton
        self.btnThemeToggle = QPushButton("🌙 Giao diện tối")
        self.btnThemeToggle.setCheckable(True)
        self.btnThemeToggle.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btnThemeToggle)
        
        main_layout.addLayout(header_layout)

        # Java Warning Banner
        self.javaWarningBanner = QFrame(self)
        self.javaWarningBanner.setObjectName("warningBanner")
        
        banner_layout = QHBoxLayout(self.javaWarningBanner)
        banner_layout.setContentsMargins(10, 4, 10, 4)
        
        self.bannerLabel = QLabel("⚠️ Để chuyển đổi PDF thường, cần Java 11+. Bạn có muốn tự động cài đặt Java JDK 17 (via winget)?", self)
        self.bannerLabel.setObjectName("warnText")
        banner_layout.addWidget(self.bannerLabel, stretch=4)
        
        self.btnAutoInstallJava = QPushButton("Cài đặt Java Tự Động", self)
        self.btnAutoInstallJava.setObjectName("installJavaBtn")
        self.btnAutoInstallJava.setObjectName("installBtn")
        self.btnAutoInstallJava.clicked.connect(self.auto_install_java)
        banner_layout.addWidget(self.btnAutoInstallJava, stretch=1)
        
        self.btnManualDownloadJava = QPushButton("Tải Thủ Công", self)
        self.btnManualDownloadJava.setObjectName("manualJavaBtn")
        self.btnManualDownloadJava.setObjectName("manualBtn")
        self.btnManualDownloadJava.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://adoptium.net/")))
        banner_layout.addWidget(self.btnManualDownloadJava, stretch=1)
        
        main_layout.addWidget(self.javaWarningBanner)

        # Tesseract OCR Warning Banner (Hidden by default, shown if Tesseract is missing when selected)
        self.tessWarningBanner = QFrame(self)
        self.tessWarningBanner.setObjectName("tessWarningBanner")
        
        tess_banner_layout = QHBoxLayout(self.tessWarningBanner)
        tess_banner_layout.setContentsMargins(10, 4, 10, 4)
        
        self.tessBannerLabel = QLabel("⚠️ Chưa tìm thấy Tesseract OCR. Cài đặt tự động để sử dụng tính năng OCR ngoại tuyến?", self)
        self.tessBannerLabel.setObjectName("infoText")
        tess_banner_layout.addWidget(self.tessBannerLabel, stretch=4)
        
        self.btnAutoInstallTess = QPushButton("Cài đặt Tesseract OCR", self)
        self.btnAutoInstallTess.setObjectName("installTessBtn")
        self.btnAutoInstallTess.setObjectName("installTessBtn")
        self.btnAutoInstallTess.clicked.connect(self.auto_install_tesseract)
        tess_banner_layout.addWidget(self.btnAutoInstallTess, stretch=1)
        
        main_layout.addWidget(self.tessWarningBanner)
        self.tessWarningBanner.hide()

        # Drop Zone (Interactive)
        self.dropZone = FileDropZone(self)
        self.dropZone.filesDropped.connect(self.handle_files_input)
        main_layout.addWidget(self.dropZone, stretch=3)

        # Configuration Panel
        config_frame = QFrame(self)
        config_frame.setObjectName("configFrame")
        config_layout = QGridLayout(config_frame)
        config_layout.setContentsMargins(15, 12, 15, 12)
        config_layout.setSpacing(10)

        # 1. Output Formats
        config_layout.addWidget(QLabel("<b>Định dạng đầu ra:</b>", self), 0, 0)
        format_layout = QHBoxLayout()
        self.cbMarkdown = QCheckBox("Markdown (.md)", self)
        self.cbMarkdown.setChecked(True)
        self.cbJson = QCheckBox("JSON (.json)", self)
        self.cbHtml = QCheckBox("HTML (.html)", self)
        self.cbText = QCheckBox("Text (.txt)", self)
        
        format_layout.addWidget(self.cbMarkdown)
        format_layout.addWidget(self.cbJson)
        format_layout.addWidget(self.cbHtml)
        format_layout.addWidget(self.cbText)
        format_layout.addStretch()
        config_layout.addLayout(format_layout, 0, 1)

        # 2. PDF Processing Mode (Standard, Tesseract OCR, Gemini OCR)
        config_layout.addWidget(QLabel("<b>Chế độ xử lý PDF:</b>", self), 1, 0)
        ocr_layout = QHBoxLayout()
        self.ocrCombo = QComboBox(self)
        self.ocrCombo.addItems([
            "Không sử dụng OCR (Chỉ trích xuất text gốc từ PDF số)",
            "OCR Ngoại tuyến (Sử dụng Tesseract OCR - Miễn phí, offline)",
            "OCR Trí tuệ nhân tạo (Sử dụng AI API - Độ chính xác cao)"
        ])
        
        self.ocrCombo.currentIndexChanged.connect(self.handle_ocr_mode_change)
        self.btnSettings = QPushButton('⚙️ Cài đặt')
        self.btnSettings.clicked.connect(self.open_settings)
        config_layout.addWidget(self.btnSettings, 1, 2)
        ocr_layout.addWidget(self.ocrCombo, stretch=2)
        config_layout.addLayout(ocr_layout, 1, 1)

        # 3. Gemini Key Input (Only shown when Gemini mode is active)
        self.geminiKeyLabel = QLabel("<b>Cấu hình AI:</b>", self)
        config_layout.addWidget(self.geminiKeyLabel, 2, 0)
        
        self.geminiKeyEdit = QLabel("Chưa chọn cấu hình", self)
        self.geminiKeyEdit.setStyleSheet("color: #2d3a8c; font-weight: bold;")
        
        
        config_layout.addWidget(self.geminiKeyEdit, 2, 1)
        
        self.geminiKeyLabel.hide()
        self.geminiKeyEdit.hide()

        # 4. Output Path
        config_layout.addWidget(QLabel("<b>Thư mục đầu ra:</b>", self), 3, 0)
        out_path_layout = QHBoxLayout()
        self.outPathEdit = QLineEdit(self)
        self.outPathEdit.setPlaceholderText("Mặc định: Cùng thư mục với file nguồn")
        self.outPathEdit.setReadOnly(True)
        
        
        self.btnBrowseOut = QPushButton("Chọn thư mục", self)
        self.btnBrowseOut.setObjectName("browseBtn")
        self.btnBrowseOut.clicked.connect(self.browse_output_dir)
        
        self.btnClearOut = QPushButton("Clear", self)
        self.btnClearOut.setObjectName("browseBtn")
        self.btnClearOut.clicked.connect(self.clear_output_dir)
        
        out_path_layout.addWidget(self.outPathEdit)
        out_path_layout.addWidget(self.btnBrowseOut)
        out_path_layout.addWidget(self.btnClearOut)
        config_layout.addLayout(out_path_layout, 3, 1)

        # 5. Page Range
        config_layout.addWidget(QLabel("<b>Trang trích xuất:</b>", self), 4, 0)
        self.pageRangeEdit = QLineEdit(self)
        self.pageRangeEdit.setPlaceholderText("VD: 1-5, 8, 11-13 (Để trống để xử lý tất cả)")
        config_layout.addWidget(self.pageRangeEdit, 4, 1)


        main_layout.addWidget(config_frame)

        # Progress bar and label
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        main_layout.addWidget(self.progressBar)
        
        self.progressLabel = QLabel("", self)
        self.progressLabel.setObjectName("progressLabel")
        self.progressLabel.setObjectName("progressLabel")
        main_layout.addWidget(self.progressLabel)

        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.btnBrowseFile = QPushButton("📁 Chọn File", self)
        self.btnBrowseFile.setObjectName("actionBtnSecondary")
        self.btnBrowseFile.clicked.connect(self.browse_input_file)
        
        self.btnBrowseFolder = QPushButton("📁 Chọn Thư Mục", self)
        self.btnBrowseFolder.setObjectName("actionBtnSecondary")
        self.btnBrowseFolder.clicked.connect(self.browse_input_folder)
        
        self.btnConvert = QPushButton("🚀 CHUYỂN ĐỔI", self)
        self.btnConvert.setObjectName("convertBtn")
        self.btnConvert.clicked.connect(self.start_conversion)
        
        self.btnCancel = QPushButton("❌ HỦY", self)
        self.btnCancel.setObjectName("cancelBtn")
        
        self.btnCancel.clicked.connect(self.cancel_conversion)
        self.btnCancel.setEnabled(False)
        
        button_layout.addWidget(self.btnBrowseFile)
        button_layout.addWidget(self.btnBrowseFolder)
        button_layout.addWidget(self.btnConvert, stretch=2)
        button_layout.addWidget(self.btnCancel)
        main_layout.addLayout(button_layout)

        # Tab Widget for Log and Preview
        from PySide6.QtWidgets import QTabWidget, QTextBrowser
        self.bottomTabs = QTabWidget()
        self.logTab = QWidget()
        self.previewTab = QWidget()
        
        log_layout = QVBoxLayout(self.logTab)
        log_layout.setContentsMargins(0,0,0,0)
        self.logConsole = QTextBrowser(self)
        self.logConsole.setObjectName("logConsole")
        self.logConsole.setReadOnly(True)
        log_layout.addWidget(self.logConsole)
        
        preview_layout = QVBoxLayout(self.previewTab)
        preview_layout.setContentsMargins(0,0,0,0)
        self.previewBrowser = QTextBrowser(self)
        self.previewBrowser.setOpenExternalLinks(True)
        self.previewBrowser.setObjectName("previewBrowser")
        preview_layout.addWidget(self.previewBrowser)
        
        self.bottomTabs.addTab(self.logTab, "📝 Nhật ký xử lý")
        self.bottomTabs.addTab(self.previewTab, "👀 Xem trước kết quả")
        
        main_layout.addWidget(self.bottomTabs, stretch=2)

        # Status Bar
        status_bar = self.statusBar()
        
        status_bar.showMessage("✨ Sẵn sàng — Kéo thả hoặc chọn tệp để bắt đầu")

        # Startup checks
        if self.check_java_status():
            self.javaWarningBanner.hide()
        
        self.check_dependencies_on_startup()
        self.load_config()

    def toggle_theme(self):
        config = getattr(self, "app_config", {})
        config["dark_mode"] = self.btnThemeToggle.isChecked()
        self.app_config = config
        self.save_config()
        self.setup_styles()
        
    def setup_styles(self):
        is_dark = getattr(self, "app_config", {}).get("dark_mode", False)
        if hasattr(self, "btnThemeToggle"):
            self.btnThemeToggle.setChecked(is_dark)
            self.btnThemeToggle.setText("☀️ Giao diện sáng" if is_dark else "🌙 Giao diện tối")
        
        if is_dark:
            bg_color = "#0f172a"
            panel_bg = "#1e293b"
            text_color = "#f8fafc"
            subtext_color = "#94a3b8"
            border_color = "#334155"
            primary_color = "#3b82f6"
            primary_hover = "#2563eb"
            success_bg = "#064e3b"
            success_text = "#34d399"
            danger_bg = "#7f1d1d"
            danger_text = "#f87171"
            input_bg = "#0f172a"
        else:
            bg_color = "#f8fafc"
            panel_bg = "#ffffff"
            text_color = "#1e293b"
            subtext_color = "#475569"
            border_color = "#cbd5e1"
            primary_color = "#2d3a8c"
            primary_hover = "#1e2865"
            success_bg = "#eff6ff"
            success_text = "#2d3a8c"
            danger_bg = "#fef2f2"
            danger_text = "#e52b2d"
            input_bg = "#ffffff"
            
        qss = f"""
        QMainWindow, QWidget#mainCentralWidget, QScrollArea {{ background-color: {bg_color}; }}
        QDialog {{ background-color: {bg_color}; }}
        QWidget {{ color: {text_color}; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; font-size: 13px; }}
        
        QFrame#dropZone {{ background-color: {panel_bg}; border: 2px dashed {subtext_color}; border-radius: 12px; margin: 2px; }}
        QFrame#dropZone:hover {{ border: 2px dashed {primary_color}; background-color: {success_bg}; }}
        QFrame#dropZone[dragged="true"] {{ border: 2px solid {danger_text}; background-color: {danger_bg}; }}
        
        QLabel#dropIcon {{ font-size: 48px; color: {primary_color}; background: transparent; }}
        QLabel#dropText {{ font-size: 14px; font-weight: 500; color: {subtext_color}; background: transparent; }}
        QFrame#dropZone[dragged="true"] QLabel#dropText {{ color: {danger_text}; font-size: 16px; font-weight: bold; }}
        QLabel#dropPath {{ font-size: 12px; color: {primary_color}; font-weight: bold; background: transparent; }}
        
        QFrame#configFrame {{ background-color: {panel_bg}; border: 1px solid {border_color}; border-radius: 10px; }}
        QLabel#titleLabel {{ font-size: 22px; font-weight: bold; color: {danger_text}; }}
        QLabel#subtitleLabel {{ font-size: 13px; color: {subtext_color}; }}
        
        QLabel#javaStatus {{ font-size: 12px; padding: 6px 12px; border-radius: 12px; border: 1px solid transparent; }}
        QLabel#javaStatus[status="ok"] {{ background-color: {success_bg}; color: {success_text}; border-color: {success_text}; }}
        QLabel#javaStatus[status="warn"] {{ background-color: {danger_bg}; color: {danger_text}; border-color: {danger_text}; }}
        
        QFrame#warningBanner {{ background-color: {danger_bg}; border: 1px solid {danger_text}; border-radius: 8px; }}
        QLabel#warnText {{ color: {danger_text}; font-weight: bold; }}
        
        QFrame[objectName="tessWarningBanner"] {{ background-color: {success_bg}; border: 1px solid {primary_color}; border-radius: 8px; }}
        QLabel#infoText {{ color: {primary_color}; font-weight: bold; }}
        
        QPushButton {{ background-color: {panel_bg}; color: {text_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px 16px; font-weight: 500; }}
        QPushButton:hover {{ background-color: {border_color}; }}
        
        QPushButton#installBtn, QPushButton#installTessBtn {{
            background-color: {panel_bg}; color: {primary_color}; font-weight: 600; border: 1px solid {primary_color}; border-radius: 6px; padding: 5px 10px;
        }}
        QPushButton#installBtn:hover, QPushButton#installTessBtn:hover {{ background-color: {success_bg}; }}
        
        QPushButton#manualBtn {{ background-color: transparent; color: {subtext_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 5px 10px; }}
        
        QPushButton#convertBtn {{ background: {primary_color}; color: #ffffff; font-weight: bold; border: none; border-radius: 8px; padding: 12px; font-size: 14px; }}
        QPushButton#convertBtn:hover {{ background: {primary_hover}; }}
        QPushButton#convertBtn:disabled {{ background-color: {border_color}; color: {subtext_color}; }}
        
        QPushButton#cancelBtn {{ background-color: {panel_bg}; color: {danger_text}; font-weight: bold; border: 2px solid {danger_text}; border-radius: 8px; padding: 8px 16px; font-size: 13px; }}
        QPushButton#cancelBtn:hover {{ background-color: {danger_bg}; }}
        QPushButton#cancelBtn:disabled {{ border-color: {border_color}; color: {subtext_color}; }}
        
        QPushButton#browseBtn, QPushButton#actionBtnSecondary {{ background-color: {panel_bg}; border: 1px solid {border_color}; border-radius: 8px; padding: 8px 16px; color: {text_color}; font-weight: 500; }}
        
        QLineEdit, QComboBox, QSpinBox, QTextEdit {{ background-color: {input_bg}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px; color: {text_color}; }}
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border: 1px solid {primary_color}; }}
        
        QComboBox QAbstractItemView {{ background-color: {panel_bg}; color: {text_color}; selection-background-color: {primary_color}; selection-color: #ffffff; border: 1px solid {border_color}; }}
        
        QTextBrowser#logConsole {{ background-color: #000000; color: #00ff00; border: 1px solid {border_color}; border-radius: 8px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; padding: 8px; }}
        QTextBrowser#previewBrowser {{ background-color: {panel_bg}; color: {text_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 12px; }}
        
        QStatusBar {{ background-color: {panel_bg}; color: {subtext_color}; border-top: 1px solid {border_color}; font-size: 11px; padding: 2px 8px; }}
        
        QProgressBar {{ border: none; background-color: {border_color}; height: 8px; border-radius: 4px; }}
        QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffe700, stop:1 {danger_text}); border-radius: 4px; }}
        QLabel#progressLabel {{ color: {subtext_color}; font-size: 11px; padding: 0 4px; }}
        
        QCheckBox {{ color: {text_color}; }}
        
        QGroupBox {{ border: 1px solid {border_color}; border-radius: 6px; margin-top: 10px; padding-top: 15px; font-weight: bold; color: {primary_color}; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        
        QTabWidget::pane {{ border: 1px solid {border_color}; background: {panel_bg}; border-radius: 4px; }}
        QTabBar::tab {{ padding: 8px 16px; background: {border_color}; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; color: {subtext_color}; }}
        QTabBar::tab:selected {{ background: {panel_bg}; border: 1px solid {border_color}; border-bottom: none; font-weight: bold; color: {primary_color}; }}
        
        QMessageBox {{ background-color: {panel_bg}; }}
        QMessageBox QLabel {{ color: {text_color}; }}
        QMessageBox QPushButton {{ background-color: {primary_color}; color: #ffffff; border: none; border-radius: 4px; padding: 6px 16px; min-width: 60px; }}
        QMessageBox QPushButton:hover {{ background-color: {primary_hover}; }}
        """
        self.setStyleSheet(qss)
        
        if hasattr(self, "apply_config_ui"):
            self.apply_config_ui()

    def write_log(self, text, log_type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": "#e5e7eb",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444"
        }
        icon_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        color = color_map.get(log_type, "#e5e7eb")
        icon = icon_map.get(log_type, "")
        log_html = (
            f"<span style='color: #6b7280; font-size: 11px;'>[{timestamp}]</span> "
            f"<span style='color: {color};'>{icon} {text}</span>"
        )
        self.logConsole.append(log_html)
        
        scrollbar = self.logConsole.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def check_java_status(self):
        if is_java_available():
            self.javaStatusLabel.setText("☕ Java: Sẵn sàng")
            self.javaStatusLabel.setProperty("status", "ok"); self.javaStatusLabel.style().unpolish(self.javaStatusLabel); self.javaStatusLabel.style().polish(self.javaStatusLabel)
            return True

        self.javaStatusLabel.setText("⚠️ Java: Chưa tìm thấy")
        self.javaStatusLabel.setProperty("status", "warn"); self.javaStatusLabel.style().unpolish(self.javaStatusLabel); self.javaStatusLabel.style().polish(self.javaStatusLabel)
        self.write_log("Không tìm thấy Java JRE/JDK 11+ trên hệ thống.", "warning")
        self.write_log("Thư viện OpenDataLoader PDF yêu cầu Java để chuyển đổi tệp PDF thông thường.", "warning")
        return False


    def open_settings(self):
        dialog = SettingsDialog(self, getattr(self, "app_config", {}))
        if dialog.exec():
            self.save_config()
            self.apply_config_ui()
            
    def get_active_ai_profile(self):
        config = getattr(self, "app_config", {})
        active_id = config.get("active_ai_profile_id", "")
        for p in config.get("ai_profiles", []):
            if p.get("id") == active_id:
                return p
        return {}

    def apply_config_ui(self):
        config = getattr(self, "app_config", {})
        ui_set = config.get("ui_settings", {})
        font_family = ui_set.get("font_family", "Segoe UI")
        font_size = ui_set.get("font_size", 13)
        self.setStyleSheet(self.styleSheet().replace("font-family: 'Segoe UI'", f"font-family: '{font_family}'").replace("font-size: 13px;", f"font-size: {font_size}px;"))
        
        p = self.get_active_ai_profile()
        if hasattr(self, "geminiKeyEdit"):
            self.geminiKeyEdit.setText(p.get("name", "Chưa cấu hình"))

    def handle_ocr_mode_change(self, index):
        # Index 0: No OCR, Index 1: Tesseract, Index 2: Gemini
        if index == 2:
            self.geminiKeyLabel.show()
            self.geminiKeyEdit.show()
            self.tessWarningBanner.hide()
        else:
            self.geminiKeyLabel.hide()
            self.geminiKeyEdit.hide()
            
            if index == 1:
                # Check Tesseract path
                tess_path = find_tesseract_path()
                if not tess_path:
                    self.tessWarningBanner.show()
                else:
                    self.tessWarningBanner.hide()
            else:
                self.tessWarningBanner.hide()

    def auto_install_java(self):
        self.btnAutoInstallJava.setEnabled(False)
        self.btnManualDownloadJava.setEnabled(False)
        self.bannerLabel.setText("⏳ Đang cài đặt Java JDK 17... Vui lòng đồng ý với hộp thoại UAC (nếu xuất hiện).")
        self.write_log("Bắt đầu cài đặt Java JDK 17...", "info")
        
        self.java_installer_worker = JavaInstallerWorker()
        self.java_installer_worker.progress.connect(self.write_log)
        self.java_installer_worker.finished.connect(self.java_install_finished)
        self.java_installer_worker.start()

    def java_install_finished(self, success):
        self.btnAutoInstallJava.setEnabled(True)
        self.btnManualDownloadJava.setEnabled(True)
        
        if success:
            self.write_log("Đang làm mới danh sách biến môi trường PATH từ Registry...", "info")
            refresh_path()
            if self.check_java_status():
                self.javaWarningBanner.hide()
                self.write_log("Java đã sẵn sàng hoạt động! Bạn đã có thể chuyển đổi tệp PDF.", "success")
                QMessageBox.information(self, "Cài đặt thành công", "Java JDK 17 đã được cài đặt thành công!")
            else:
                self.write_log("Cài đặt Java thành công nhưng PATH chưa kịp cập nhật. Bạn nên khởi động lại ứng dụng.", "warning")
        else:
            self.bannerLabel.setText("⚠️ Cài đặt tự động thất bại. Vui lòng tự cài đặt thủ công.")
            QMessageBox.critical(self, "Lỗi cài đặt", "Không thể tự động cài đặt Java qua winget.")

    def auto_install_tesseract(self):
        self.btnAutoInstallTess.setEnabled(False)
        self.tessBannerLabel.setText("⏳ Đang cài đặt Tesseract OCR... Vui lòng đồng ý với hộp thoại UAC (nếu xuất hiện).")
        self.write_log("Bắt đầu cài đặt Tesseract OCR và bộ tiếng Việt...", "info")
        
        local_tessdata = APP_DIR / "tessdata"
        self.tesseract_installer_worker = TesseractInstallerWorker(str(local_tessdata))
        self.tesseract_installer_worker.progress.connect(self.write_log)
        self.tesseract_installer_worker.finished.connect(self.tesseract_install_finished)
        self.tesseract_installer_worker.start()

    def tesseract_install_finished(self, success):
        self.btnAutoInstallTess.setEnabled(True)
        if success:
            # Refresh path to find newly installed Tesseract command
            refresh_path()
            tess_path = find_tesseract_path()
            if tess_path:
                self.tessWarningBanner.hide()
                self.write_log("Tesseract OCR đã sẵn sàng hoạt động ngoại tuyến!", "success")
                QMessageBox.information(self, "Thành công", "Tesseract OCR đã được cài đặt và cấu hình thành công!")
            else:
                self.write_log("Cài đặt Tesseract thành công nhưng hệ thống chưa ghi nhận. Vui lòng khởi động lại ứng dụng.", "warning")
        else:
            self.tessBannerLabel.setText("⚠️ Cài đặt Tesseract tự động thất bại.")
            QMessageBox.critical(self, "Lỗi cài đặt", "Không thể cài đặt Tesseract OCR tự động qua winget.")

    def browse_input_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Chọn tệp cần chuyển đổi", 
            "", 
            "Tài liệu (*.pdf *.docx)"
        )
        if file_paths:
            self.handle_files_input(file_paths)

    def browse_input_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa tài liệu")
        if dir_path:
            self.handle_files_input([dir_path])

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu kết quả")
        if dir_path:
            self.outPathEdit.setText(dir_path)

    def clear_output_dir(self):
        self.outPathEdit.clear()

    def browseInput(self):
        self.browse_input_file()

    def handle_files_input(self, paths):
        if not paths:
            return
        
        self.input_paths = paths
        
        if len(paths) == 1:
            path = Path(paths[0])
            if path.is_file():
                self.dropZone.textLabel.setText(f"Tệp đã chọn: {path.name}")
                self.dropZone.pathLabel.setText(str(path))
                self.write_log(f"Đã chọn tệp: {path}", "info")
            else:
                self.dropZone.textLabel.setText(f"Thư mục đã chọn: {path.name}")
                self.dropZone.pathLabel.setText(str(path))
                self.write_log(f"Đã chọn thư mục: {path}", "info")
        else:
            self.dropZone.textLabel.setText(f"Đã chọn {len(paths)} mục")
            self.dropZone.pathLabel.setText(", ".join([Path(p).name for p in paths]))
            self.write_log(f"Đã chọn {len(paths)} tài liệu/thư mục", "info")

    def start_conversion(self):
        if not self.input_paths:
            QMessageBox.warning(self, "Chưa chọn tài liệu", "Vui lòng chọn hoặc kéo thả tệp/thư mục cần chuyển đổi trước.")
            return

        formats = []
        if self.cbMarkdown.isChecked():
            formats.append("markdown")
        if self.cbJson.isChecked():
            formats.append("json")
        if self.cbHtml.isChecked():
            formats.append("html")
        if self.cbText.isChecked():
            formats.append("text")

        if not formats:
            QMessageBox.warning(self, "Chưa chọn định dạng", "Vui lòng chọn ít nhất một định dạng đầu ra.")
            return

        # Parse OCR options
        ocr_idx = self.ocrCombo.currentIndex()
        ocr_mode = "none"
        if ocr_idx == 1:
            ocr_mode = "tesseract"
        elif ocr_idx == 2:
            ocr_mode = "gemini"

        active_profile = None
        gemini_key = ""
        if ocr_mode == "gemini":
            gemini_key = "profile"
            active_profile = self.get_active_ai_profile()
            if not active_profile.get("api_key"):
                QMessageBox.warning(self, "Chưa cấu hình AI", "Vui lòng vào Cài đặt để thêm và chọn cấu hình AI.")
                return
            # Validate Gemini API Key
            self.statusBar().showMessage("🔍 Đang xác thực API Key...")
            key_valid, key_msg = validate_ai_profile(active_profile)
            if not key_valid:
                QMessageBox.warning(self, "API Key không hợp lệ", f"{key_msg}\n\nVui lòng kiểm tra lại API Key của bạn.")
                self.statusBar().showMessage("❌ API Key không hợp lệ")
                return
            self.write_log("API Key hợp lệ - Sẵn sàng quét tài liệu.", "success")

        output_dir = self.outPathEdit.text().strip()

        # Check Java only if standard PDF mode (No OCR) is used for PDF files
        has_pdf = False
        for path_str in self.input_paths:
            path = Path(path_str)
            if path.is_file() and path.suffix.lower() == '.pdf':
                has_pdf = True
                break
            elif path.is_dir():
                has_pdf = True
                break

        if has_pdf and ocr_mode == "none":
            if not is_java_available():
                reply = QMessageBox.question(
                    self, 
                    "Không tìm thấy Java",
                    "Thư viện OpenDataLoader PDF yêu cầu Java 11+ để chuyển đổi tệp PDF thường.\n\n"
                    "Bạn có muốn tự động cài đặt Java JDK 17 ngay bây giờ không?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.auto_install_java()
                return

        # Check Tesseract if OCR Tesseract mode is selected
        if has_pdf and ocr_mode == "tesseract":
            tess_path = find_tesseract_path()
            if not tess_path:
                reply = QMessageBox.question(
                    self, 
                    "Không tìm thấy Tesseract OCR",
                    "Chế độ OCR Offline yêu cầu Tesseract OCR được cài đặt trên máy của bạn.\n\n"
                    "Bạn có muốn tự động cài đặt Tesseract OCR và gói ngôn ngữ tiếng Việt ngay bây giờ không?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.auto_install_tesseract()
                    return
                else:
                    return

        # Prepare GUI for processing
        self.btnConvert.setEnabled(False)
        self.btnBrowseFile.setEnabled(False)
        self.btnBrowseFolder.setEnabled(False)
        self.btnCancel.setEnabled(True)
        self.progressBar.setValue(0)
        self.progressLabel.setText("")
        self.logConsole.clear()
        self.statusBar().showMessage("⏳ Đang chuyển đổi...")

        # Start Worker Thread
        self.worker = ConversionWorker(
            input_paths=self.input_paths,
            formats=formats,
            output_dir=output_dir,
            ocr_mode=ocr_mode,
            ai_profile=active_profile,
            page_range=getattr(self, "pageRangeEdit", None) and self.pageRangeEdit.text() or ""
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.progress_detail.connect(self.update_progress_detail)
        self.worker.log.connect(self.write_log)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    @Slot(int)
    def update_progress(self, val):
        self.progressBar.setValue(val)

    @Slot(str)
    def update_progress_detail(self, text):
        self.progressLabel.setText(text)

    def cancel_conversion(self):
        """Cancel the running conversion."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.btnCancel.setEnabled(False)
            self.write_log("Đang hủy quá trình chuyển đổi...", "warning")
            self.statusBar().showMessage("⚠️ Đang hủy...")

    @Slot(bool, int)
    def conversion_finished(self, success, count):
        output_dir = self.outPathEdit.text().strip()
        if not output_dir and getattr(self, "input_paths", []):
            from pathlib import Path
            first_path = Path(self.input_paths[0])
            output_dir = str(first_path.parent if first_path.is_file() else first_path)
            
        if output_dir:
            from pathlib import Path
            import markdown
            for f in Path(output_dir).glob("*.md"):
                try:
                    with open(f, "r", encoding="utf-8") as md_file:
                        html = markdown.markdown(md_file.read(), extensions=["tables", "fenced_code"])
                        if hasattr(self, "previewBrowser"):
                            self.previewBrowser.setHtml(html)
                            self.bottomTabs.setCurrentWidget(self.previewTab)
                        break
                except Exception as e: 
                    self.write_log(f"Lỗi preview: {e}", "warning")

        self.btnConvert.setEnabled(True)
        self.btnBrowseFile.setEnabled(True)
        self.btnBrowseFolder.setEnabled(True)
        self.btnCancel.setEnabled(False)
        
        # Determine output directory for "Open folder" action
        output_dir = self.outPathEdit.text().strip()
        if not output_dir and self.input_paths:
            first_path = Path(self.input_paths[0])
            output_dir = str(first_path.parent if first_path.is_file() else first_path)
        
        if success:
            self.statusBar().showMessage(f"✅ Hoàn thành thành công {count} tệp")
            reply = QMessageBox.question(
                self, 
                "Hoàn thành", 
                f"Đã chuyển đổi thành công toàn bộ {count} tệp!\n\nBạn có muốn mở thư mục kết quả?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes and output_dir:
                QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
        else:
            self.statusBar().showMessage(f"⚠️ Hoàn thành với cảnh báo — {count} tệp thành công")
            reply = QMessageBox.warning(
                self, 
                "Hoàn thành kèm cảnh báo", 
                f"Quá trình hoàn tất. Có tệp chuyển đổi lỗi.\nĐã xử lý thành công: {count} tệp.\n\nBạn có muốn mở thư mục kết quả?"
            )

    def check_dependencies_on_startup(self):
        """Check and warn about missing optional libraries at startup."""
        missing = []
        if opendataloader_pdf is None:
            missing.append(("opendataloader-pdf", "Chuyển đổi PDF cơ bản"))
        if mammoth is None:
            missing.append(("mammoth", "Chuyển đổi DOCX"))
        if markdownify is None:
            missing.append(("markdownify", "Xuất định dạng Markdown từ DOCX"))
        if fitz is None:
            missing.append(("PyMuPDF", "OCR & xử lý PDF nâng cao"))
        if md_lib is None:
            missing.append(("markdown", "Xuất HTML chuẩn từ Markdown"))
        
        if missing:
            self.write_log("━━━ Kiểm tra thư viện ━━━", "info")
            for lib, purpose in missing:
                self.write_log(f"Thiếu '{lib}' — Tính năng: {purpose}", "warning")
                self.write_log(f"   → Cài đặt: pip install {lib}", "info")
            self.write_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")

    def save_config(self):
        """Save user configuration to JSON file."""
        try:
            if not hasattr(self, "app_config"):
                self.app_config = {}
            self.app_config.update({
                "formats": {
                    "markdown": self.cbMarkdown.isChecked(),
                    "json": self.cbJson.isChecked(),
                    "html": self.cbHtml.isChecked(),
                    "text": self.cbText.isChecked(),
                },
                "ocr_mode": self.ocrCombo.currentIndex(),
                "output_dir": self.outPathEdit.text(),
                "page_range": getattr(self, "pageRangeEdit", None) and self.pageRangeEdit.text() or "",
                "dark_mode": self.app_config.get("dark_mode", False),
                "window_size": {
                    "width": self.width(),
                    "height": self.height(),
                }
            })
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.app_config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_config(self):
        """Load user configuration from JSON file."""
        self.app_config = {}
        try:
            if not CONFIG_FILE.exists():
                return
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.app_config = json.load(f)
                config = self.app_config
                self.apply_config_ui()
            
            formats = config.get("formats", {})
            self.cbMarkdown.setChecked(formats.get("markdown", True))
            self.cbJson.setChecked(formats.get("json", False))
            self.cbHtml.setChecked(formats.get("html", False))
            self.cbText.setChecked(formats.get("text", False))
            
            ocr_mode = config.get("ocr_mode", 0)
            self.ocrCombo.setCurrentIndex(ocr_mode)
            
            output_dir = config.get("output_dir", "")
            if output_dir:
                self.outPathEdit.setText(output_dir)
            
            if "page_range" in config and hasattr(self, "pageRangeEdit"):
                page_range = config.get("page_range", "")
                self.pageRangeEdit.setText(page_range)
            
            window_size = config.get("window_size", {})
            w = window_size.get("width", 750)
            h = window_size.get("height", 750)
            self.resize(w, h)
            self.setup_styles()
        except Exception:
            pass

    def closeEvent(self, event):
        """Save configuration when the window is closed."""
        self.save_config()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    
    # Handle files dropped directly onto exe icon at launch
    if len(sys.argv) > 1:
        dropped_files = sys.argv[1:]
        window.handle_files_input(dropped_files)
        
    window.show()
    sys.exit(app.exec())
