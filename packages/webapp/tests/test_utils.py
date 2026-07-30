# cSpell: ignore documentclass embedfile
from __future__ import annotations

import base64
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import EquipmentRegister, cfg

try:
    has_vera_pdf = run([cfg.verapdf, "--version"], check=False, capture_output=True).returncode == 0  # noqa: S603
except FileNotFoundError:
    has_vera_pdf = False


try:
    has_pdflatex = run([cfg.pdflatex, "--version"], check=False, capture_output=True).returncode == 0  # noqa: S603
except FileNotFoundError:
    has_pdflatex = False


def test_is_register_valid() -> None:
    assert utils.is_register_valid(Path("tests/data/light/register.xml"))


@pytest.mark.anyio
async def test_process_events() -> None:
    out = await utils.process_events()  # type: ignore[func-returns-value]
    assert out is None


@pytest.mark.anyio
async def test_git_not_installed() -> None:
    git = cfg.git
    cfg.git = "missing"
    error = await utils.git_pull([EquipmentRegister("Light", Path())])
    cfg.git = git
    assert error.startswith("  \u21b3 ERROR! Cannot sync")


@pytest.mark.anyio
async def test_git_pull_not_git_dir(tmp_path: Path) -> None:
    registers = [EquipmentRegister("Light", tmp_path)]
    error = await utils.git_pull(registers)
    assert error == ""  # no error, directory is ignored


@pytest.mark.anyio
async def test_pdflatex_not_installed() -> None:
    pdflatex = cfg.pdflatex
    cfg.pdflatex = "missing"
    pdf_path, error = await utils.to_pdf(Path("not-used.tex"), {})
    cfg.pdflatex = pdflatex

    assert pdf_path == Path("not-used.pdf")
    assert error.startswith("ERROR! `pdflatex` cannot be found.")


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
async def test_pdflatex_fails() -> None:
    # don't use the `tmp_path` fixture from pytest, want to mimic exactly with is done in pages/pdf.py
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / "example.tex"
        _ = file.write_text(
            "\\documentclass{article}\n\\begin{document}\n\\embedfile[mimetype=text/plain]{data.text}\n\\end{document}"
        )
        _, error = await utils.to_pdf(file, {})
        assert error.rstrip().endswith("==> Fatal error occurred, no output PDF file produced!")


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
async def test_pdflatex_passes() -> None:
    # don't use the `tmp_path` fixture from pytest, want to mimic exactly with is done in pages/pdf.py
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / "file with spaces.tex"
        _ = file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        extra = {"data.txt": base64.b64encode(b"hi").decode()}
        assert not (Path(tmp) / "data.txt").exists()

        pdf, error = await utils.to_pdf(file, extra)

        assert error == ""
        assert (Path(tmp) / "data.txt").read_text() == "hi"
        assert pdf == Path(tmp) / "file with spaces.pdf"


@pytest.mark.anyio
async def test_vera_check_verapdf_not_installed() -> None:
    verapdf = cfg.verapdf
    cfg.verapdf = "missing"
    error = await utils.vera_check(Path("not-used"))
    cfg.verapdf = verapdf
    assert error.startswith("ERROR! `veraPDF` cannot be found.")


@pytest.mark.anyio
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_vera_check_fails() -> None:
    # file was download from https://github.com/veraPDF/veraPDF-corpus
    error = await utils.vera_check(Path("tests/data/veraPDF test suite 6-8-t02-fail-a.pdf"))
    assert error.startswith("ERROR! Invalid PDF file.\n```xml\n<?xml version=")


@pytest.mark.anyio
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_vera_check_passes() -> None:
    # file was download from https://github.com/veraPDF/veraPDF-corpus
    error = await utils.vera_check(Path("tests/data/veraPDF test suite 6-8-t02-pass-a.pdf"))
    assert error == ""
