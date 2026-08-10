import re

with open('openloader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Rename Gemini UI strings to generic AI strings
replacements = {
    '"OCR Trí tuệ nhân tạo (Sử dụng Gemini AI API - Độ chính xác cao)"': '"OCR Trí tuệ nhân tạo (Sử dụng AI API - Độ chính xác cao)"',
    '"🔍 Đang xác thực Gemini API Key..."': '"🔍 Đang xác thực API Key..."',
    '"Gemini API Key hợp lệ - Sẵn sàng quét tài liệu."': '"API Key hợp lệ - Sẵn sàng quét tài liệu."',
    '"Google Gemini (Mặc định)"': '"AI (Mặc định)"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 2. Fix the Window Icon loading
old_window_icon = 'self.setWindowIcon(QIcon(str(APP_DIR / "logo.png")))'
new_window_icon = '''icon_path = APP_DIR / "icon.ico"
        if not icon_path.exists():
            icon_path = APP_DIR / "icon.png"
        if not icon_path.exists():
            icon_path = APP_DIR / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))'''

content = content.replace(old_window_icon, new_window_icon)

# 3. Fix the UI Header Logo loading
old_header_logo = '''logo_path = APP_DIR / "logo.png"
        if logo_path.exists():'''
new_header_logo = '''logo_path = APP_DIR / "logo.png"
        if not logo_path.exists():
            logo_path = APP_DIR / "icon.png"
        if logo_path.exists():'''

content = content.replace(old_header_logo, new_header_logo)

with open('openloader.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated UI strings and icon logic successfully.")
