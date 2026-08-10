import re
import os
from pathlib import Path

file_path = "openloader.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports for QIcon
if "QIcon" not in content:
    content = content.replace("from PySide6.QtGui import QFont, QColor", "from PySide6.QtGui import QIcon, QFont, QColor")

# 2. Add window icon setup in MainWindow.__init__
if "self.setWindowIcon" not in content:
    content = content.replace(
        'self.setWindowTitle("Bộ Chuyển Đổi Tài Liệu PDF & DOCX")',
        'self.setWindowTitle("Bộ Chuyển Đổi Tài Liệu PDF & DOCX")\n        self.setWindowIcon(QIcon(str(APP_DIR / "logo.png")))'
    )

# 3. Strip all individual setStyleSheet strings (careful replacements)
# FileDropZone
content = content.replace('self.iconLabel.setStyleSheet("font-size: 48px; background: transparent;")', 'self.iconLabel.setObjectName("dropIcon")')
content = content.replace('self.textLabel.setStyleSheet("font-size: 14px; font-weight: 500; color: #9ca3af; background: transparent;")', 'self.textLabel.setObjectName("dropText")')
content = content.replace('self.pathLabel.setStyleSheet("font-size: 12px; color: #10b981; font-weight: bold; background: transparent;")', 'self.pathLabel.setObjectName("dropPath")')

# Remove dynamic text style changes in FileDropZone
content = content.replace('self.textLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981; background: transparent;")', '')
# Remove the second occurrence when leaving drag
content = content.replace('self.textLabel.setStyleSheet("font-size: 14px; font-weight: 500; color: #9ca3af; background: transparent;")', '')

# javaStatusLabel static styling
content = content.replace('self.javaStatusLabel.setStyleSheet("font-size: 12px; padding: 6px 12px; border-radius: 12px;")', 'self.javaStatusLabel.setObjectName("javaStatus")')

# banners
content = re.sub(r'self\.javaWarningBanner\.setStyleSheet\("""[\s\S]*?    """\)', '', content)
content = re.sub(r'self\.tessWarningBanner\.setStyleSheet\("""[\s\S]*?    """\)', '', content)

content = content.replace('self.bannerLabel.setStyleSheet("color: #f59e0b; font-weight: 500;")', 'self.bannerLabel.setObjectName("warnText")')
content = content.replace('self.tessBannerLabel.setStyleSheet("color: #3b82f6; font-weight: 500;")', 'self.tessBannerLabel.setObjectName("infoText")')

# buttons inside banners
content = re.sub(r'self\.btnAutoInstallJava\.setStyleSheet\("""[\s\S]*?    """\)', 'self.btnAutoInstallJava.setObjectName("installBtn")', content)
content = re.sub(r'self\.btnManualDownloadJava\.setStyleSheet\("""[\s\S]*?    """\)', 'self.btnManualDownloadJava.setObjectName("manualBtn")', content)
content = re.sub(r'self\.btnAutoInstallTess\.setStyleSheet\("""[\s\S]*?    """\)', 'self.btnAutoInstallTess.setObjectName("installTessBtn")', content)

# config widgets
content = re.sub(r'self\.ocrCombo\.setStyleSheet\("""[\s\S]*?    """\)', '', content)
content = content.replace('self.geminiKeyEdit.setStyleSheet("background-color: #0d0d0f; border: 1px solid #33333b; border-radius: 6px; padding: 6px;")', '')
content = content.replace('self.outPathEdit.setStyleSheet("background-color: #0d0d0f; border: 1px solid #33333b; border-radius: 6px; padding: 6px;")', '')

# progress & cancel & status bar
content = content.replace('self.progressLabel.setStyleSheet("color: #9ca3af; font-size: 11px; padding: 0 4px;")', 'self.progressLabel.setObjectName("progressLabel")')
content = re.sub(r'self\.btnCancel\.setStyleSheet\("""[\s\S]*?    """\)', '', content)
content = re.sub(r'status_bar\.setStyleSheet\("""[\s\S]*?    """\)', '', content)

# dynamic styles in check_java_status (replace them with property updates)
content = content.replace(
    'self.javaStatusLabel.setStyleSheet("background-color: #1c3d2e; color: #10b981; border: 1px solid #10b981; font-size: 12px; padding: 6px 12px; border-radius: 12px;")', 
    'self.javaStatusLabel.setProperty("status", "ok"); self.javaStatusLabel.style().unpolish(self.javaStatusLabel); self.javaStatusLabel.style().polish(self.javaStatusLabel)'
)
content = content.replace(
    'self.javaStatusLabel.setStyleSheet("background-color: #452b15; color: #f59e0b; border: 1px solid #f59e0b; font-size: 12px; padding: 6px 12px; border-radius: 12px;")', 
    'self.javaStatusLabel.setProperty("status", "warn"); self.javaStatusLabel.style().unpolish(self.javaStatusLabel); self.javaStatusLabel.style().polish(self.javaStatusLabel)'
)


# 4. Replace setup_styles
new_styles = '''    def setup_styles(self):
        qss = """
        QMainWindow { background-color: #f8fafc; }
        QWidget { color: #1e293b; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; font-size: 13px; }
        
        QFrame#dropZone { background-color: #ffffff; border: 2px dashed #94a3b8; border-radius: 12px; margin: 2px; }
        QFrame#dropZone:hover { border: 2px dashed #2d3a8c; background-color: #eff6ff; }
        QFrame#dropZone[dragged="true"] { border: 2px solid #e52b2d; background-color: #fef2f2; }
        
        QLabel#dropIcon { font-size: 48px; color: #2d3a8c; background: transparent; }
        QLabel#dropText { font-size: 14px; font-weight: 500; color: #475569; background: transparent; }
        QFrame#dropZone[dragged="true"] QLabel#dropText { color: #e52b2d; font-size: 16px; font-weight: bold; }
        QLabel#dropPath { font-size: 12px; color: #2d3a8c; font-weight: bold; background: transparent; }
        
        QFrame#configFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }
        QLabel#titleLabel { font-size: 22px; font-weight: bold; color: #e52b2d; }
        QLabel#subtitleLabel { font-size: 13px; color: #475569; }
        
        QLabel#javaStatus { font-size: 12px; padding: 6px 12px; border-radius: 12px; border: 1px solid transparent; }
        QLabel#javaStatus[status="ok"] { background-color: #eff6ff; color: #2d3a8c; border-color: #2d3a8c; }
        QLabel#javaStatus[status="warn"] { background-color: #fef2f2; color: #e52b2d; border-color: #e52b2d; }
        
        QFrame#warningBanner { background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; }
        QLabel#warnText { color: #e52b2d; font-weight: bold; }
        
        QFrame[objectName="tessWarningBanner"] { background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; }
        QLabel#infoText { color: #2d3a8c; font-weight: bold; }
        
        QPushButton#installBtn, QPushButton#installTessBtn {
            background-color: #ffffff; color: #2d3a8c; font-weight: 600; border: 1px solid #2d3a8c; border-radius: 6px; padding: 5px 10px;
        }
        QPushButton#installBtn:hover, QPushButton#installTessBtn:hover { background-color: #eff6ff; }
        
        QPushButton#manualBtn { background-color: transparent; color: #475569; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 10px; }
        QPushButton#manualBtn:hover { background-color: #f1f5f9; }
        
        QPushButton#convertBtn { background: #2d3a8c; color: #ffffff; font-weight: bold; border: none; border-radius: 8px; padding: 12px; font-size: 14px; }
        QPushButton#convertBtn:hover { background: #1e2865; }
        QPushButton#convertBtn:disabled { background-color: #cbd5e1; color: #94a3b8; }
        
        QPushButton#cancelBtn { background-color: #ffffff; color: #e52b2d; font-weight: bold; border: 2px solid #e52b2d; border-radius: 8px; padding: 8px 16px; font-size: 13px; }
        QPushButton#cancelBtn:hover { background-color: #fef2f2; }
        QPushButton#cancelBtn:disabled { border-color: #cbd5e1; color: #94a3b8; }
        
        QPushButton#browseBtn, QPushButton#actionBtnSecondary { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 16px; color: #334155; font-weight: 500; }
        QPushButton#browseBtn:hover, QPushButton#actionBtnSecondary:hover { background-color: #f1f5f9; border-color: #94a3b8; }
        
        QLineEdit, QComboBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; color: #1e293b; }
        QLineEdit:focus, QComboBox:focus { border: 1px solid #2d3a8c; }
        
        QComboBox QAbstractItemView { background-color: #ffffff; color: #1e293b; selection-background-color: #eff6ff; selection-color: #2d3a8c; border: 1px solid #cbd5e1; }
        
        QPlainTextEdit#logConsole { background-color: #1e293b; color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; padding: 8px; }
        
        QStatusBar { background-color: #ffffff; color: #475569; border-top: 1px solid #e2e8f0; font-size: 11px; padding: 2px 8px; }
        
        QProgressBar { border: none; background-color: #e2e8f0; height: 8px; border-radius: 4px; }
        QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffe700, stop:1 #e52b2d); border-radius: 4px; }
        QLabel#progressLabel { color: #64748b; font-size: 11px; padding: 0 4px; }
        
        QCheckBox { color: #334155; }
        QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #cbd5e1; border-radius: 4px; background-color: #ffffff; }
        QCheckBox::indicator:checked { background-color: #2d3a8c; border-color: #2d3a8c; }
        
        QMessageBox { background-color: #ffffff; }
        QMessageBox QLabel { color: #1e293b; }
        QMessageBox QPushButton { background-color: #2d3a8c; color: #ffffff; border: none; border-radius: 4px; padding: 6px 16px; min-width: 60px; }
        QMessageBox QPushButton:hover { background-color: #1e2865; }
        """
        self.setStyleSheet(qss)'''

content = re.sub(r'    def setup_styles\(self\):[\s\S]*?self\.setStyleSheet\(qss\)', new_styles, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Theme updated successfully!")
