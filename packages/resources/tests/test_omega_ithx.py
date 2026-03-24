# cSpell: ignore SRTC SRTF SRDC SRDF
from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from conftest import TCPServer
    from msl.equipment.resources import ITHX


def test_temperature_humidity_dewpoint(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"\r") as server:
        connection = Connection(
            f"TCP::{server.host}::{server.port}",
            manufacturer="OMEGA",
            model="iTHX-W3",
            termination=b"\r",
            timeout=1,
        )

        dev: ITHX
        with connection.connect() as dev:
            server.add_requests_responses(
                {
                    b"*SRTC\r": b"19.3\r",
                    b"*SRTC2\r": b"25.1\r",
                    b"*SRTF\r": b"63.8\r",
                    b"*SRTF2\r": b"68.1\r",
                }
            )

            assert dev.temperature() == 19.3
            assert dev.temperature(probe=1) == 19.3
            assert dev.temperature(probe=2) == 25.1
            assert dev.temperature(probe=1, celsius=False) == 63.8
            assert dev.temperature(probe=2, celsius=False) == 68.1

            server.add_requests_responses(
                {
                    b"*SRH\r": b"42.5\r",
                    b"*SRH2\r": b"44.4\r",
                }
            )

            assert dev.humidity() == 42.5
            assert dev.humidity(probe=1) == 42.5
            assert dev.humidity(probe=2) == 44.4

            server.add_requests_responses(
                {
                    b"*SRDC\r": b"9.4\r",
                    b"*SRDF\r": b"38.1\r",
                    b"*SRDC2\r": b"11.0\r",
                    b"*SRDF2\r": b"37.8\r",
                }
            )

            assert dev.dewpoint() == 9.4
            assert dev.dewpoint(probe=1) == 9.4
            assert dev.dewpoint(probe=2) == 11.0
            assert dev.dewpoint(probe=1, celsius=False) == 38.1
            assert dev.dewpoint(probe=2, celsius=False) == 37.8
