from __future__ import annotations

import socket
from typing import TYPE_CHECKING

import pytest
from msl.equipment_webapp import main

if TYPE_CHECKING:
    from pathlib import Path


def test_help(capsys: pytest.CaptureFixture[str]) -> None:

    with pytest.raises(SystemExit) as e:
        main(["--help"])

    result = capsys.readouterr()
    assert result.out.startswith("usage: msl-equipment-webapp")
    assert e.value.code == 0


def test_config_not_found() -> None:
    with pytest.raises(FileNotFoundError, match=r"missing.json"):
        main(["missing.json"])


def test_static_dir_not_found(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    _ = file.write_text('{"static": "missing-directory"}')

    # Comes from the `starlette` package
    with pytest.raises(RuntimeError, match=r"missing-directory"):
        main([str(file)])


def test_port_in_use(tmp_path: Path) -> None:
    file = tmp_path / "config.json"

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()

    _ = file.write_text(f'{{"static": "{tmp_path.as_posix()}", "port": {port}, "host": "127.0.0.1"}}')
    with pytest.raises(SystemExit):
        main([str(file)])

    s.close()
