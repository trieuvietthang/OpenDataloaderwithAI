"""Chạy Docling trong một tiến trình Python riêng, do LexGuard (openloader.py) gọi.

Vì sao tách riêng: bản đóng gói (.exe) không chứa Docling/PyTorch (~2GB) và
không thể import thư viện từ Python bên ngoài. LexGuard thay vào đó gọi script
này bằng một Python đã `pip install docling`. Script chỉ dùng thư viện chuẩn +
docling, KHÔNG import openloader (không cần PySide6).

Giao thức với tiến trình gọi:
  - stdout: các dòng `LOG|<info|success|warning|error>|<thông điệp>`
  - ghi markdown đã làm sạch vào tệp `out_md`
  - mã thoát: 0 = OK, 1 = lỗi khác, 2 = không import được Docling, 3 = không tải được model
"""
import argparse
import os
import sys
from pathlib import Path

# torch.compile cần trình biên dịch MSVC mà đa số máy Windows không có.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_IMPORT = 2
EXIT_MODELS = 3

_IMAGE_PLACEHOLDERS = ("<!-- image -->", "![image]()", "![Image]()")


def log(level, message):
    print(f"LOG|{level}|{message}", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("out_md")
    parser.add_argument("--models-dir", required=True)
    parser.add_argument("--tessdata-dir", required=True)
    parser.add_argument("--tesseract-cmd", required=True)
    args = parser.parse_args(argv)

    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions, TableFormerMode, TesseractCliOcrOptions, OcrMode
        )
    except ImportError as e:
        log("error", f"Python '{sys.executable}' không import được Docling: {e}")
        return EXIT_IMPORT

    # Tải model về thư mục cố định thay vì để Docling tự chọn cache ẩn ở nơi khác.
    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    if not any(models_dir.iterdir()):
        log("warning", "  Chưa có mô hình cục bộ, đang tải về (chỉ xảy ra lần đầu tiên)...")
        try:
            from docling.utils.model_downloader import download_models
            download_models(output_dir=models_dir, progress=False)
            log("success", "  Tải mô hình thành công. Từ lần sau sẽ không cần tải lại.")
        except Exception as e:
            log("error", f"Lỗi: Không tải được mô hình Docling: {e}")
            return EXIT_MODELS

    pipeline_options = PdfPipelineOptions(
        do_ocr=True,
        do_table_structure=True,
        artifacts_path=str(models_dir),
    )
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    # Dùng Tesseract CLI (binding tesserocr phải tự biên dịch). Không truyền lang/path
    # tường minh thì Docling mặc định ['fra','deu','spa','eng'] và không thấy tiếng Việt.
    pipeline_options.ocr_options = TesseractCliOcrOptions(
        lang=["vie", "eng"],
        tesseract_cmd=args.tesseract_cmd,
        path=args.tessdata_dir,
        mode=OcrMode.FULL_PAGE,
        force_full_page_ocr=True,
    )

    try:
        log("info", "  Đang xử lý tài liệu với Docling...")
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        result = converter.convert(args.pdf)

        # Giữ đầu ra là 1 tệp .md độc lập: không ảnh, không placeholder.
        markdown = result.document.export_to_markdown(image_placeholder="")
        markdown = "\n".join(
            line for line in markdown.splitlines() if line.strip() not in _IMAGE_PLACEHOLDERS
        ).strip()
        Path(args.out_md).write_text(markdown, encoding="utf-8")
    except Exception as e:
        log("error", f"-> Thất bại Docling OCR: {e}")
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
