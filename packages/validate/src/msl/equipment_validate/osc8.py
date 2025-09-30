"""Hyperlinks (a.k.a. HTML-like anchors) in terminal emulators.

See this [gist](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda) for an overview.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from subprocess import Popen
from typing import Callable

regex = re.compile(
    r"(?P<scheme>[^:]+)://open/?\?file=(?P<file>[^&]+)(&line=(?P<line>[^&]+))?(&column=(?P<column>[^&]+))?",
)


def register_uri_scheme(name: str) -> None:
    """Register a custom URI Scheme handler in the Windows Registry.

    Args:
        name: URI scheme name (e.g., PyCharm).

    Raises:
        PermissionError: If Python is not running within an elevated terminal.
    """
    import winreg  # noqa: PLC0415

    root = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "")
    winreg.SetValue(root, name, winreg.REG_SZ, f"URL:{name.lower()}")

    key = winreg.CreateKey(root, name)
    winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    exe = Path(sys.base_exec_prefix) / "pythonw.exe"
    shell = winreg.CreateKey(key, "shell")
    _open = winreg.CreateKey(shell, "open")
    winreg.SetValue(_open, "command", winreg.REG_SZ, f'"{exe}" "{__file__}" "%1"')

    winreg.CloseKey(_open)
    winreg.CloseKey(shell)
    winreg.CloseKey(key)
    winreg.CloseKey(root)


def unregister_uri_scheme(name: str) -> None:
    """Unregister a custom URI Scheme handler from the Windows Registry.

    Args:
        name: URI scheme name.

    Raises:
        PermissionError: If Python is not running within an elevated terminal.
        FileNotFoundError: If `name` is not found in the Windows Registry.
    """
    import winreg  # noqa: PLC0415

    _open = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{name}\\shell\\open")
    winreg.DeleteKey(_open, "command")
    winreg.CloseKey(_open)

    shell = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{name}\\shell")
    winreg.DeleteKey(shell, "open")
    winreg.CloseKey(shell)

    key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, name)
    winreg.DeleteKey(key, "shell")
    winreg.CloseKey(key)

    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, name)


def pycharm_uri_scheme_handler(file: str, line: str | None, column: str | None) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in PyCharm.

    The PyCharm URI Scheme must first be registered using `register_uri_scheme(name="PyCharm")`

    Alternatively, install [this] PyCharm Plugin to handle *any*
    `filename.ext:line:character` link within the PyCharm terminal.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    [this]: https://github.com/anthraxx/intellij-awesome-console/pull/102#issuecomment-2069122744
    """
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
        for path in Path(pf).glob("JetBrains\\*\\bin"):
            exe = path / "pycharm64.exe"
            if exe.is_file():
                cmd: list[str] = [str(exe)]
                if line:
                    cmd.extend(["--line", line])
                if column:
                    cmd.extend(["--column", column])
                cmd.append(file)
                _ = Popen(cmd)  # noqa: S603
                return


def vs_uri_scheme_handler(file: str, line: str | None, column: str | None) -> None:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG001
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Visual Studio.

    The Visual Studio URI Scheme must first be registered using `register_uri_scheme(name="VS")`

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
        for path in Path(pf).glob("Microsoft Visual Studio\\*\\Community\\Common7\\IDE"):
            exe = path / "devenv.exe"
            if exe.is_file():
                # `column` is currently not supported by the GoTo option
                _ = Popen([str(exe), "/Edit", file, "/Command", f"Edit.GoTo {line or ''}"])  # noqa: S603
                return


def uri_scheme_handler(command: str) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

    Args:
        command: The URI Scheme command stored in the Windows Registry.
    """
    match = regex.match(command)
    if match is None:
        return

    handler = handler_map.get(match["scheme"])
    if handler is None:
        msg = f"A URI Scheme handler for {command!r} does not exist"
        raise ValueError(msg)

    handler(match["file"], match["line"], match["column"])


handler_map: dict[str, Callable[[str, str | None, str | None], None]] = {
    "pycharm": pycharm_uri_scheme_handler,
    "vs": vs_uri_scheme_handler,
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        uri_scheme_handler(sys.argv[1])
