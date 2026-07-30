"""Configuration settings."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Logo:
    """Information about the logo."""

    src: str = ""
    """Location of the image."""

    height: int = 50
    """Image height, in pixels."""

    margin_left: int = 5
    """Padding of left-side margin."""

    margin_right: int = 25
    """Padding of right-side margin."""

    def __post_init__(self) -> None:
        """Called automatically after the __init__ method finishes."""
        if not self.src:
            self.height = 0

    @property
    def style(self) -> dict[str, int]:
        """Returns the html style."""
        return {"marginLeft": self.margin_left, "marginRight": self.margin_right}


@dataclass
class NavBar:
    """Information about the NavBar."""

    color: str = "dark"
    """Sets the color of the NavBar.

    Main options are `primary`, `light` and `dark`. You can also choose one of the other
    contextual classes provided by Bootstrap (secondary, success, warning, danger, info, white)
    or any valid CSS color of your choice (e.g., a hex code, a decimal code or a CSS color name).
    """

    dark: bool = True
    """Whether to apply the navbar-dark class to the NavBar.

    Causes text in the children of the NavBar to use light colors for contrast/visibility.
    """


@dataclass
class EquipmentRegister:
    """Information about an equipment register."""

    team: str
    """The team that is responsible for the equipment register, e.g., `Light`, `Length`."""

    dir: Path
    """The directory that contains the equipment-register files for the `team`."""

    def __post_init__(self) -> None:
        """Called automatically after the __init__ method finishes."""
        self.dir = self.dir.expanduser()


@dataclass
class Config:
    """Configuration for the web application."""

    assets: str = "assets"
    """Path to the assets directory.

    Store the favicon.ico and custom.css files here.
    """

    git: str = "git"
    """Path to the [git](https://git-scm.com/) executable."""

    host: str = "0.0.0.0"  # noqa: S104
    """The network interface to run the app on.

    Default is to listen on all network interfaces.
    """

    logo: Logo = field(default_factory=Logo)
    """The logo to use in the navigation bar."""

    navbar: NavBar = field(default_factory=NavBar)
    """Navigation bar at the top of each webpage in the application."""

    nmi: str = "MSL"
    """Name of the National Metrology Institute."""

    pdflatex: str = "pdflatex"
    """Path to the `pdflatex` (e.g., [MiKTeX](https://miktex.org/), [TeX Live](https://www.tug.org/texlive/)) executable."""  # noqa: E501

    port: int = 17025
    """The port number to use for the app."""

    registers: list[EquipmentRegister] = field(default_factory=list)
    """A list of `team -> path` mapping for each equipment register."""

    theme: str = "BOOTSTRAP"
    """A theme name in https://bootswatch.com/."""

    verapdf: str = "verapdf.bat" if sys.platform == "win32" else "verapdf"
    """Path to the [veraPDF](https://verapdf.org/) executable."""

    def equipment_registers(self, teams: list[str]) -> list[EquipmentRegister]:
        """Returns the equipment registers for the specified `team` names."""
        return [t for t in self.registers if t.team in teams]

    def load(self, path: str | Path, *, host: str | None = None, port: int | None = None) -> None:
        """Load a configuration file."""
        with Path(path).expanduser().open("rb") as fp:
            data = json.load(fp)

        if not isinstance(data, dict):
            msg = "The configuration data must be a JSON object (a Python dict)"
            raise TypeError(msg)

        d: dict[str, Any] = data  # pyright: ignore[reportUnknownVariableType]
        self.nmi = d.get("nmi", self.nmi)
        self.theme = d.get("theme", self.theme)
        self.host = host or d.get("host", self.host)
        self.port = port or int(d.get("port", self.port))
        self.assets = Path(d.get("assets", self.assets)).expanduser().as_posix()
        self.git = Path(d.get("git", self.git)).expanduser().as_posix()
        self.pdflatex = Path(d.get("pdflatex", self.pdflatex)).expanduser().as_posix()
        self.verapdf = Path(d.get("verapdf", self.verapdf)).expanduser().as_posix()
        self.logo = Logo(**d.get("logo", {}))
        self.navbar = NavBar(**d.get("navbar", {}))
        self.registers.extend(EquipmentRegister(team=k, dir=Path(v)) for k, v in d.get("registers", {}).items())

    @property
    def teams(self) -> list[str]:
        """Returns the list of `team` names."""
        return [t.team for t in self.registers]


cfg = Config()
