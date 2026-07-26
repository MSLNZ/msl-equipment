"""Configuration settings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import run


@dataclass
class Logo:
    """Information about the logo."""

    src: str = ""
    """Location of the image."""

    height: int = 60
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

    def git_pull(self) -> str:
        """Perform a `git pull` of the equipment-register directory.

        Returns:
            An error message, if an error occurred.
        """
        try:
            out = run(["git", "pull"], cwd=self.dir, check=False, capture_output=True)  # noqa: S607
        except FileNotFoundError:
            return "ERROR! git is not installed, cannot sync"
        else:
            return "" if out.returncode == 0 else f"ERROR! {out.stderr.decode().rstrip()}"


@dataclass
class Config:
    """Configuration for the web application."""

    assets: str = "assets"
    """Path to the assets directory.

    Store the favicon.ico and custom.css files here.
    """

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

    port: int = 17025
    """The port number to use for the app."""

    registers: list[EquipmentRegister] = field(default_factory=list)
    """A list of `team -> path` mapping for each equipment register."""

    theme: str = "BOOTSTRAP"
    """A theme name in https://bootswatch.com/."""

    def load(self, path: str | Path, *, host: str | None = None, port: int | None = None) -> None:
        """Load a configuration file."""
        with Path(path).expanduser().open("rb") as fp:
            cfg = json.load(fp)

        self.assets = Path(cfg.get("assets", self.assets)).expanduser().as_posix()
        self.host = host or cfg.get("host", self.host)
        self.nmi = cfg.get("nmi", self.nmi)
        self.port = port or cfg.get("port", self.port)
        self.theme = cfg.get("theme", self.theme)
        self.logo = Logo(**cfg.get("logo", {}))
        self.navbar = NavBar(**cfg.get("navbar", {}))
        self.registers.extend(EquipmentRegister(team=k, dir=Path(v)) for k, v in cfg.get("registers", {}).items())

    @property
    def teams(self) -> list[str]:
        """Returns the list of `team` names."""
        return [t.team for t in self.registers]


cfg = Config()
