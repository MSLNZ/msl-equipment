# cSpell: ignore easybus
from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from msl.equipment import Connection, MSLConnectionError
from msl.equipment.resources import GMH3000

if TYPE_CHECKING:
    from tests.protocol_mock import SerialServer


def test_easybus() -> None:
    connection = Connection(
        address="ASRL/mock://",
        manufacturer="Greisinger",
        model="GMH3710-GE",
        timeout=1,
    )

    with connection.connect() as dev:
        assert isinstance(dev, GMH3000)

        server = cast("SerialServer", cast("object", dev.serial))

        server.add_response(b"\xfe\x05&q\x00H\xf7\x80\t")
        assert dev.value() == 21.76

        server.add_response(b"\xfe\x05&\x72\xff\x84\x00\xfc\x05")
        assert dev.value() == -0.04

        server.add_response(b"\xfe\xf5\xf8O\x00g\xbf0\xe3")  # min measurement range request
        server.add_response(b"\xfe\xf5\xf8N\x00r\x964\xec")  # max measurement range request
        assert dev.measurement_range() == (-200.0, 850.0)

        server.add_response(b"\xfe\r\x1ep\xf6\x91\xdf\xed\x0b")  # "No sensor" error code
        with pytest.raises(MSLConnectionError, match="No sensor"):
            _ = dev.value()
