from __future__ import annotations

from msl.equipment.connection_sdk import ConnectionSDK


def test_parse_address():
    p = ConnectionSDK.parse_address

    for address in [
        "",
        "SDK",
        "sdk",
        "SDK:",
        "SDK::",
        "COM2",
        "ASRL7::INSTR",
        "ASRL/dev/ttyS1",
        "SOCKET::192.168.1.100::5000",
        "Prologix::192.168.1.110::1234::6",
    ]:
        assert p(address) is None

    assert p("SDK::whatever")["path"] == "whatever"
    assert p("SDK::file.dll")["path"] == "file.dll"
    assert p("SDK::/home/username/file.so")["path"] == "/home/username/file.so"
    assert p("SDK::C:\\a\\b\\c\\file.dll")["path"] == "C:\\a\\b\\c\\file.dll"
    assert p(r"SDK::C:\a\b\c\file.dll")["path"] == r"C:\a\b\c\file.dll"
    assert p("SDK::C:\\name with\\spaces -_ [v1.2]\\s d k.dll")["path"] == "C:\\name with\\spaces -_ [v1.2]\\s d k.dll"
