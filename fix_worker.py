import re

with open('openloader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix ConversionWorker init
old_init = '''    def __init__(self, input_paths, formats, output_dir, ocr_mode="none", ai_profile=None):
        super().__init__()
        self.input_paths = input_paths
        self.formats = formats
        self.output_dir = output_dir
        self.ocr_mode = ocr_mode
        self.ai_profile = ai_profile
        self.is_cancelled = False'''

new_init = '''    def __init__(self, input_paths, formats, output_dir, ocr_mode="none", ai_profile=None, page_range=""):
        super().__init__()
        self.input_paths = input_paths
        self.formats = formats
        self.output_dir = output_dir
        self.ocr_mode = ocr_mode
        self.ai_profile = ai_profile
        self.page_range = page_range
        self.is_cancelled = False'''

if old_init in content:
    content = content.replace(old_init, new_init)
    print("Fixed ConversionWorker init")

# 2. Restore deleted Tesseract exception code if missing
tess_missing = '''                    self.progress.emit("Bạn vẫn có thể OCR bằng tiếng Anh. Hãy tải thủ công file vie.traineddata sau.", "warning")
                    self.finished.emit(True)
            else:
                self.progress.emit(f"Cài đặt Tesseract thất bại (mã lỗi: {process.returncode}).", "error")
                if stderr:
                    self.progress.emit(f"Chi tiết: {stderr.strip()}", "error")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Lỗi khi chạy lệnh winget: {str(e)}", "error")
            self.finished.emit(False)'''

if "Bạn vẫn có thể OCR bằng tiếng Anh." not in content:
    print("Restoring missing Tesseract code")
    anchor = 'self.progress.emit(f"Không thể tải tự động gói tiếng Việt: {str(down_err)}", "error")'
    if anchor in content:
        content = content.replace(anchor, anchor + "\n" + tess_missing)

with open('openloader.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
