# cSpell: ignore documentclass usepackage pdfx
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from msl.equipment_webapp.config import EquipmentRegister, cfg

from .conftest import has_pdflatex, has_vera_pdf


class TestAPI:
    """Test the API."""

    client: TestClient  # pyright: ignore[reportUninitializedInstanceVariable]

    @classmethod
    def setup_class(cls) -> None:
        """Create the test client."""
        cfg.registers.clear()
        cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))
        cfg.registers.append(EquipmentRegister(team="Mass", directory=Path("tests/data/mass")))

        # require EquipmentRegister's to be added before creating the AllowedTeams enumeration in the api module
        # Also defined --ignore=packages/webapp/src/msl/equipment_webapp/pages for pytest in pyproject.toml
        from msl.equipment_webapp.pages import api  # noqa: PLC0415

        cls.client = TestClient(api.server)

    @classmethod
    def teardown_class(cls) -> None:
        """Close the test client."""
        cls.client.close()

    @pytest.mark.parametrize("endpoint", ["recalibrations", "search"])
    def test_invalid_team(self, endpoint: str) -> None:
        """Test for an invalid team."""
        response = self.client.get(f"/api/{endpoint}", params={"team": "Unknown"})
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Input should be 'Light' or 'Mass'"

    def test_search_invalid_text(self) -> None:
        """Test for an invalid search pattern."""
        response = self.client.get("/api/search", params={"team": "Light", "text": "*"})
        assert response.status_code == 400
        assert response.json()["detail"].startswith(("PatternError:", "error:"))

    def test_recalibrations(self) -> None:
        """Test recalibrations."""
        today = date.today().isoformat()  # noqa: DTZ011
        response = self.client.get("/api/recalibrations", params={"team": "Light"})
        assert response.status_code == 200
        value = response.json()
        assert value["synced"] is False
        assert value["is_valid"] == {"Light": True}
        assert value["header"] == [
            "ID",
            "Team",
            "Due Date",
            "Overdue?",
            "Description",
            "Manufacturer",
            "Model",
            "Serial",
        ]
        assert value["data"] == [
            ["MSLE.O.231", "Light", today, "Yes (uncalibrated)", "A digital multimeter", "MSL", "3458A", "0123456789"],
            ["MSLE.O.103", "Light", today, "Yes (uncalibrated)", "Single element photodiode", "MSL", "Single", "B02"],
            ["MSLE.O.061", "Light", today, "Yes (uncalibrated)", "Monochromator f=500mm", "MSL", "Mono", "123"],
            ["MSLE.O.023", "Light", today, "Yes (uncalibrated)", "Temperature probe", "MSL", "Model", "abc"],
        ]

    def test_search(self) -> None:
        """Test search."""
        response = self.client.get("/api/search", params={"team": "Light", "text": "B02"})
        assert response.status_code == 200
        value = response.json()
        assert value["synced"] is False
        assert value["is_valid"] == {"Light": True}
        assert value["header"] == ["ID", "Team", "Location", "Description", "Manufacturer", "Model", "Serial"]
        assert value["data"] == [
            ["MSLE.O.103", "Light", "Spectrophotometer", "Single element photodiode", "MSL", "Single", "B02"]
        ]

    @pytest.mark.anyio
    async def test_pdf_no_filename(self) -> None:
        """Test pdf."""
        from msl.equipment_webapp.pages import api  # noqa: PLC0415

        with pytest.raises(
            HTTPException, match=r" Must include the `source` filename in the Content-Disposition header"
        ):
            _ = await api.pdf(source=UploadFile(file=BytesIO(b"foo")))

        with pytest.raises(
            HTTPException, match=r" Must include the `attach` filename in the Content-Disposition header"
        ):
            _ = await api.pdf(
                source=UploadFile(file=BytesIO(b"foo"), filename="a.tex"), attach=[UploadFile(file=BytesIO(b"foo"))]
            )

    def test_pdf_invalid_source_extension(self) -> None:
        """Test pdf."""
        files = {"source": ("a.txt", b"hi", "text/plain")}
        response = self.client.post("/api/pdf", files=files)
        assert response.status_code == 415
        assert response.json() == {"detail": "Unsupported file extension. Must be one of .docx or .tex"}

    def test_pdf_pdflatex_not_found(self) -> None:
        """Test pdf."""
        pdflatex = cfg.pdflatex
        cfg.pdflatex = "does-not-exist"

        files = {"source": ("a.tex", b"hi", "text/plain"), "attach": ("a.txt", b"hi", "text/plain")}
        response = self.client.post("/api/pdf", files=files)

        cfg.pdflatex = pdflatex

        assert response.status_code == 400
        assert response.json() == {
            "detail": (
                "ERROR! `pdflatex` cannot be found. "
                "If it is installed, specify the path to the executable in the configuration file.\n"
                "```json\n"
                '  "pdflatex": "path/to/pdflatex"\n'
                "```"
            )
        }

    @pytest.mark.anyio
    @pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
    @pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
    async def test_pdf_convert_valid(self) -> None:
        """Test pdf."""
        content = b"\\documentclass{article}\n\\usepackage[a-3b]{pdfx}\n\\begin{document}\nHello\n\\end{document}"
        files = {"source": ("example.tex", content, "text/plain")}
        response = self.client.post("/api/pdf", files=files)
        assert response.status_code == 200
        assert response.headers["content-disposition"] == 'attachment; filename="example.pdf"'
        assert response.headers["content-length"] == "20726"
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["filename"] == "example.pdf"
        assert len(response.headers["md5-checksum"]) == 32
        assert response.content.startswith(b"%PDF-")

    def test_assets(self) -> None:
        """Test recalibrations."""
        response = self.client.get("/api/assets", params={"team": "Light"})
        assert response.status_code == 200
        value = response.json()
        assert value["synced"] is False
        assert value["is_valid"] == {"Light": True}
        assert value["header"] == [
            "ID",
            "Team",
            "Asset Number",
            "Depreciation Start Date",
            "Depreciation End Date",
            "Depreciated?",
            "Price",
            "Currency",
            "Manufacturer",
            "Model",
        ]
        assert value["data"] == []
