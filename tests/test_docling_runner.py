"""Test docling_runner.py bằng tiến trình THẬT với một gói `docling` giả.

Gói giả (không cần torch ~2GB) được đặt trước trên PYTHONPATH nên che luôn cả Docling
thật nếu máy dev có cài — test luôn chạy được trên CI. Cách này kiểm chứng đúng thứ mà
bản .exe dùng: mã thoát, giao thức `LOG|...`, UTF-8 qua pipe, tham số dòng lệnh.
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import openloader as ol
from openloader import ConversionWorker

RUNNER = Path(ol.DOCLING_RUNNER)

LONG_MD = "# Biên bản\n\nNội dung tài liệu đủ dài để vượt ngưỡng kiểm tra rỗng."

FAKE_DOCLING = {
    "docling/__init__.py": "",
    "docling/datamodel/__init__.py": "",
    "docling/utils/__init__.py": "",
    "docling/datamodel/base_models.py": "class InputFormat:\n    PDF = 'pdf'\n",
    "docling/utils/model_downloader.py": textwrap.dedent('''
        import os
        from pathlib import Path

        def download_models(output_dir=None, progress=False, **kwargs):
            if os.environ.get("FAKE_DOCLING_FAIL_DOWNLOAD"):
                raise OSError("Network is unreachable")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            (Path(output_dir) / "downloaded_model.bin").write_bytes(b"fake")
    '''),
    "docling/datamodel/pipeline_options.py": textwrap.dedent('''
        from types import SimpleNamespace

        class PdfPipelineOptions:
            def __init__(self, **kw):
                self.kw = kw
                self.table_structure_options = SimpleNamespace(mode=None)
                self.ocr_options = None

        class TesseractCliOcrOptions:
            def __init__(self, **kw):
                self.kw = kw

        class TableFormerMode:
            ACCURATE = "accurate"

        class OcrMode:
            FULL_PAGE = "full_page"
    '''),
    "docling/document_converter.py": textwrap.dedent('''
        import json
        import os
        from types import SimpleNamespace

        class PdfFormatOption:
            def __init__(self, pipeline_options=None):
                self.pipeline_options = pipeline_options

        class DocumentConverter:
            def __init__(self, format_options=None):
                self.options = format_options["pdf"].pipeline_options

            def convert(self, source):
                if os.environ.get("FAKE_DOCLING_FAIL_CONVERT"):
                    raise RuntimeError("layout model crashed")
                record = os.environ.get("FAKE_DOCLING_RECORD")
                if record:
                    json.dump({
                        "source": source,
                        "artifacts_path": self.options.kw["artifacts_path"],
                        "table_mode": self.options.table_structure_options.mode,
                        "ocr": self.options.ocr_options.kw,
                    }, open(record, "w", encoding="utf-8"))
                md = os.environ.get("FAKE_DOCLING_MD", "")
                document = SimpleNamespace(export_to_markdown=lambda **kw: md)
                return SimpleNamespace(document=document)
    '''),
}


@pytest.fixture
def fake_docling_dir(tmp_path):
    root = tmp_path / "fake_site"
    for rel, source in FAKE_DOCLING.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return root


@pytest.fixture
def run_runner(tmp_path, fake_docling_dir):
    models = tmp_path / "models"
    out_md = tmp_path / "out.md"
    pdf = tmp_path / "hoso.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    def run(extra_env=None, site=None):
        env = ol._docling_subprocess_env()
        env["PYTHONPATH"] = str(site or fake_docling_dir)
        env.update(extra_env or {})
        proc = subprocess.run(
            [sys.executable, str(RUNNER), str(pdf), str(out_md),
             "--models-dir", str(models), "--tessdata-dir", str(tmp_path / "tessdata"),
             "--tesseract-cmd", "tesseract"],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=60,
        )
        log_lines = [ln.split("|", 2) for ln in proc.stdout.splitlines() if ln.startswith("LOG|")]
        return proc, log_lines

    run.models, run.out_md, run.pdf = models, out_md, pdf
    return run


def test_runner_file_ships_next_to_app():
    """LexGuard.spec đóng gói file này; thiếu nó thì mọi lần chạy Docling đều lỗi."""
    assert RUNNER.is_file()
    assert "docling_runner.py" in (Path(__file__).parent.parent / "LexGuard.spec").read_text(encoding="utf-8")


def test_runner_success_writes_markdown_and_downloads_models_once(run_runner):
    proc, logs = run_runner({"FAKE_DOCLING_MD": LONG_MD})

    assert proc.returncode == 0
    assert run_runner.out_md.read_text(encoding="utf-8") == LONG_MD
    assert (run_runner.models / "downloaded_model.bin").exists()
    assert any("đang tải về" in msg for _, _, msg in logs)

    (run_runner.models / "downloaded_model.bin").write_bytes(b"cached")
    proc, logs = run_runner({"FAKE_DOCLING_MD": LONG_MD})
    assert proc.returncode == 0
    assert not any("đang tải về" in msg for _, _, msg in logs)  # đã có model -> không tải lại
    assert (run_runner.models / "downloaded_model.bin").read_bytes() == b"cached"


def test_runner_configures_vietnamese_tesseract_and_model_dir(run_runner, tmp_path):
    record = tmp_path / "record.json"
    proc, _ = run_runner({"FAKE_DOCLING_MD": LONG_MD, "FAKE_DOCLING_RECORD": str(record)})

    assert proc.returncode == 0
    seen = json.loads(record.read_text(encoding="utf-8"))
    assert seen["source"] == str(run_runner.pdf)
    assert seen["artifacts_path"] == str(run_runner.models)
    assert seen["table_mode"] == "accurate"
    assert seen["ocr"]["lang"] == ["vie", "eng"]
    assert seen["ocr"]["path"] == str(tmp_path / "tessdata")
    assert seen["ocr"]["tesseract_cmd"] == "tesseract"
    assert seen["ocr"]["force_full_page_ocr"] is True


def test_runner_strips_image_placeholders_from_markdown(run_runner):
    md = "# Tiêu đề\n<!-- image -->\n![image]()\n\nĐoạn văn bản thật ở đây.\n![Image]()"
    proc, _ = run_runner({"FAKE_DOCLING_MD": md})

    assert proc.returncode == 0
    assert run_runner.out_md.read_text(encoding="utf-8") == "# Tiêu đề\n\nĐoạn văn bản thật ở đây."


def test_runner_exit_2_when_docling_cannot_be_imported(run_runner, tmp_path):
    broken = tmp_path / "broken_site"
    (broken / "docling").mkdir(parents=True)
    (broken / "docling" / "__init__.py").write_text("raise ImportError('DLL load failed: torch')", encoding="utf-8")

    proc, logs = run_runner(site=broken)

    assert proc.returncode == 2
    assert any(level == "error" and "DLL load failed" in msg for _, level, msg in logs)
    assert not run_runner.out_md.exists()


def test_runner_exit_3_when_models_cannot_be_downloaded(run_runner):
    proc, logs = run_runner({"FAKE_DOCLING_FAIL_DOWNLOAD": "1"})

    assert proc.returncode == 3
    assert any(level == "error" and "Network is unreachable" in msg for _, level, msg in logs)
    assert not run_runner.out_md.exists()


def test_runner_exit_1_when_conversion_crashes(run_runner):
    proc, logs = run_runner({"FAKE_DOCLING_FAIL_CONVERT": "1"})

    assert proc.returncode == 1
    assert any(level == "error" and "layout model crashed" in msg for _, level, msg in logs)
    assert not run_runner.out_md.exists()


# --- Đầu-cuối: ConversionWorker -> Popen thật -> docling_runner.py -> gói docling giả ---

class _Log:
    def __init__(self):
        self.entries = []

    def emit(self, message, level="info"):
        self.entries.append((message, level))


class _Host:
    redact_pii_enabled = True

    def __init__(self):
        self.log = _Log()


def test_end_to_end_through_real_subprocess_keeps_vietnamese_and_redacts(tmp_path, fake_docling_dir, monkeypatch):
    """Đường chạy đầy đủ như trong .exe, chỉ khác Python/Docling là giả: tiếng Việt phải
    nguyên vẹn qua pipe và PII phải bị ẩn trước khi ghi file."""
    md = "# Biên bản thừa phát lại\n\nÔng Nguyễn Văn A, CCCD số 079123456789."
    monkeypatch.setenv("FAKE_DOCLING_MD", md)
    real_env = ol._docling_subprocess_env
    monkeypatch.setattr(ol, "_docling_subprocess_env", lambda: {**real_env(), "PYTHONPATH": str(fake_docling_dir)})
    monkeypatch.setattr(ol, "find_docling_python", lambda: (sys.executable, [sys.executable]))
    monkeypatch.setattr(ol, "pytesseract", object())
    monkeypatch.setattr(ol, "find_tesseract_path", lambda: "tesseract")
    monkeypatch.setattr(ol, "check_tesseract_vietnamese", lambda: (True, str(tmp_path / "tessdata")))
    monkeypatch.setattr(ol, "DOCLING_MODELS_DIR", tmp_path / "docling_models")
    pdf = tmp_path / "Biên bản.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    host = _Host()
    for name in ("convert_pdf_with_docling", "_run_docling_runner", "_redact"):
        setattr(host, name, getattr(ConversionWorker, name).__get__(host, _Host))

    assert host.convert_pdf_with_docling(pdf, str(out_dir)) is True

    written = (out_dir / "Biên bản.md").read_text(encoding="utf-8")
    assert "Biên bản thừa phát lại" in written
    assert "079123456789" not in written and "[ĐÃ ẨN: CCCD]" in written
    assert any("tải về" in m for m, _ in host.log.entries)  # log của runner được chuyển tiếp
