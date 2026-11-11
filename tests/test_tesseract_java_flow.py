"""Test luồng Tesseract OCR, dò Tesseract/Java và đường lỗi của chế độ Standard.

PDF được dựng thật bằng PyMuPDF; Tesseract (pytesseract) và Java (subprocess) bị giả
lập ở biên của chúng nên chạy được trên CI mà không cần cài binary nào.
"""
import subprocess
from pathlib import Path

import fitz
import pytest

import openloader as ol
from openloader import ConversionWorker


class LogSpy:
    def __init__(self):
        self.entries = []

    def emit(self, message, level="info"):
        self.entries.append((message, level))

    def at(self, level):
        return [m for m, lv in self.entries if lv == level]

    @property
    def text(self):
        return "\n".join(m for m, _ in self.entries)


class Host:
    """Stand-in cho ConversionWorker: đủ thuộc tính để chạy convert_pdf_with_ocr/standard."""

    def __init__(self, **attrs):
        self.log = LogSpy()
        self.formats = ["markdown"]
        self.ocr_mode = "tesseract"
        self.page_range = ""
        self.dpi = 72
        self.redact_pii_enabled = False
        self._cancelled = False
        for key, value in attrs.items():
            setattr(self, key, value)
        for name in ("convert_pdf_with_ocr", "convert_pdf_standard", "_redact"):
            setattr(self, name, getattr(ConversionWorker, name).__get__(self, Host))


def make_pdf(path, pages=2):
    doc = fitz.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"Trang {i + 1}")
    doc.save(str(path))
    doc.close()
    return path


class FakeTesseract:
    """pytesseract giả: `answers` là hàm (lang, lần_gọi) -> văn bản, hoặc ném lỗi."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def image_to_string(self, img, lang):
        self.calls.append(lang)
        return self.answers(lang, len(self.calls))


@pytest.fixture
def tess_env(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (True, str(tmp_path / "tessdata")))
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    return out_dir


@pytest.fixture
def pdf(tmp_path):
    return make_pdf(tmp_path / "hoso.pdf")


# --- Luồng Tesseract ---

def test_tesseract_flow_writes_markdown_with_page_text(pdf, tess_env, monkeypatch):
    fake = FakeTesseract(lambda lang, n: "Nội dung đọc được bằng tiếng Việt")
    monkeypatch.setattr(ol, "pytesseract", fake)
    host = Host()

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is True

    md = (tess_env / "hoso.md").read_text(encoding="utf-8")
    assert md.count("Nội dung đọc được bằng tiếng Việt") == 2
    assert "## Trang 1" in md and "## Trang 2" in md
    assert set(fake.calls) == {"vie"}
    assert not (tess_env / "hoso_ocr_images").exists()  # ảnh tạm đã được dọn


def test_tesseract_flow_respects_page_range(pdf, tess_env, monkeypatch):
    fake = FakeTesseract(lambda lang, n: "chỉ trang được chọn")
    monkeypatch.setattr(ol, "pytesseract", fake)
    host = Host(page_range="2")

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is True

    md = (tess_env / "hoso.md").read_text(encoding="utf-8")
    assert "## Trang 2" in md and "## Trang 1" not in md
    assert len(fake.calls) == 1


def test_tesseract_falls_back_to_english_when_vietnamese_model_fails(pdf, tess_env, monkeypatch):
    """Mất vie.traineddata giữa chừng: phải thử lại bằng eng thay vì mất cả trang."""
    def answers(lang, n):
        if lang == "vie":
            raise RuntimeError("Failed loading language 'vie'")
        return "english fallback text"
    monkeypatch.setattr(ol, "pytesseract", FakeTesseract(answers))
    host = Host()

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is True
    assert "english fallback text" in (tess_env / "hoso.md").read_text(encoding="utf-8")
    assert any("Thử lại bằng tiếng Anh" in m for m in host.log.at("warning"))


def test_tesseract_total_failure_returns_false_and_writes_nothing(pdf, tess_env, monkeypatch):
    """Tesseract chết hẳn (binary lỗi/hỏng): báo thất bại rõ, không xuất file toàn thông báo lỗi."""
    def answers(lang, n):
        raise RuntimeError("tesseract is not installed or it's not in your PATH")
    monkeypatch.setattr(ol, "pytesseract", FakeTesseract(answers))
    host = Host()

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is False
    assert any("Tất cả 2 trang đều lỗi OCR" in m for m in host.log.at("error"))
    assert not (tess_env / "hoso.md").exists()


def test_tesseract_failed_page_is_repaired_by_retry_pass(tmp_path, tess_env, monkeypatch):
    """Trang lỗi ở lượt đầu (cả vie lẫn eng) được lượt 'quét vá' đọc lại thành công."""
    one_page = make_pdf(tmp_path / "mot_trang.pdf", pages=1)

    def answers(lang, n):
        if n <= 2:  # lượt đầu: vie rồi eng đều lỗi
            raise RuntimeError("transient failure")
        return "đọc được ở lượt vá"
    fake = FakeTesseract(answers)
    monkeypatch.setattr(ol, "pytesseract", fake)
    host = Host()

    assert host.convert_pdf_with_ocr(one_page, str(tess_env)) is True
    assert fake.calls == ["vie", "eng", "vie"]
    assert any("Quét vá thành công" in m for m in host.log.at("success"))
    md = (tess_env / "mot_trang.md").read_text(encoding="utf-8")
    assert "đọc được ở lượt vá" in md and "Không thể nhận diện" not in md


def test_tesseract_continues_in_english_when_vietnamese_pack_download_fails(pdf, tess_env, monkeypatch, tmp_path):
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (False, str(tmp_path / "tessdata")))

    def offline(url, dest):
        raise OSError("Network is unreachable")
    monkeypatch.setattr(ol.urllib.request, "urlretrieve", offline)
    monkeypatch.setattr(ol, "pytesseract", FakeTesseract(lambda lang, n: "vẫn đọc được"))
    host = Host()

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is True
    assert any("Tesseract sẽ chạy bằng tiếng Anh" in m for m in host.log.at("warning"))


def test_tesseract_output_is_redacted_when_enabled(pdf, tess_env, monkeypatch):
    monkeypatch.setattr(ol, "pytesseract", FakeTesseract(lambda lang, n: "Ông A, CCCD số 079123456789"))
    host = Host(redact_pii_enabled=True)

    assert host.convert_pdf_with_ocr(pdf, str(tess_env)) is True
    md = (tess_env / "hoso.md").read_text(encoding="utf-8")
    assert "079123456789" not in md and "[ĐÃ ẨN: CCCD]" in md


def test_tesseract_unreadable_pdf_fails_without_crashing(tess_env, monkeypatch, tmp_path):
    monkeypatch.setattr(ol, "pytesseract", FakeTesseract(lambda lang, n: "x"))
    bad = tmp_path / "hong.pdf"
    bad.write_bytes(b"not a pdf at all")
    host = Host()

    assert host.convert_pdf_with_ocr(bad, str(tess_env)) is False
    assert any("Thất bại OCR PDF" in m for m in host.log.at("error"))


# --- Dò Tesseract ---

def test_find_tesseract_none_without_pytesseract(monkeypatch):
    monkeypatch.setattr(ol, "pytesseract", None)
    assert ol.find_tesseract_path() is None


def test_find_tesseract_uses_path_when_available(monkeypatch):
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol.shutil, "which", lambda name: "/usr/bin/tesseract")
    assert ol.find_tesseract_path() == "tesseract"


def test_find_tesseract_scans_standard_install_dir_and_configures_pytesseract(monkeypatch):
    exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    fake = type("PT", (), {"pytesseract": type("Inner", (), {"tesseract_cmd": "tesseract"})()})()
    monkeypatch.setattr(ol, "pytesseract", fake)
    monkeypatch.setattr(ol.shutil, "which", lambda name: None)
    monkeypatch.setattr(ol.os.path, "exists", lambda p: p == exe)

    assert ol.find_tesseract_path() == exe
    assert fake.pytesseract.tesseract_cmd == exe


def test_find_tesseract_none_when_nowhere_to_be_found(monkeypatch):
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol.shutil, "which", lambda name: None)
    monkeypatch.setattr(ol.os.path, "exists", lambda p: False)
    assert ol.find_tesseract_path() is None


# --- Dò Java ---

def test_java_available_when_version_command_succeeds(monkeypatch):
    monkeypatch.setattr(ol.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, b"", b""))
    assert ol.is_java_available() is True


def test_java_missing_everywhere_returns_false(monkeypatch):
    def not_found(*a, **k):
        raise FileNotFoundError("java")
    monkeypatch.setattr(ol.subprocess, "run", not_found)
    monkeypatch.setattr(ol, "check_adoptium_java", lambda: False)
    assert ol.is_java_available() is False


def test_java_found_via_adoptium_when_not_on_path(monkeypatch):
    """Vừa cài Java xong nhưng PATH của tiến trình chưa cập nhật: dò thư mục Adoptium."""
    def not_found(*a, **k):
        raise FileNotFoundError("java")
    monkeypatch.setattr(ol.subprocess, "run", not_found)
    monkeypatch.setattr(ol, "check_adoptium_java", lambda: True)
    assert ol.is_java_available() is True


# --- Đường lỗi của chế độ Standard khi Java chạy lỗi ---

class _FailingConverter:
    def __init__(self, error):
        self.error = error

    def convert(self, **kwargs):
        raise self.error


def _standard_host(monkeypatch, error):
    monkeypatch.setattr(ol, "opendataloader_pdf", _FailingConverter(error))
    monkeypatch.setattr(ol, "is_java_available", lambda: True)
    return Host()


def test_standard_reports_java_process_failure_with_its_output(pdf, tmp_path, monkeypatch):
    error = subprocess.CalledProcessError(1, "java", output="boom stdout", stderr="Exception in thread main")
    host = _standard_host(monkeypatch, error)

    assert host.convert_pdf_standard(pdf, str(tmp_path)) is False
    assert any("Mã lỗi: 1" in m for m in host.log.at("error"))
    assert "Exception in thread main" in host.log.text
    assert "boom stdout" in host.log.text


def test_standard_reports_unexpected_error_without_crashing(pdf, tmp_path, monkeypatch):
    host = _standard_host(monkeypatch, RuntimeError("jar bị hỏng"))

    assert host.convert_pdf_standard(pdf, str(tmp_path)) is False
    assert any("jar bị hỏng" in m for m in host.log.at("error"))
