"""Regression tests for ConversionWorker.convert_docx's format branching.

Mammoth/markdownify are faked so these tests don't need a real .docx file.
Also guards against the once-fixed ".markdown" vs ".md" extension bug
(see PROGRESS.md item 9): FORMAT_EXTENSIONS must be applied to every format.
"""
import json

import openloader as ol
from openloader import ConversionWorker


class _DummyLog:
    def emit(self, *args, **kwargs):
        pass


class _ConvertHost:
    def __init__(self, formats, redact_pii_enabled=False):
        self.formats = formats
        self.redact_pii_enabled = redact_pii_enabled
        self.log = _DummyLog()


def _make_host(formats, redact_pii_enabled=False):
    host = _ConvertHost(formats, redact_pii_enabled)
    host.convert_docx = ConversionWorker.convert_docx.__get__(host, _ConvertHost)
    host._redact = ConversionWorker._redact.__get__(host, _ConvertHost)
    return host


class _FakeMammothResult:
    def __init__(self, value, messages=()):
        self.value = value
        self.messages = messages


class _FakeMammoth:
    def convert_to_html(self, f):
        return _FakeMammothResult("<p>Hello <b>World</b></p>")

    def extract_raw_text(self, f):
        return _FakeMammothResult("Hello World")


class _FakeMarkdownify:
    def markdownify(self, html, heading_style="ATX"):
        return "Hello **World**"


def test_all_formats_write_expected_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "mammoth", _FakeMammoth())
    monkeypatch.setattr(ol, "markdownify", _FakeMarkdownify())

    docx_path = tmp_path / "sample.docx"
    docx_path.write_bytes(b"fake docx bytes")  # content ignored by the fake mammoth
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    host = _make_host(["markdown", "text", "html", "json"])
    assert host.convert_docx(docx_path, out_dir) is True

    assert (out_dir / "sample.md").exists()
    assert (out_dir / "sample.txt").exists()
    assert (out_dir / "sample.html").exists()
    assert (out_dir / "sample.json").exists()
    # would fail if FORMAT_EXTENSIONS mapping regressed to raw format names
    assert not (out_dir / "sample.markdown").exists()

    assert "World" in (out_dir / "sample.md").read_text(encoding="utf-8")

    json_content = json.loads((out_dir / "sample.json").read_text(encoding="utf-8"))
    assert json_content["file_type"] == "docx"
    assert json_content["text"] == "Hello World"
    assert json_content["markdown"] == "Hello **World**"


class _PiiMammoth:
    def convert_to_html(self, f):
        return _FakeMammothResult("<p>Ông A, CCCD 079123456789, ĐT 0901234567</p>")

    def extract_raw_text(self, f):
        return _FakeMammothResult("Ông A, CCCD 079123456789, ĐT 0901234567")


def test_pii_is_redacted_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "mammoth", _PiiMammoth())
    monkeypatch.setattr(ol, "markdownify", _FakeMarkdownify())

    docx_path = tmp_path / "hoso.docx"
    docx_path.write_bytes(b"fake")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    host = _make_host(["html", "text"], redact_pii_enabled=True)
    assert host.convert_docx(docx_path, out_dir) is True

    for name in ("hoso.html", "hoso.txt"):
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "079123456789" not in content
        assert "0901234567" not in content
        assert "[ĐÃ ẨN: CCCD]" in content


def test_pii_left_intact_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "mammoth", _PiiMammoth())
    monkeypatch.setattr(ol, "markdownify", _FakeMarkdownify())

    docx_path = tmp_path / "hoso.docx"
    docx_path.write_bytes(b"fake")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    host = _make_host(["text"], redact_pii_enabled=False)
    assert host.convert_docx(docx_path, out_dir) is True
    assert "079123456789" in (out_dir / "hoso.txt").read_text(encoding="utf-8")


def test_returns_false_when_mammoth_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "mammoth", None)
    host = _make_host(["markdown"])
    assert host.convert_docx(tmp_path / "x.docx", tmp_path) is False


def test_returns_false_on_missing_file_instead_of_raising(tmp_path, monkeypatch):
    monkeypatch.setattr(ol, "mammoth", _FakeMammoth())
    monkeypatch.setattr(ol, "markdownify", _FakeMarkdownify())
    host = _make_host(["markdown"])
    assert host.convert_docx(tmp_path / "does_not_exist.docx", tmp_path) is False
