import logging
import re

_KEY_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}"
    r"|AIza[A-Za-z0-9_\-]{30,}"
    r"|sk-ant-[A-Za-z0-9_\-]{20,}"
    r"|[A-Za-z0-9]{40,})"
)


class RedactingFormatter(logging.Formatter):
    """
    Sanitizes fully rendered log messages and tracebacks before output.
    Processes the final string output so records from any child logger
    and multi-line tracebacks are guaranteed to have keys redacted.
    """

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return _KEY_PATTERN.sub("[REDACTED]", formatted)


def install_redacting_formatters() -> None:
    """
    Attach RedactingFormatter to every handler on logging.root so all log
    output paths (including standalone workers and propagated records) are sanitized.
    """
    for handler in logging.root.handlers:
        fmt = handler.formatter
        fmt_str = fmt._fmt if fmt else "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
        date_fmt = fmt.datefmt if fmt else None
        handler.setFormatter(RedactingFormatter(fmt_str, datefmt=date_fmt))
