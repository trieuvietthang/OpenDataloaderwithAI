"""Tests for PII redaction (xóa định danh cá nhân khi convert).

The false-negative cases matter as much as the positives here: over-redacting a
legal document (hiding the document date or a money amount) corrupts it, so
context-anchored patterns must stay narrow.
"""
from openloader import redact_pii


def test_empty_input_is_passthrough():
    assert redact_pii("") == ("", {})
    assert redact_pii(None) == (None, {})


def test_email():
    out, counts = redact_pii("Liên hệ: nguyenvana@example.com.vn để biết thêm")
    assert out == "Liên hệ: [ĐÃ ẨN: EMAIL] để biết thêm"
    assert counts == {"EMAIL": 1}


def test_bare_12_digit_cccd():
    out, counts = redact_pii("Số định danh 079123456789 do CSGT cấp")
    assert out == "Số định danh [ĐÃ ẨN: CCCD] do CSGT cấp"
    assert counts == {"CCCD": 1}


def test_cccd_with_context_keyword_and_separators():
    out, _ = redact_pii("CCCD số: 079 123 456 789")
    assert out == "CCCD số: [ĐÃ ẨN: CCCD]"


def test_cmnd_only_redacted_with_context():
    # 9 bare digits could be a money amount, so the keyword is required
    with_ctx, _ = redact_pii("CMND số 123456789")
    assert with_ctx == "CMND số [ĐÃ ẨN: CCCD]"

    bare, counts = redact_pii("Tổng cộng 123456789 đồng")
    assert bare == "Tổng cộng 123456789 đồng"
    assert counts == {}


def test_phone_plain_and_separated():
    plain, _ = redact_pii("Điện thoại 0901234567")
    assert plain == "Điện thoại [ĐÃ ẨN: SĐT]"

    dotted, _ = redact_pii("ĐT: 090.123.4567")
    assert dotted == "ĐT: [ĐÃ ẨN: SĐT]"

    intl, _ = redact_pii("Hotline +84901234567 gặp thư ký")
    assert intl == "Hotline [ĐÃ ẨN: SĐT] gặp thư ký"


def test_birth_date_redacted_but_document_date_kept():
    out, counts = redact_pii(
        "Hôm nay, ngày 14/09/2026, ông A sinh ngày 01/01/1990 có mặt"
    )
    assert "14/09/2026" in out  # ngày lập văn bản phải được giữ nguyên
    assert "01/01/1990" not in out
    assert out.count("[ĐÃ ẨN: NGÀY SINH]") == 1
    assert counts == {"NGÀY SINH": 1}


def test_birth_date_label_form():
    out, _ = redact_pii("Ngày sinh: 05/12/1985")
    assert out == "Ngày sinh: [ĐÃ ẨN: NGÀY SINH]"


def test_bank_account_requires_context():
    with_ctx, _ = redact_pii("Số tài khoản: 0123456789 tại Vietcombank")
    assert with_ctx == "Số tài khoản: [ĐÃ ẨN: STK] tại Vietcombank"

    amount, counts = redact_pii("Số tiền 500.000.000 đồng")
    assert amount == "Số tiền 500.000.000 đồng"
    assert counts == {}


def test_tax_code_requires_context():
    out, _ = redact_pii("MST: 0301234567")
    assert out == "MST: [ĐÃ ẨN: MST]"


def test_licence_plate():
    out, _ = redact_pii("Xe ô tô biển số 51A-12345 đỗ tại hiện trường")
    assert out == "Xe ô tô biển số [ĐÃ ẨN: BIỂN SỐ] đỗ tại hiện trường"


def test_multiple_types_counted_separately():
    out, counts = redact_pii(
        "Ông Nguyễn Văn A, CCCD số 079123456789, điện thoại 0901234567, "
        "email a@b.vn, sinh ngày 01/01/1990"
    )
    assert counts == {"CCCD": 1, "SĐT": 1, "EMAIL": 1, "NGÀY SINH": 1}
    assert "079123456789" not in out
    assert "0901234567" not in out


def test_context_keywords_work_without_diacritics():
    """OCR bản scan hay làm rơi dấu; PII vẫn phải được ẩn, không được lọt ra."""
    accented, counts_a = redact_pii(
        "CCCD số: 079078001234. Số tài khoản: 0071000123456. Mã số thuế: 0301234567"
    )
    plain, counts_p = redact_pii(
        "CCCD so: 079078001234. So tai khoan: 0071000123456. Ma so thue: 0301234567"
    )
    assert counts_a == counts_p == {"CCCD": 1, "STK": 1, "MST": 1}
    for out in (accented, plain):
        assert "0071000123456" not in out
        assert "0301234567" not in out


def test_document_essentials_are_preserved():
    """Ẩn nhầm ngày lập văn bản / số tiền / số hợp đồng sẽ làm hỏng hồ sơ."""
    text = (
        "Hôm nay, ngày 14/09/2026, tổng giá trị 2.500.000.000 đồng, "
        "hợp đồng số 123456789 ký ngày 01/06/2025."
    )
    out, counts = redact_pii(text)
    assert out == text
    assert counts == {}


def test_clean_text_is_untouched():
    text = "Biên bản ghi nhận sự việc tại số 12 đường Lê Lợi, Quận 1."
    assert redact_pii(text) == (text, {})


def test_placeholders_are_not_re_redacted():
    once, _ = redact_pii("CCCD 079123456789")
    twice, counts = redact_pii(once)
    assert twice == once
    assert counts == {}
