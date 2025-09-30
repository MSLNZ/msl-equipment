"""Hyperlinks (a.k.a. HTML-like anchors) in terminal emulators.

See this [gist](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda) for an overview.

OSC (operating system command) is typically ESC ].
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from subprocess import Popen
from typing import Callable

schemes = ("vs", "vscode", "pycharm", "n++")

regexp = re.compile(r"(?P<scheme>[^:]+)://file/(?P<file>([a-zA-Z]:)?[^:]+)(:(?P<line>\d+))?(:(?P<column>\d+))?")


def register_uri_scheme(name: str) -> None:
    """Register a custom URI Scheme handler in the Windows Registry.

    Args:
        name: URI scheme name.

    Raises:
        PermissionError: If Python is not running within an elevated terminal.
    """
    import winreg  # noqa: PLC0415

    name = name.lower()

    # Visual Studio Code creates the vscode URI scheme handler in the Windows Registry when it is installed
    if name == "vscode":
        return

    root = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "")
    winreg.SetValue(root, name, winreg.REG_SZ, f"URL:{name}")

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

    name = name.lower()

    # Visual Studio Code creates the vscode URI scheme handler in the Windows Registry when it is installed
    # So we should not remove it
    if name == "vscode":
        return

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


def pycharm_uri_scheme_handler(file: str, line: int, column: int) -> None:
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
                    cmd.extend(["--line", str(line)])
                if column:
                    cmd.extend(["--column", str(column)])
                cmd.append(file)
                _ = Popen(cmd)  # noqa: S603
                return


def vs_uri_scheme_handler(file: str, line: int, column: int) -> None:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG001
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Visual Studio.

    The Visual Studio URI Scheme must first be registered using `register_uri_scheme(name="VS")`

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
        for path in Path(pf).glob("Microsoft Visual Studio\\*\\Community\\Common7\\IDE"):
            exe = path / "devenv.exe"
            if exe.is_file():
                cmd = [str(exe), "/Edit", file]
                if line:
                    cmd.extend(["/Command", f"Edit.GoTo {line}"])
                # `column` is currently not supported by the GoTo option
                _ = Popen(cmd)  # noqa: S603
                return


def notepad_pp_uri_scheme_handler(file: str, line: int, column: int) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Notepad++.

    The Notepad++ URI Scheme must first be registered using `register_uri_scheme(name="npp")`

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
        exe = Path(pf) / "Notepad++" / "notepad++.exe"
        if exe.is_file():
            cmd = [str(exe)]
            if line:
                cmd.append(f"-n{line}")
            if column:
                cmd.append(f"-c{column}")
            cmd.append(file)
            _ = Popen(cmd)  # noqa: S603
            return


def uri_scheme_handler(command: str) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

    Args:
        command: The URI Scheme command stored in the Windows Registry.
    """
    match = regexp.match(command)
    if match is None:
        return

    scheme = match["scheme"].lower()
    handler = handler_map.get(scheme)
    if handler is None:
        return

    line = int(match["line"]) if match["line"] is not None else 0
    column = int(match["column"]) if match["column"] is not None else 0
    handler(match["file"], line, column)


handler_map: dict[str, Callable[[str, int, int], None]] = {
    "pycharm": pycharm_uri_scheme_handler,
    "vs": vs_uri_scheme_handler,
    "n++": notepad_pp_uri_scheme_handler,
    # vscode has its own handler
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        uri_scheme_handler(sys.argv[1])
