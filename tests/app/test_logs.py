"""Secrets in request URLs never reach the logs."""

import logging

from newsimpact.app.logs import JsonFormatter


def test_keys_and_webhooks_are_redacted() -> None:
    msg = ("HTTP Request: GET https://eodhd.com/api/eod/NVDA.US?api_token=SECRET123&fmt=json "
           "and POST https://discord.com/api/webhooks/123/abcTOKEN")  # fmt: skip
    record = logging.LogRecord("httpx", logging.INFO, "", 0, msg, (), None)
    line = JsonFormatter().format(record)
    assert "SECRET123" not in line and "abcTOKEN" not in line
    assert "api_token=***" in line and "fmt=json" in line
