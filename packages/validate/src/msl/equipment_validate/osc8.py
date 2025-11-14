"""Hyperlinks (a.k.a. HTML-like anchors) in terminal emulators.

See this [gist](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda) for an overview.

OSC (operating system command) is typically ESC ].
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from subprocess import Popen, run
from tempfile import TemporaryDirectory
from typing import Callable

schemes = ("vs", "vscode", "pycharm", "n++")

regexp = re.compile(r"(?P<scheme>[^:]+)://file/(?P<file>([a-zA-Z]:)?[^:]+)(:(?P<line>\d+))?(:(?P<column>\d+))?")


def register_uri_scheme(name: str) -> bool:
    """Register a custom URI Scheme handler in the Windows Registry.

    Args:
        name: URI scheme name.

    Returns:
        Whether registering the URI scheme was successful.

    Raises:
        PermissionError: If Python is not running within an elevated terminal.
    """
    import winreg  # noqa: PLC0415

    name = name.lower()

    # Visual Studio Code creates the vscode URI scheme handler in the Windows Registry when it is installed
    if name == "vscode":
        return False

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
    return True


def unregister_uri_scheme(name: str) -> bool:
    """Unregister a custom URI Scheme handler from the Windows Registry.

    Args:
        name: URI scheme name.

    Returns:
        Whether unregistering the URI scheme was successful.

    Raises:
        PermissionError: If Python is not running within an elevated terminal.
        FileNotFoundError: If `name` is not found in the Windows Registry.
    """
    import winreg  # noqa: PLC0415

    name = name.lower()

    # Visual Studio Code creates the vscode URI scheme handler in the Windows Registry when it is installed
    # So we should not remove it
    if name == "vscode":
        return False

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
    return True


def pycharm_uri_scheme_handler(file: str, line: int, column: int) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in PyCharm.

    The PyCharm URI Scheme must first be registered using `register_uri_scheme(name="PyCharm")`

    Alternatively, install [this] PyCharm Plugin to handle *any*
    `filename.ext:line:character` link within the PyCharm terminal.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    [this]: https://github.com/anthraxx/intellij-awesome-console/pull/102#issuecomment-2069122744
    """
    if not Path(file).is_file():
        return

    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:  # pragma: no cover
        for path in Path(pf).glob("JetBrains\\*\\bin"):
            for pycharm in ["pycharm64.exe", "pycharm.exe"]:
                exe = path / pycharm
                if exe.is_file():
                    cmd: list[str] = [str(exe)]
                    if line:
                        cmd.extend(["--line", str(line)])
                    if column:
                        cmd.extend(["--column", str(column)])
                    cmd.append(file)
                    _ = Popen(cmd)  # noqa: S603
                    return


def vs_uri_scheme_handler_devenv(file: str, line: int, column: int) -> None:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG001
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Visual Studio.

    The Visual Studio URI Scheme must first be registered using `register_uri_scheme(name="VS")`.

    Uses the Visual Studio devenv.exe tool to open the file.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    if not Path(file).is_file():
        return

    # The "/Command Edit.GoTo LINE" option works when VS is not currently open. If an instance of
    # VS is already running, the devenv.exe tool ignores the /Command option. The file is still
    # opened but remains at line 1. This is a known bug that Microsoft hasn't fixed for many years
    # https://learn.microsoft.com/en-us/answers/questions/919213/vs2019-open-file-and-goto-line
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:  # pragma: no cover
        for path in Path(pf).glob("Microsoft Visual Studio\\*\\Community\\Common7\\IDE"):
            exe = path / "devenv.exe"
            if exe.is_file():
                cmd = [str(exe), "/Edit", file]
                if line:
                    cmd.extend(["/Command", f"Edit.GoTo {line}"])
                # `column` is currently not supported by the GoTo option
                _ = Popen(cmd)  # noqa: S603
                return


def vs_uri_scheme_handler_dte(file: str, line: int, column: int) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Visual Studio.

    The Visual Studio URI Scheme must first be registered using `register_uri_scheme(name="VS")`.

    Uses the Visual Studio DTE (Development Tools Environment) COM object to open the file.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    if not Path(file).is_file():
        return

    # Temporarily create a Visual Basic Script to open (or create) an instance of Visual Studio
    # with the specified file opened at the line and column numbers
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "open-vs.vbs"
        _ = path.write_text(f"""
            On Error Resume Next
            Set dte = GetObject(, "VisualStudio.DTE")
            If Err.Number <> 0 Then
                Set dte = CreateObject("VisualStudio.DTE")
            End If
            dte.MainWindow.Activate
            dte.MainWindow.Visible = True
            dte.UserControl = True
            dte.ItemOperations.OpenFile "{file}"
            dte.ActiveDocument.Selection.MoveToLineAndOffset {line}, {column + 1}
        """)
        __ = run([r"C:\Windows\SysWOW64\wscript.exe", path], check=False)  # noqa: S603


def notepad_pp_uri_scheme_handler(file: str, line: int, column: int) -> None:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file in Notepad++.

    The Notepad++ URI Scheme must first be registered using `register_uri_scheme(name="npp")`

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    if not Path(file).is_file():
        return

    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:  # pragma: no cover
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


def uri_scheme_handler(command: str) -> bool:
    """Handles [OSC-8 Hyperlinks] in the Windows Terminal to open a file.

    [OSC-8 Hyperlinks]: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

    Args:
        command: The URI Scheme command stored in the Windows Registry.
    """
    match = regexp.match(command)
    if match is None:
        return False

    scheme = match["scheme"].lower()
    handler = handler_map.get(scheme)
    if handler is None:
        return False

    line = int(match["line"]) if match["line"] is not None else 0
    column = int(match["column"]) if match["column"] is not None else 0
    handler(match["file"], line, column)
    return True


handler_map: dict[str, Callable[[str, int, int], None]] = {
    "pycharm": pycharm_uri_scheme_handler,
    "vs": vs_uri_scheme_handler_dte,
    "n++": notepad_pp_uri_scheme_handler,
    # vscode has its own handler
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        _ = uri_scheme_handler(sys.argv[1])
