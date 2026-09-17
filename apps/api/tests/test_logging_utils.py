"""
Unit tests for services/logging_utils.py — API key redaction in logging.
"""

import logging
from services.logging_utils import RedactingFormatter, install_redacting_formatters


def test_redacting_formatter_masks_openai_key():
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Using key sk-1234567890abcdef1234567890 to authenticate",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "sk-1234567890abcdef1234567890" not in output
    assert "[REDACTED]" in output


def test_redacting_formatter_masks_gemini_key():
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connecting with key AIzaSyA123456789012345678901234567890",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "AIzaSyA123456789012345678901234567890" not in output
    assert "[REDACTED]" in output


def test_redacting_formatter_masks_anthropic_key():
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Anthropic token: sk-ant-api03-1234567890abcdefghij",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "sk-ant-api03-1234567890abcdefghij" not in output
    assert "[REDACTED]" in output


def test_install_redacting_formatters_attaches_to_root():
    handler = logging.StreamHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    try:
        install_redacting_formatters()
        assert isinstance(handler.formatter, RedactingFormatter)
    finally:
        root_logger.removeHandler(handler)
