"""Tests cho các đường lỗi khi thiếu phụ thuộc ngoài (Java, Tesseract, Docling, PyMuPDF).

Kịch bản 2 trong TESTING_SCENARIOS.md: phần mềm không được crash khi bên thứ ba
vắng mặt — phải trả về False và ghi log lỗi đủ rõ để người dùng biết cài gì.
Các phụ thuộc này là binary/model nặng, nên chúng được giả lập ở biên import.
"""
import sys
import types

import pytest

import openloader as ol
from openloader import ConversionWorker


class LogSpy:
    def __init__(self):
        self.entries = []

    def emit(self, message, level="info"):
        self.entries.append((message, level))

    @property
    def errors(self):
        return [m for m, level in self.entries if level == "error"]

    @property
    def all_text(self):
        return "\n".join(m for m, _ in self.entries)


class _WorkerHost:
    """Stand-in cho ConversionWorker để gọi được method mà không cần Qt."""

    def __init__(self, **attrs):
        self.log = LogSpy()
        self.formats = ["markdown"]
        self.ocr_mode = "none"
        self.page_range = ""
        self.dpi = 300
        self.redact_pii_enabled = False
        for key, value in attrs.items():
            setattr(self, key, value)


def _host(methods, **attrs):
    host = _WorkerHost(**attrs)
    for name in methods:
        setattr(host, name, getattr(ConversionWorker, name).__get__(host, _WorkerHost))
    return host


@pytest.fixture
def pdf_path(tmp_path):
    path = tmp_path / "hoso.pdf"
    path.write_bytes(b"%PDF-1.4 fake")
    return path


# --- Luồng Standard (opendataloader-pdf + Java) ---

def test_standard_reports_missing_library(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "opendataloader_pdf", None)
    host = _host(["convert_pdf_standard"])

    assert host.convert_pdf_standard(pdf_path, str(tmp_path)) is False
    assert any("opendataloader-pdf" in m for m in host.log.errors)


def test_standard_reports_missing_java(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "opendataloader_pdf", object())
    monkeypatch.setattr(ol, "is_java_available", lambda: False)
    host = _host(["convert_pdf_standard"])

    assert host.convert_pdf_standard(pdf_path, str(tmp_path)) is False
    assert any("Java" in m for m in host.log.errors)


# --- Luồng OCR (PyMuPDF + Tesseract) ---

def test_ocr_reports_missing_pymupdf(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "fitz", None)
    host = _host(["convert_pdf_with_ocr"], ocr_mode="tesseract")

    assert host.convert_pdf_with_ocr(pdf_path, str(tmp_path)) is False
    assert any("PyMuPDF" in m for m in host.log.errors)


def test_ocr_reports_missing_pytesseract(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "fitz", object())
    monkeypatch.setattr(ol, "pytesseract", None)
    host = _host(["convert_pdf_with_ocr"], ocr_mode="tesseract")

    assert host.convert_pdf_with_ocr(pdf_path, str(tmp_path)) is False
    assert any("pytesseract" in m for m in host.log.errors)


def test_ocr_reports_missing_tesseract_binary(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "fitz", object())
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: None)
    host = _host(["convert_pdf_with_ocr"], ocr_mode="tesseract")

    assert host.convert_pdf_with_ocr(pdf_path, str(tmp_path)) is False
    assert any("Tesseract" in m for m in host.log.errors)


def test_ocr_delegates_to_docling_in_docling_mode(pdf_path, tmp_path):
    host = _host(["convert_pdf_with_ocr"], ocr_mode="docling")
    seen = {}

    def fake_docling(file_path, output_dir):
        seen["file"] = file_path
        return True

    host.convert_pdf_with_docling = fake_docling

    assert host.convert_pdf_with_ocr(pdf_path, str(tmp_path)) is True
    assert seen["file"] == pdf_path


# --- Dò dữ liệu ngôn ngữ tiếng Việt ---

def test_vietnamese_data_found_in_system_tessdata(tmp_path, monkeypatch):
    sys_tessdata = tmp_path / "Tesseract-OCR" / "tessdata"
    sys_tessdata.mkdir(parents=True)
    (sys_tessdata / "vie.traineddata").write_bytes(b"fake")
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: str(tmp_path / "Tesseract-OCR" / "tesseract.exe"))

    has_viet, tessdata_dir = ol.check_tesseract_vietnamese()
    assert has_viet is True
    assert tessdata_dir == str(sys_tessdata)


def test_vietnamese_data_falls_back_to_local_dir(tmp_path, monkeypatch):
    local = tmp_path / "tessdata"
    local.mkdir()
    (local / "vie.traineddata").write_bytes(b"fake")
    monkeypatch.setattr(ol, "APP_DIR", tmp_path)
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")  # chỉ có trên PATH

    has_viet, tessdata_dir = ol.check_tesseract_vietnamese()
    assert has_viet is True
    assert tessdata_dir == str(local)


def test_missing_vietnamese_data_returns_download_target(tmp_path, monkeypatch):
    """Trả về False kèm thư mục đích để phía gọi biết chỗ tải vie.traineddata về."""
    monkeypatch.setattr(ol, "APP_DIR", tmp_path)
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")

    has_viet, tessdata_dir = ol.check_tesseract_vietnamese()
    assert has_viet is False
    assert tessdata_dir == str(tmp_path / "tessdata")


# --- Luồng Docling ---

def test_docling_reports_missing_package_with_install_hint(pdf_path, tmp_path, monkeypatch):
    # Buộc ImportError kể cả khi docling đã cài trên máy dev (CI thì chưa cài)
    monkeypatch.setitem(sys.modules, "docling", None)
    monkeypatch.setitem(sys.modules, "docling.document_converter", None)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(tmp_path)) is False
    assert any("Docling" in m for m in host.log.errors)
    # Người dùng cuối cần biết bấm vào đâu để cài, không chỉ biết là thiếu
    assert "Cài đặt Docling" in host.log.all_text


def _install_fake_docling(monkeypatch, markdown=""):
    """Cho qua bước import Docling mà không cần cài thật (nó kéo theo torch ~2GB).

    Nhờ vậy các đường lỗi phía sau vẫn được kiểm tra trên CI, thay vì bị skip.
    """

    class _Options:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.table_structure_options = types.SimpleNamespace(mode=None)

    class _FakeConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, source):
            document = types.SimpleNamespace(export_to_markdown=lambda **kw: markdown)
            return types.SimpleNamespace(document=document)

    converter_mod = types.ModuleType("docling.document_converter")
    converter_mod.DocumentConverter = _FakeConverter
    converter_mod.PdfFormatOption = _Options

    base_models = types.ModuleType("docling.datamodel.base_models")
    base_models.InputFormat = types.SimpleNamespace(PDF="pdf")

    pipeline = types.ModuleType("docling.datamodel.pipeline_options")
    pipeline.PdfPipelineOptions = _Options
    pipeline.TesseractCliOcrOptions = _Options
    pipeline.TableFormerMode = types.SimpleNamespace(ACCURATE="accurate")
    pipeline.OcrMode = types.SimpleNamespace(FULL_PAGE="full_page")

    for name, module in [
        ("docling", types.ModuleType("docling")),
        ("docling.datamodel", types.ModuleType("docling.datamodel")),
        ("docling.document_converter", converter_mod),
        ("docling.datamodel.base_models", base_models),
        ("docling.datamodel.pipeline_options", pipeline),
    ]:
        monkeypatch.setitem(sys.modules, name, module)


def _ready_docling_env(monkeypatch, tmp_path, markdown):
    """Giả lập môi trường Docling đã sẵn sàng để chạy tới bước xuất kết quả."""
    _install_fake_docling(monkeypatch, markdown=markdown)
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (True, str(tmp_path / "tessdata")))
    monkeypatch.setattr(ol, "APP_DIR", tmp_path)


def test_docling_reports_missing_tesseract_binary(pdf_path, tmp_path, monkeypatch):
    _install_fake_docling(monkeypatch)
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: None)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(tmp_path)) is False
    assert any("Tesseract" in m for m in host.log.errors)


def test_docling_reports_missing_pytesseract(pdf_path, tmp_path, monkeypatch):
    _install_fake_docling(monkeypatch)
    monkeypatch.setattr(ol, "pytesseract", None)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(tmp_path)) is False
    assert any("pytesseract" in m for m in host.log.errors)


def test_docling_reports_empty_result_and_suggests_other_modes(pdf_path, tmp_path, monkeypatch):
    """Bug cũ ở V2.1: Docling trả kết quả rỗng mà vẫn xuất file trống."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _ready_docling_env(monkeypatch, tmp_path, markdown="")
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("rỗng" in m for m in host.log.errors)
    assert "OCR" in host.log.all_text  # gợi ý người dùng đổi sang chế độ khác
    assert list(out_dir.iterdir()) == []  # không để lại file rỗng


def test_docling_writes_markdown_output(pdf_path, tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _ready_docling_env(
        monkeypatch, tmp_path,
        markdown="# Biên bản\n\nNội dung tài liệu đủ dài để vượt ngưỡng kiểm tra rỗng.",
    )
    host = _host(["convert_pdf_with_docling", "_redact"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True
    assert (out_dir / "hoso.md").read_text(encoding="utf-8").startswith("# Biên bản")


def test_docling_output_is_redacted_when_enabled(pdf_path, tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _ready_docling_env(
        monkeypatch, tmp_path,
        markdown="# Biên bản\n\nÔng A, CCCD số 079123456789, điện thoại 0901234567.",
    )
    host = _host(["convert_pdf_with_docling", "_redact"], redact_pii_enabled=True)

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True
    written = (out_dir / "hoso.md").read_text(encoding="utf-8")
    assert "079123456789" not in written
    assert "[ĐÃ ẨN: CCCD]" in written
