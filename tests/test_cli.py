from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

from bce.cli import main


def test_cli_character_markdown_basic() -> None:
    buf_out = io.StringIO()
    with redirect_stdout(buf_out):
        rc = main(["character", "jesus", "--format", "markdown"])

    output = buf_out.getvalue()

    assert rc == 0
    assert isinstance(output, str)
    assert output.strip(), "expected non-empty markdown output"
    assert "jesus" in output
    assert output.lstrip().startswith("# ")


def test_cli_event_markdown_basic() -> None:
    buf_out = io.StringIO()
    with redirect_stdout(buf_out):
        rc = main(["event", "crucifixion", "--format", "markdown"])

    output = buf_out.getvalue()

    assert rc == 0
    assert isinstance(output, str)
    assert output.strip(), "expected non-empty markdown output"
    assert "crucifixion" in output
    assert ("## Accounts" in output) or ("## Participants" in output)


def test_cli_unknown_id_nonzero_exit() -> None:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = main(["character", "this-id-does-not-exist"])

    stdout = buf_out.getvalue()
    stderr = buf_err.getvalue()

    assert rc != 0
    assert "this-id-does-not-exist" in stderr or "not found" in stderr.lower()
    # stdout may or may not have content, but we don't rely on it.
