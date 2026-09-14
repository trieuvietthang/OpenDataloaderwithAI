"""Regression tests for ocr_page_with_ai's HTTP retry/backoff and response parsing.

Network calls are faked at the urllib.request.urlopen boundary so these tests
run offline and fast (time.sleep is stubbed out for the same reason).
"""
import json
import urllib.error

import pytest
from PIL import Image

from openloader import ocr_page_with_ai

GEMINI_PROFILE = {
    "api_type": "gemini",
    "api_key": "test-key",
    "base_url": "https://example.com",
    "model": "gemini-test",
}

OPENAI_PROFILE = {
    "api_type": "openai",
    "api_key": "test-key",
    "base_url": "https://example.com",
    "model": "gpt-test",
}


class _FakeResponse:
    """Minimal stand-in for the context manager urllib.request.urlopen returns."""

    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _gemini_payload(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def _openai_payload(text):
    return {"choices": [{"message": {"content": text}}]}


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)


@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "page.png"
    Image.new("RGB", (4, 4), (255, 255, 255)).save(img_path)
    return img_path


def test_gemini_success_strips_markdown_fence(sample_image, monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: _FakeResponse(_gemini_payload("```markdown\n# Hi\n```")),
    )
    assert ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=1) == "# Hi"


def test_openai_compatible_success(sample_image, monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: _FakeResponse(_openai_payload("hello world")),
    )
    assert ocr_page_with_ai(sample_image, OPENAI_PROFILE, max_retries=1) == "hello world"


def test_retries_on_503_then_succeeds(sample_image, monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)
        return _FakeResponse(_gemini_payload("ok"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=3) == "ok"
    assert calls["n"] == 2


def test_gives_up_after_max_retries_on_persistent_500(sample_image, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 500, "Internal Server Error", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(Exception, match="AI API failed after 2 attempts"):
        ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=2)


def test_non_retryable_http_error_raises_immediately(sample_image, monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=3)
    assert calls["n"] == 1  # 401 is not in the retry_codes list -> no retry


def test_respects_retry_after_header_on_429(sample_image, monkeypatch):
    calls = {"n": 0}
    sleep_calls = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {"Retry-After": "7"}, None)
        return _FakeResponse(_gemini_payload("ok"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
    assert ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=3) == "ok"
    assert sleep_calls == [7.0]


def test_cancel_check_aborts_before_first_attempt(sample_image, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise AssertionError("should not attempt request once cancelled")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(Exception, match="Đã hủy bởi người dùng"):
        ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=5, cancel_check=lambda: True)


def test_cancel_check_aborts_during_backoff_wait(sample_image, monkeypatch):
    state = {"n": 0}

    def cancel_check():
        state["n"] += 1
        return state["n"] > 1  # let the pre-attempt check pass once, cancel during the wait

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(Exception, match="Đã hủy bởi người dùng"):
        ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=5, cancel_check=cancel_check)


def _captured_prompt(sample_image, monkeypatch, **kwargs):
    """Run one successful call and return the prompt text actually sent."""
    sent = {}

    def fake_urlopen(req, timeout=None):
        sent["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(_gemini_payload("ok"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=1, **kwargs)
    return sent["payload"]["contents"][0]["parts"][0]["text"]


def test_pii_hint_appended_to_prompt_when_requested(sample_image, monkeypatch):
    prompt = _captured_prompt(sample_image, monkeypatch, redact_pii_hint=True)
    assert "[ĐÃ ẨN: HỌ TÊN]" in prompt
    assert "[ĐÃ ẨN: ĐỊA CHỈ]" in prompt
    assert "Markdown" in prompt  # chỉ dẫn gốc vẫn được giữ


def test_prompt_unchanged_when_pii_hint_off(sample_image, monkeypatch):
    prompt = _captured_prompt(sample_image, monkeypatch)
    assert "ĐÃ ẨN" not in prompt


def test_invalid_ai_response_shape_raises_clear_error(sample_image, monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: _FakeResponse({"unexpected": "shape"}),
    )
    with pytest.raises(Exception, match="Phản hồi AI không hợp lệ"):
        ocr_page_with_ai(sample_image, GEMINI_PROFILE, max_retries=1)
