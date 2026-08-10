import re

with open("openloader.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add missing methods
extra_methods = '''
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
'''
if "def open_settings(self):" not in content:
    content = content.replace("    def handle_ocr_mode_change(self, index):", extra_methods + "\n    def handle_ocr_mode_change(self, index):")

# 2. Add btnSettings to UI
if "self.btnSettings = QPushButton" not in content:
    content = content.replace(
        "self.ocrCombo.currentIndexChanged.connect(self.handle_ocr_mode_change)",
        "self.ocrCombo.currentIndexChanged.connect(self.handle_ocr_mode_change)\n        self.btnSettings = QPushButton('⚙️ Cài đặt')\n        self.btnSettings.clicked.connect(self.open_settings)\n        config_layout.addWidget(self.btnSettings, 1, 2)"
    )

with open("openloader.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Patch applied.")
