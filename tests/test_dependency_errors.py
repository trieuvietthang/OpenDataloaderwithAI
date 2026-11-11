"""Tests cho các đường lỗi khi thiếu phụ thuộc ngoài (Java, Tesseract, Docling, PyMuPDF).

Kịch bản 2 trong TESTING_SCENARIOS.md: phần mềm không được crash khi bên thứ ba
vắng mặt — phải trả về False và ghi log lỗi đủ rõ để người dùng biết cài gì.
Các phụ thuộc này là binary/model nặng, nên chúng được giả lập ở biên import.
"""
import subprocess
import sys
from pathlib import Path

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


# --- Thư mục cache ghi được (docling_models, tessdata) ---

def test_writable_cache_dir_uses_app_dir_when_writable(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "APP_DIR", tmp_path)
    result = ol.get_writable_cache_dir("docling_models")
    assert result == tmp_path / "docling_models"
    assert result.exists()


def test_writable_cache_dir_falls_back_to_localappdata_when_app_dir_readonly(tmp_path, monkeypatch):
    """Cài vào Program Files + chạy quyền thường -> phải chuyển sang %LOCALAPPDATA%,
    không được để lỗi ghi file làm crash tính năng Docling/Tesseract."""
    fake_app_dir = tmp_path / "Program Files" / "LexGuard"
    fake_app_dir.mkdir(parents=True)
    monkeypatch.setattr(ol, "APP_DIR", fake_app_dir)

    fake_local_appdata = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_local_appdata))

    original_touch = Path.touch

    def blocked_touch(self, *a, **k):
        if self.name == ".test_write":
            raise PermissionError("simulated: no write access to Program Files")
        return original_touch(self, *a, **k)

    monkeypatch.setattr(Path, "touch", blocked_touch)

    result = ol.get_writable_cache_dir("docling_models")

    assert result == fake_local_appdata / "LexGuard" / "docling_models"
    assert result.exists()


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
    monkeypatch.setattr(ol, "LOCAL_TESSDATA_DIR", local)
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")  # chỉ có trên PATH

    has_viet, tessdata_dir = ol.check_tesseract_vietnamese()
    assert has_viet is True
    assert tessdata_dir == str(local)


def test_missing_vietnamese_data_returns_download_target(tmp_path, monkeypatch):
    """Trả về False kèm thư mục đích để phía gọi biết chỗ tải vie.traineddata về."""
    local = tmp_path / "tessdata"
    monkeypatch.setattr(ol, "LOCAL_TESSDATA_DIR", local)
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")

    has_viet, tessdata_dir = ol.check_tesseract_vietnamese()
    assert has_viet is False
    assert tessdata_dir == str(local)


# --- Dò Python có Docling (Docling chạy ở tiến trình ngoài, xem docling_runner.py) ---

@pytest.fixture(autouse=True)
def _reset_docling_python_cache(monkeypatch):
    monkeypatch.setattr(ol, "_docling_python_cache", None)


def _fake_run(has_docling):
    """subprocess.run giả: trả mã 0 cho các Python nằm trong tập `has_docling`."""
    def run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 0 if cmd[0] in has_docling else 1, b"", b"")
    return run


def test_python_has_docling_true_on_exit_zero(monkeypatch):
    monkeypatch.setattr(ol.subprocess, "run", _fake_run({"py_ok"}))
    assert ol._python_has_docling("py_ok") is True


def test_python_has_docling_false_when_module_missing(monkeypatch):
    monkeypatch.setattr(ol.subprocess, "run", _fake_run(set()))
    assert ol._python_has_docling("py_no") is False


@pytest.mark.parametrize("error", [
    FileNotFoundError("python.exe đã bị gỡ"),
    subprocess.TimeoutExpired("python", 30),
])
def test_python_has_docling_false_when_probe_cannot_run(monkeypatch, error):
    """Python hỏng/treo không được làm crash việc dò — coi như không có Docling."""
    def boom(*a, **k):
        raise error
    monkeypatch.setattr(ol.subprocess, "run", boom)
    assert ol._python_has_docling("whatever") is False


def test_probe_never_imports_docling_in_process(monkeypatch):
    """Bug UI treo 13s (2026-09-14): import docling thật kéo theo torch. Giờ việc dò
    chạy ở tiến trình khác nên module không bao giờ vào sys.modules của ứng dụng."""
    sys.modules.pop("docling.document_converter", None)
    monkeypatch.setattr(ol.subprocess, "run", _fake_run({"py_ok"}))
    ol._python_has_docling("py_ok")
    assert "docling.document_converter" not in sys.modules


def _fake_python_files(tmp_path, *names):
    paths = []
    for name in names:
        exe = tmp_path / name / "python.exe"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"")
        paths.append(str(exe))
    return paths


def test_find_docling_python_returns_first_python_that_has_it(tmp_path, monkeypatch):
    a, b, c = _fake_python_files(tmp_path, "a", "b", "c")
    monkeypatch.setattr(ol, "_python_candidates", lambda: [a, b, c])
    monkeypatch.setattr(ol.subprocess, "run", _fake_run({b, c}))

    exe, checked = ol.find_docling_python()

    assert exe == b
    assert checked == [a, b]  # dừng ngay khi tìm thấy, không dò thừa c


def test_find_docling_python_reports_what_it_checked_when_none_has_it(tmp_path, monkeypatch):
    """Ca của người dùng: đã `pip install docling` nhưng vào nhầm Python khác — phải
    biết app đã dò những Python nào để chỉ đúng chỗ cần cài."""
    a, b = _fake_python_files(tmp_path, "a", "b")
    monkeypatch.setattr(ol, "_python_candidates", lambda: [a, b])
    monkeypatch.setattr(ol.subprocess, "run", _fake_run(set()))

    assert ol.find_docling_python() == (None, [a, b])


def test_find_docling_python_caches_positive_result(tmp_path, monkeypatch):
    (a,) = _fake_python_files(tmp_path, "a")
    monkeypatch.setattr(ol, "_python_candidates", lambda: [a])
    monkeypatch.setattr(ol.subprocess, "run", _fake_run({a}))
    assert ol.find_docling_python()[0] == a

    def must_not_probe(*args, **kwargs):
        raise AssertionError("không được dò lại khi đã có kết quả cache")
    monkeypatch.setattr(ol.subprocess, "run", must_not_probe)
    assert ol.find_docling_python()[0] == a


def test_python_candidates_env_override_first_and_deduped(tmp_path, monkeypatch):
    (custom,) = _fake_python_files(tmp_path, "custom")
    monkeypatch.setenv(ol.DOCLING_PYTHON_ENV_VAR, custom)
    monkeypatch.setattr(ol, "IS_FROZEN", False)
    monkeypatch.setattr(ol.shutil, "which", lambda name: custom if name == "python" else None)

    found = ol._python_candidates()

    assert found[0] == custom
    assert found.count(custom) == 1


def test_python_candidates_skip_frozen_exe_and_windows_store_stub(tmp_path, monkeypatch):
    """Chạy lại chính LexGuard.exe như thể là Python sẽ mở thêm cửa sổ ứng dụng; chạy
    stub WindowsApps\\python.exe sẽ bật cửa hàng Microsoft Store."""
    (frozen_exe,) = _fake_python_files(tmp_path, "LexGuard")
    stub = tmp_path / "WindowsApps" / "python.exe"
    stub.parent.mkdir()
    stub.write_bytes(b"")
    monkeypatch.delenv(ol.DOCLING_PYTHON_ENV_VAR, raising=False)
    monkeypatch.setattr(ol, "IS_FROZEN", True)
    monkeypatch.setattr(ol.sys, "executable", frozen_exe)
    monkeypatch.setattr(ol.shutil, "which", lambda name: {"python": str(stub), "py": None}.get(name))
    monkeypatch.setenv(ol.DOCLING_PYTHON_ENV_VAR, frozen_exe)

    found = ol._python_candidates()

    assert frozen_exe not in found
    assert str(stub) not in found


def test_parse_py_launcher_listing_extracts_every_interpreter_path():
    listing = (
        " -V:3.13 *        C:\\Users\\Văn Thắng\\AppData\\Local\\Programs\\Python\\Python313\\python.exe\r\n"
        " -V:3.11          C:\\Python311\\python.exe\r\n"
        "No installed Pythons found!\r\n"
    )
    assert ol._parse_py_launcher_listing(listing) == [
        "C:\\Users\\Văn Thắng\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
        "C:\\Python311\\python.exe",
    ]


def test_python_candidates_use_py_launcher_and_drop_nonexistent_paths(tmp_path, monkeypatch):
    (py313,) = _fake_python_files(tmp_path, "Python313")
    monkeypatch.delenv(ol.DOCLING_PYTHON_ENV_VAR, raising=False)
    monkeypatch.setattr(ol, "IS_FROZEN", True)
    monkeypatch.setattr(ol, "APP_DIR", tmp_path / "no_app_dir")
    monkeypatch.setattr(ol.shutil, "which", lambda name: "py" if name == "py" else None)
    monkeypatch.setattr(ol, "_parse_py_launcher_listing", lambda text: [py313, r"C:\Gone\python.exe"])
    monkeypatch.setattr(
        ol.subprocess, "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "listing", ""),
    )

    assert ol._python_candidates() == [py313]


def test_docling_missing_hint_when_python_exists_but_lacks_docling():
    hint = ol.docling_missing_hint([r"C:\Python313\python.exe"])
    assert r'"C:\Python313\python.exe" -m pip install docling' in hint
    assert ol.DOCLING_PYTHON_ENV_VAR in hint


def test_docling_missing_hint_when_no_python_at_all():
    hint = ol.docling_missing_hint([])
    assert "python.org" in hint
    assert "pip install docling" in hint


def test_docling_subprocess_env_strips_pyinstaller_and_forces_utf8(monkeypatch):
    monkeypatch.setenv("PYTHONHOME", "C:/bundle")
    monkeypatch.setenv("PYTHONPATH", "C:/bundle/lib")
    monkeypatch.setenv("_MEIPASS2", "C:/tmp/_MEI123")
    monkeypatch.setenv("_PYI_APPLICATION_HOME_DIR", "C:/tmp")

    env = ol._docling_subprocess_env()

    for key in ("PYTHONHOME", "PYTHONPATH", "_MEIPASS2", "_PYI_APPLICATION_HOME_DIR"):
        assert key not in env
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["TORCHDYNAMO_DISABLE"] == "1"


# --- Luồng Docling (tiến trình runner được giả lập ở biên subprocess.Popen) ---

class _FakePopen:
    """Popen giả: phát lại các dòng stdout dựng sẵn và (tuỳ chọn) ghi file kết quả như runner thật."""
    calls = []

    def __init__(self, cmd, **kwargs):
        type(self).calls.append((cmd, kwargs))
        self.stdout = iter(type(self).lines)
        self._exit = type(self).exit_code
        if type(self).markdown is not None:
            Path(cmd[3]).write_text(type(self).markdown, encoding="utf-8")

    def wait(self):
        return self._exit


def _fake_runner(monkeypatch, lines=(), exit_code=0, markdown=None):
    cls = type("FakePopen", (_FakePopen,), {"calls": [], "lines": list(lines),
                                             "exit_code": exit_code, "markdown": markdown})
    monkeypatch.setattr(ol.subprocess, "Popen", cls)
    return cls


def _ready_docling_env(monkeypatch, tmp_path):
    """Có Python Docling, pytesseract, Tesseract + gói tiếng Việt — chỉ còn runner là giả."""
    monkeypatch.setattr(ol, "find_docling_python", lambda: ("C:/py/python.exe", ["C:/py/python.exe"]))
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (True, str(tmp_path / "tessdata")))
    monkeypatch.setattr(ol, "DOCLING_MODELS_DIR", tmp_path / "docling_models")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    return out_dir


def test_docling_reports_missing_python_with_actionable_hint(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "IS_FROZEN", True)
    monkeypatch.setattr(ol, "find_docling_python", lambda: (None, [r"C:\Python313\python.exe"]))
    popen = _fake_runner(monkeypatch)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(tmp_path)) is False
    assert any("Docling" in m for m in host.log.errors)
    assert "pip install docling" in host.log.all_text
    assert r"C:\Python313\python.exe" in host.log.all_text  # chỉ ra Python đã dò
    assert popen.calls == []  # chưa có Python thì không được thử chạy runner


def test_docling_source_run_still_points_to_install_button(pdf_path, tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "IS_FROZEN", False)
    monkeypatch.setattr(ol, "find_docling_python", lambda: (None, []))
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(tmp_path)) is False
    assert "Cài đặt Docling" in host.log.all_text


def test_docling_reports_missing_tesseract_binary(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: None)
    popen = _fake_runner(monkeypatch)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("Tesseract" in m for m in host.log.errors)
    assert popen.calls == []


def test_docling_reports_missing_pytesseract(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    monkeypatch.setattr(ol, "pytesseract", None)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("pytesseract" in m for m in host.log.errors)


def test_docling_fails_cleanly_when_vietnamese_pack_cannot_be_downloaded(pdf_path, tmp_path, monkeypatch):
    """Mất mạng lúc tải vie.traineddata: báo lỗi rõ, không chạy runner với dữ liệu thiếu."""
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (False, str(tmp_path / "tessdata")))

    def offline(url, dest):
        raise OSError("Network is unreachable")
    monkeypatch.setattr(ol.urllib.request, "urlretrieve", offline)
    popen = _fake_runner(monkeypatch)
    host = _host(["convert_pdf_with_docling"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("tiếng Việt" in m for m in host.log.errors)
    assert popen.calls == []


def test_docling_passes_explicit_paths_to_runner(pdf_path, tmp_path, monkeypatch):
    """Runner phải nhận đúng Python, tessdata, thư mục model, lệnh Tesseract — thiếu
    tessdata thì Docling mặc định sang fra/deu/spa/eng và mất tiếng Việt."""
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    popen = _fake_runner(monkeypatch, markdown="# Biên bản\n\nNội dung tài liệu đủ dài để vượt ngưỡng kiểm tra rỗng.")
    host = _host(["convert_pdf_with_docling", "_redact", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True

    cmd, kwargs = popen.calls[0]
    assert cmd[0] == "C:/py/python.exe"
    assert cmd[1] == str(ol.DOCLING_RUNNER)
    assert cmd[2] == str(pdf_path)
    assert cmd[cmd.index("--models-dir") + 1] == str(tmp_path / "docling_models")
    assert cmd[cmd.index("--tessdata-dir") + 1] == str(tmp_path / "tessdata")
    assert cmd[cmd.index("--tesseract-cmd") + 1] == "tesseract"
    assert kwargs["env"]["PYTHONUTF8"] == "1"
    assert kwargs["encoding"] == "utf-8"
    assert ol.DOCLING_RUNNER.is_file()


def test_docling_relays_runner_log_lines(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(
        monkeypatch,
        lines=["LOG|warning|  Chưa có mô hình cục bộ, đang tải về\n",
               "noise không theo giao thức\n",
               "LOG|success|  Tải mô hình thành công\n"],
        markdown="# Biên bản\n\nNội dung tài liệu đủ dài để vượt ngưỡng kiểm tra rỗng.",
    )
    host = _host(["convert_pdf_with_docling", "_redact", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True
    assert ("  Chưa có mô hình cục bộ, đang tải về", "warning") in host.log.entries
    assert ("  Tải mô hình thành công", "success") in host.log.entries
    assert "noise" not in host.log.all_text


def test_docling_runner_import_failure_invalidates_cache(pdf_path, tmp_path, monkeypatch):
    """Exit 2 = Python đã dò được nhưng giờ không import nổi Docling (vd. vừa gỡ):
    phải quên cache để lần sau dò lại thay vì cứ chọn mãi Python hỏng đó."""
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    monkeypatch.setattr(ol, "_docling_python_cache", "C:/py/python.exe")
    _fake_runner(monkeypatch, lines=["LOG|error|không import được Docling: DLL load failed\n"], exit_code=2)
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("DLL load failed" in m for m in host.log.errors)
    assert ol._docling_python_cache is None


def test_docling_model_download_failure_is_reported_once(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, lines=["LOG|error|Lỗi: Không tải được mô hình Docling: offline\n"], exit_code=3)
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert len(host.log.errors) == 1
    assert "Không tải được mô hình" in host.log.errors[0]


def test_docling_runner_crash_surfaces_last_output(pdf_path, tmp_path, monkeypatch):
    """Runner chết đột ngột (thiếu RAM, DLL torch lỗi) mà không kịp báo theo giao thức:
    phải cho người dùng thấy vài dòng cuối thay vì chỉ 'thất bại'."""
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, lines=["Traceback (most recent call last):\n", "MemoryError\n"], exit_code=1)
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("MemoryError" in m and "mã thoát 1" in m for m in host.log.errors)
    assert list(out_dir.iterdir()) == []


def test_docling_popen_oserror_is_reported_not_raised(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)

    def boom(*a, **k):
        raise PermissionError("Access is denied")
    monkeypatch.setattr(ol.subprocess, "Popen", boom)
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("Access is denied" in m for m in host.log.errors)


def test_docling_reports_empty_result_and_suggests_other_modes(pdf_path, tmp_path, monkeypatch):
    """Bug cũ ở V2.1: Docling trả kết quả rỗng mà vẫn xuất file trống."""
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, markdown="")
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("rỗng" in m for m in host.log.errors)
    assert "OCR" in host.log.all_text  # gợi ý người dùng đổi sang chế độ khác
    assert list(out_dir.iterdir()) == []  # không để lại file rỗng


def test_docling_runner_reports_ok_but_writes_no_file(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, markdown=None, exit_code=0)
    host = _host(["convert_pdf_with_docling", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is False
    assert any("không đọc được kết quả" in m for m in host.log.errors)


def test_docling_writes_markdown_output(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, markdown="# Biên bản\n\nNội dung tài liệu đủ dài để vượt ngưỡng kiểm tra rỗng.")
    host = _host(["convert_pdf_with_docling", "_redact", "_run_docling_runner"])

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True
    assert (out_dir / "hoso.md").read_text(encoding="utf-8").startswith("# Biên bản")


def test_docling_output_is_redacted_when_enabled(pdf_path, tmp_path, monkeypatch):
    out_dir = _ready_docling_env(monkeypatch, tmp_path)
    _fake_runner(monkeypatch, markdown="# Biên bản\n\nÔng A, CCCD số 079123456789, điện thoại 0901234567.")
    host = _host(["convert_pdf_with_docling", "_redact", "_run_docling_runner"], redact_pii_enabled=True)

    assert host.convert_pdf_with_docling(pdf_path, str(out_dir)) is True
    written = (out_dir / "hoso.md").read_text(encoding="utf-8")
    assert "079123456789" not in written
    assert "[ĐÃ ẨN: CCCD]" in written
