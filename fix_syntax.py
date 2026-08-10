import re

with open('openloader.py', 'r', encoding='utf-8') as f:
    content = f.read()

broken_block = """        try:
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
                    self.progress.emit(f"Không thể tải tự động gói tiếng Việt: {str(down_err)}", "error")"""

fixed_block = """        try:
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
            self.finished.emit(False)"""

if broken_block in content:
    content = content.replace(broken_block, fixed_block)
    with open('openloader.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed SyntaxError")
else:
    print("Could not find broken block. Please check manually.")
