"""Regression tests for the page-range parser used by the OCR page-range feature."""
from openloader import parse_page_range


def test_empty_string_selects_all_pages():
    assert parse_page_range("", 5) == {0, 1, 2, 3, 4}
    assert parse_page_range("   ", 5) == {0, 1, 2, 3, 4}


def test_single_page():
    assert parse_page_range("3", 10) == {2}


def test_comma_separated_pages():
    assert parse_page_range("1, 3, 5", 10) == {0, 2, 4}


def test_range_is_inclusive_of_both_ends():
    assert parse_page_range("2-4", 10) == {1, 2, 3}


def test_mixed_ranges_and_singles():
    assert parse_page_range("1-2, 5, 8-9", 10) == {0, 1, 4, 7, 8}


def test_range_clamped_to_document_length():
    assert parse_page_range("8-20", 10) == {7, 8, 9}


def test_start_below_one_clamped_to_zero():
    assert parse_page_range("-2-3", 10) == set()  # malformed ("- 2 - 3" -> 3 parts) is silently dropped
    assert parse_page_range("0-3", 10) == {0, 1, 2}


def test_malformed_parts_are_ignored_not_fatal():
    assert parse_page_range("abc, 2, ,", 10) == {1}


def test_out_of_range_single_page_kept_as_is():
    # Single-page entries are not clamped like ranges are; callers filter against total_pages.
    assert parse_page_range("99", 10) == {98}
