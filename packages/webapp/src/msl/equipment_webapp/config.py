"""Configuration settings."""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from subprocess import run
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger("dash_logger")
logger.setLevel(logging.INFO)


@dataclass
class Team:
    """Information about a team."""

    team: str
    """The team that is responsible for the equipment register, e.g., `Light`, `Length`."""

    url: Path
    """Path to the directory containing equipment register XML files for the `team`."""

    def maybe_git_pull(self) -> None:
        """Maybe perform a `git pull` if the equipment-register directory is a cloned repository."""
        if not (self.url / ".git").exists():
            return

        logger.info("Performing `git pull` for %s", self.url)
        with contextlib.suppress(FileNotFoundError):
            _ = run(["git", "pull"], cwd=self.url, check=False, capture_output=True)  # noqa: S607

    def valid(self) -> bool:
        """Check if the equipment register is valid against the schema."""
        logger.info("Performing schema validation for %s", self.url)
        result = run(
            ["msl-equipment-validate", ".", "--skip-checksum", "--exit-first"],  # noqa: S607
            cwd=self.url,
            check=False,
            capture_output=True,
        )
        return result.returncode == 0


teams: list[Team] = []
