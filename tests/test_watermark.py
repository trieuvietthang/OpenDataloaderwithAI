"""Regression tests for pixel-filter watermark removal.

Covers both filter modes and the OCR-path open→filter→save sequence
that previously passed a Path into _apply_pixel_watermark_removal
(AttributeError swallowed → no-op).
"""
from pathlib import Path

import pytest
from PIL import Image


class _DummyLog:
    def emit(self, *args, **kwargs):
        pass


class _FilterHost:
    """Minimal stand-in so we can call the unbound worker method without Qt."""

    def __init__(self, use_deep_inpaint=False, use_contrast=True, use_morphology=False):
        self.use_deep_inpaint = use_deep_inpaint
        self.use_contrast = use_contrast
        self.use_morphology = use_morphology
        self.log = _DummyLog()


def _make_host(**kwargs):
    from openloader import ConversionWorker

    host = _FilterHost(**kwargs)
    host._apply_pixel_watermark_removal = ConversionWorker._apply_pixel_watermark_removal.__get__(
        host, _FilterHost
    )
    return host


def _sample_rgb():
    """Black text pixel, mid-gray stamp, light-gray wash, white paper."""
    img = Image.new("RGB", (4, 1), (255, 255, 255))
    img.putpixel((0, 0), (0, 0, 0))
    img.putpixel((1, 0), (150, 150, 150))
    img.putpixel((2, 0), (200, 200, 200))
    img.putpixel((3, 0), (255, 255, 255))
    return img


def test_light_mode_keeps_text_and_drops_pale_wash():
    host = _make_host(use_deep_inpaint=False, use_contrast=False, use_morphology=False)
    out = host._apply_pixel_watermark_removal(_sample_rgb()).convert("RGB")

    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((1, 0)) == (255, 255, 255)  # 150 is above threshold 130
    assert out.getpixel((2, 0)) == (255, 255, 255)
    assert out.getpixel((3, 0)) == (255, 255, 255)


def test_deep_inpaint_keeps_mid_gray_as_ink():
    host = _make_host(use_deep_inpaint=True, use_contrast=False, use_morphology=False)
    out = host._apply_pixel_watermark_removal(_sample_rgb()).convert("RGB")

    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((1, 0)) == (0, 0, 0)  # 150 is below threshold 160
    assert out.getpixel((2, 0)) == (255, 255, 255)
    assert out.getpixel((3, 0)) == (255, 255, 255)


def test_ocr_path_open_filter_save(tmp_path: Path):
    """Mirrors convert_pdf_with_ocr: Path must be opened before filtering."""
    img_path = tmp_path / "page_1.png"
    _sample_rgb().save(img_path)

    host = _make_host(use_deep_inpaint=False, use_contrast=False, use_morphology=False)
    wm_img = Image.open(str(img_path))
    wm_img = host._apply_pixel_watermark_removal(wm_img)
    wm_img.save(str(img_path))

    saved = Image.open(str(img_path)).convert("RGB")
    assert saved.getpixel((0, 0)) == (0, 0, 0)
    assert saved.getpixel((2, 0)) == (255, 255, 255)


def test_passing_path_is_not_a_valid_image():
    """Documents the old bug: a Path has no .convert, so the helper must not be called with one."""
    host = _make_host(use_contrast=False, use_morphology=False)
    with pytest.raises(Exception):
        host._apply_pixel_watermark_removal(Path("page_1.png")).convert("RGB")
