"""Configuration settings."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from msl.equipment_validate import find_xml_files

from msl.equipment import Register


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
        elif self.src.startswith("~"):
            self.src = Path(self.src).expanduser().as_posix()

    @property
    def style(self) -> dict[str, int]:
        """Returns the html style."""
        return {"marginLeft": self.margin_left, "marginRight": self.margin_right}


@dataclass
class NavBar:
    """Information about the NavBar."""

    colour: str = "dark"
    """Sets the colour of the NavBar.

    Main options are `primary`, `light` and `dark`. You can also choose one of the other
    contextual classes provided by Bootstrap (secondary, success, warning, danger, info, white)
    or any valid CSS colour of your choice (e.g., a hex code, a decimal code or a CSS colour name).
    """

    dark: bool = True
    """Whether to apply the navbar-dark class to the NavBar.

    Causes text in the children of the NavBar to use light colours for contrast/visibility.
    """

    logo: Logo = field(default_factory=Logo)
    """The logo to use in the navigation bar."""

    def __post_init__(self) -> None:
        """Called automatically after the __init__ method finishes."""
        if isinstance(self.logo, dict):
            self.logo = Logo(**self.logo)  # pyright: ignore[reportUnknownArgumentType]


@dataclass
class EquipmentRegister:
    """Information about an equipment register."""

    team: str
    """The team that is responsible for the equipment register, e.g., `Light`, `Length`."""

    # Store the directory to the XML files (and not a list[Path] to the XML files) because
    # a user can to request a `git pull` on the directory and new XML files may exist after
    # the web app initially starts.
    directory: Path
    """The directory that contains the equipment-register files for the `team`."""

    def files(self) -> list[Path]:
        """Returns the XML files that compose the equipment register."""
        return find_xml_files(self.directory)


@dataclass
class Currency:
    """Price currency prefix and suffix symbols."""

    prefix: str = ""
    """Price prefix."""

    suffix: str = ""
    """Price suffix."""


@dataclass
class Price:
    """Display prices in a table using a locale-specific format."""

    format: str = ",.2f"
    """The format to use to display the value.

    See [d3-format](https://d3js.org/d3-format) for examples.
    """

    decimal: str = "."
    """The symbol to use for the decimal point."""

    thousands: str = ","
    """The symbol to use for the group separator."""

    grouping: list[int] = field(default_factory=lambda: [3])
    """The array of group sizes, cycled as needed."""

    currency: Currency = field(default_factory=Currency)
    """Price currency prefix and suffix symbols."""

    def __post_init__(self) -> None:
        """Called automatically after the __init__ method finishes."""
        if isinstance(self.currency, dict):
            self.currency = Currency(**self.currency)  # pyright: ignore[reportUnknownArgumentType]

    @property
    def format_locale(self) -> str:
        """Returns a [d3-formatLocale](https://d3js.org/d3-format#formatLocale) string to display a price value."""
        return (
            "d3.formatLocale({"
            f'"decimal": "{self.decimal}", '
            f'"thousands": "{self.thousands}", '
            f'"grouping": {self.grouping}, '
            f'"currency": ["{self.currency.prefix}", "{self.currency.suffix}"]'
            "})"
            f'.format("{self.format}")(params.value)'
        )


@dataclass
class SHA256Validation:
    """Controls the validation of `<sha256>` elements in an equipment register."""

    skip: bool = False
    """Whether to skip validating `<file>` and `<digitalReport>` elements containing a sha256 checksum."""

    roots: list[str] = field(default_factory=list)
    """Additional root paths to use during validation.

    These paths may be required when validating `<file>` or `<digitalReport>` elements that specify a relative path.
    """


@dataclass
class Config:
    """Configuration for the web application."""

    git: str = "git"
    """Path to the [git](https://git-scm.com/) executable."""

    host: str = "0.0.0.0"  # noqa: S104
    """The network interface to run the app on.

    Default is to listen on all network interfaces.
    """

    navbar: NavBar = field(default_factory=NavBar)
    """Navigation bar at the top of each webpage in the application."""

    nmi: str = "MSL"
    """Name of the National Metrology Institute."""

    pdflatex: str = "pdflatex"
    """Path to the `pdflatex` executable."""

    port: int = 17025
    """The port number to use for the app."""

    price: Price = field(default_factory=Price)
    """The format to use to display pricing information."""

    registers: list[EquipmentRegister] = field(default_factory=list)
    """A list of equipment registers to make available."""

    set_props_delay: float = 0.01
    """The number of seconds to wait after calling `dash.set_props` in a callback.

    If the value is too small, components might not update properly while the dash callback is running.
    """

    sha256_validation: dict[str, SHA256Validation] = field(default_factory=dict)
    """The key is the name of the Team that is responsible for the equipment register."""

    static: str = "static"
    """Path to the *static* directory.

    Store the favicon.ico and webapp.css files here.
    """

    theme: str = "BOOTSTRAP"
    """A theme name in https://bootswatch.com/."""

    verapdf: str = "verapdf.bat" if sys.platform == "win32" else "verapdf"
    """Path to the [veraPDF](https://verapdf.org/) executable."""

    wordapp: str = "Word.Application"
    """Name of the COM object for the [Microsoft Word Application](https://learn.microsoft.com/en-us/office/vba/api/word.application)."""

    def equipment_registers(self, *teams: str) -> list[EquipmentRegister]:
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
        self.wordapp = d.get("wordapp", self.wordapp)
        self.host = host or d.get("host", self.host)
        self.port = port or int(d.get("port", self.port))
        self.set_props_delay = float(d.get("set_props_delay", self.set_props_delay))
        self.static = Path(d.get("static", self.static)).expanduser().as_posix()
        self.git = Path(d.get("git", self.git)).expanduser().as_posix()
        self.pdflatex = Path(d.get("pdflatex", self.pdflatex)).expanduser().as_posix()
        self.verapdf = Path(d.get("verapdf", self.verapdf)).expanduser().as_posix()
        self.navbar = NavBar(**d.get("navbar", {}))
        self.price = Price(**d.get("price", {}))

        for k, v in d.get("sha256_validation", {}).items():
            self.sha256_validation[k] = SHA256Validation(**v)

        for reg in d.get("registers", []):
            directory = Path(reg).expanduser()
            files = find_xml_files(directory)
            self.registers.append(EquipmentRegister(team=Register(*files).team, directory=directory))

    @property
    def teams(self) -> list[str]:
        """Returns the list of `team` names."""
        return [t.team for t in self.registers]


cfg = Config()
