import sys
import re

with open("openloader.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Dark Mode toggle in header
content = content.replace(
'''        self.javaStatusLabel.setObjectName("javaStatus")
        header_layout.addWidget(self.javaStatusLabel)
        header_layout.setAlignment(self.javaStatusLabel, Qt.AlignVCenter)
        
        main_layout.addLayout(header_layout)''',
'''        self.javaStatusLabel.setObjectName("javaStatus")
        header_layout.addWidget(self.javaStatusLabel)
        header_layout.setAlignment(self.javaStatusLabel, Qt.AlignVCenter)
        
        from PySide6.QtWidgets import QPushButton
        self.btnThemeToggle = QPushButton("🌙 Giao diện tối")
        self.btnThemeToggle.setCheckable(True)
        self.btnThemeToggle.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btnThemeToggle)
        
        main_layout.addLayout(header_layout)'''
)

# Fix duplicate setObjectName
content = content.replace(
'''        self.javaStatusLabel.setObjectName("javaStatus")
        self.javaStatusLabel.setObjectName("javaStatus")''',
'''        self.javaStatusLabel.setObjectName("javaStatus")'''
)

# 2. Preview Tab replace logConsole
content = content.replace(
'''        # Log Panel
        main_layout.addWidget(QLabel("<b>Nhật ký xử lý:</b>", self))
        self.logConsole = QPlainTextEdit(self)
        self.logConsole.setObjectName("logConsole")
        self.logConsole.setReadOnly(True)
        main_layout.addWidget(self.logConsole, stretch=2)''',
'''        # Tab Widget for Log and Preview
        from PySide6.QtWidgets import QTabWidget, QTextBrowser
        self.bottomTabs = QTabWidget()
        self.logTab = QWidget()
        self.previewTab = QWidget()
        
        log_layout = QVBoxLayout(self.logTab)
        log_layout.setContentsMargins(0,0,0,0)
        self.logConsole = QPlainTextEdit(self)
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
        
        main_layout.addWidget(self.bottomTabs, stretch=2)'''
)

# 3. Handle Preview on conversion finished
content = content.replace(
'''    @Slot(bool, int)
    def conversion_finished(self, success, count):''',
'''    @Slot(bool, int)
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
'''
)

# 4. Implement Theme logic
import re
styles_pattern = re.compile(r'    def setup_styles\(self\):.*?        self\.setStyleSheet\(qss\)', re.DOTALL)

new_styles = '''    def toggle_theme(self):
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
        QMainWindow {{ background-color: {bg_color}; }}
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
        
        QPlainTextEdit#logConsole {{ background-color: #000000; color: #00ff00; border: 1px solid {border_color}; border-radius: 8px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; padding: 8px; }}
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
            self.apply_config_ui()'''
content = styles_pattern.sub(new_styles, content)

# 5. Add dark_mode to config save logic
content = content.replace(
'''                "output_dir": self.outPathEdit.text(),
                "page_range": self.pageRangeEdit.text(),''',
'''                "output_dir": self.outPathEdit.text(),
                "page_range": self.pageRangeEdit.text(),
                "dark_mode": getattr(self, "app_config", {}).get("dark_mode", False),'''
)

# Fix setup_styles call in __init__
# In load_config, we need to call setup_styles after loading so it applies the loaded theme
content = content.replace(
'''            window_size = config.get("window_size", {})
            w = window_size.get("width", 750)
            h = window_size.get("height", 750)
            self.resize(w, h)
        except Exception:''',
'''            window_size = config.get("window_size", {})
            w = window_size.get("width", 750)
            h = window_size.get("height", 750)
            self.resize(w, h)
            self.setup_styles()
        except Exception:'''
)

with open("openloader.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Phase 3 & 4 applied.")
