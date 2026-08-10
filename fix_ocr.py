import re

with open('openloader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to replace the dynamic routing logic with direct OCR logic.
# The original block:
original_pattern = re.compile(
    r'text = page\.get_text\("text"\)\.strip\(\)\s*'
    r'# Dynamic routing decision.*?else:\s*'
    r'self\.log\.emit\(f"\s*Trang \{page_num \+ 1\}: Trang rỗng/ảnh quét -> Chạy nhận diện OCR\.\.\.", "warning"\)\s*'
    r'# Render page to high-quality image',
    re.DOTALL
)

replacement = """self.log.emit(f"    Trang {page_num + 1}: Chạy nhận diện OCR ({self.ocr_mode.upper()})...", "info")
                # Render page to high-quality image"""

if original_pattern.search(content):
    content = original_pattern.sub(replacement, content)
    
    # Now we need to fix the indentation for the rest of the OCR block.
    # The easiest way is to just find and replace the block manually or with string replacement.
    
    # Let's do a smart unindent by finding the lines that were under the `else:` block and removing 4 spaces.
    # But since we replaced the `if/else`, we can just use re.sub for the remaining lines of the OCR block.
    pass

# Actually, it's safer to just do a strict string replacement for the entire block.
strict_old_block = """                text = page.get_text("text").strip()
                
                # Dynamic routing decision (If page contains text -> extract. If page is image -> OCR)
                if len(text) > 100:
                    self.log.emit(f"    Trang {page_num + 1}: Phát hiện text gốc -> Trích xuất trực tiếp.", "info")
                    markdown_content.append(f"## Trang {page_num + 1}\\n\\n{text}\\n\\n")
                else:
                    self.log.emit(f"    Trang {page_num + 1}: Trang rỗng/ảnh quét -> Chạy nhận diện OCR...", "warning")
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
                                    f"\\n\\n> ⚠️ **Không thể nhận diện nội dung trang {page_num + 1}**\\n"
                                    f"> Nguyên nhân: Tesseract OCR không đọc được cả tiếng Việt lẫn tiếng Anh.\\n"
                                    f"> Gợi ý: Thử chuyển sang chế độ Gemini AI OCR để nhận diện chính xác hơn.\\n\\n"
                                )
                    
                    elif self.ocr_mode == "gemini":
                        try:
                            ocr_text = ocr_page_with_ai(str(img_path), self.ai_profile)
                            self.log.emit(f"    Trang {page_num + 1}: OCR AI thành công.", "success")
                        except Exception as g_err:
                            ocr_errors += 1
                            self.log.emit(f"    Lỗi AI API trang {page_num + 1} (sau 3 lần thử): {str(g_err)}", "error")
                            ocr_text = f"\\n\\n> ❌ **LỖI OCR trang {page_num + 1}**: {str(g_err)}\\n\\n"
                            
                    markdown_content.append(f"## Trang {page_num + 1} (OCR - {self.ocr_mode.upper()})\\n\\n{ocr_text}\\n\\n")"""

strict_new_block = """                self.log.emit(f"    Trang {page_num + 1}: Chạy nhận diện OCR ({self.ocr_mode.upper()})...", "info")
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
                                f"\\n\\n> ⚠️ **Không thể nhận diện nội dung trang {page_num + 1}**\\n"
                                f"> Nguyên nhân: Tesseract OCR không đọc được cả tiếng Việt lẫn tiếng Anh.\\n"
                                f"> Gợi ý: Thử chuyển sang chế độ Gemini AI OCR để nhận diện chính xác hơn.\\n\\n"
                            )
                
                elif self.ocr_mode == "gemini":
                    try:
                        ocr_text = ocr_page_with_ai(str(img_path), self.ai_profile)
                        self.log.emit(f"    Trang {page_num + 1}: OCR AI thành công.", "success")
                    except Exception as g_err:
                        ocr_errors += 1
                        self.log.emit(f"    Lỗi AI API trang {page_num + 1} (sau 3 lần thử): {str(g_err)}", "error")
                        ocr_text = f"\\n\\n> ❌ **LỖI OCR trang {page_num + 1}**: {str(g_err)}\\n\\n"
                        
                markdown_content.append(f"## Trang {page_num + 1} (OCR - {self.ocr_mode.upper()})\\n\\n{ocr_text}\\n\\n")"""

with open('openloader.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if strict_old_block in content:
    content = content.replace(strict_old_block, strict_new_block)
    with open('openloader.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed OCR logic")
else:
    print("Could not find the strict block")
