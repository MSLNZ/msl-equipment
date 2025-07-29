from __future__ import annotations

from msl.equipment.dns_service_discovery import _DNSRecord
from msl.equipment.dns_service_discovery import find_lxi


def test_dns_record1():
    reply = (
        b"\x00\x00\x84\x00\x00\x06\x00\x06\x00\x00\x00\r\x07_vxi-11\x04_tcp\x05local\x00\x00"
        b"\x0c\x00\x01\x07_hislip\xc0\x14\x00\x0c\x00\x01\x05_http\xc0\x14\x00\x0c\x00\x01"
        b"\x04_lxi\xc0\x14\x00\x0c\x00\x01\t_scpi-raw\xc0\x14\x00\x0c\x00\x01\x0c_scpi-telnet"
        b"\xc0\x14\x00\x0c\x00\x01\xc02\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 0 Product Number - 0"
        b"\xc02\xc0>\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 0 Product Number - 1"
        b"\xc0>\xc0I\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 1 Product Number - 0"
        b"\xc0I\xc0Y\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 2 Product Number - 7"
        b"\xc0Y\xc0\x0c\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 9 Product Number - 9"
        b"\xc0\x0c\xc0$\x00\x0c\x00\x01\x00\x00\x00\n\x00$!Manufacturer 6 Product Number - 2"
        b"\xc0$\xc0x\x00!\x00\x01\x00\x00\x00\n\x00\x18\x00\x00\x00\x00\x00P\x0fX-123456-0000-0"
        b"\xc0\x19\xc0x\x00\x10\x00\x01\x00\x00\x00\n\x00\x11\ttxtvers=1\x06path=/\xc0\xa8\x00!\x00"
        b"\x01\x00\x00\x00\n\x00\x08\x00\x00\x00\x00\x00P\xc1\x9e\xc0\xa8\x00\x10\x00\x01\x00"
        b"\x00\x00\n\x00u\ttxtvers=1\x15Manufacturer=ABCD1234\x0cModel=123456\x17"
        b"SerialNumber=MY_SERIAL1/FirmwareVersion=A.00.01-02.03-04.05-06.07-08-09\xc0\xd8\x00!\x00"
        b"\x01\x00\x00\x00\n\x00\x08\x00\x00\x00\x00\x13\xa1\xc1\x9e\xc0\xd8\x00\x10\x00\x01\x00"
        b"\x00\x00\n\x00u\ttxtvers=1\x15Manufacturer=ABCDEFGH\x0cModel=987654\x17"
        b"SerialNumber=MY_SERIAL2/FirmwareVersion=B.10.11-12.13-14.15-16.17-18-19\xc1\x08\x00!\x00"
        b"\x01\x00\x00\x00\n\x00\x08\x00\x00\x00\x00\x13\xa0\xc1\x9e\xc1\x08\x00\x10\x00\x01\x00"
        b"\x00\x00\n\x00u\ttxtvers=1\x15Manufacturer=AAAAAAAA\x0cModel=BBBBBB\x17"
        b"SerialNumber=1234567890/FirmwareVersion=C.20.21-22.23-24.25-26.27-28-29\xc18\x00!\x00\x01"
        b"\x00\x00\x00\n\x00\x08\x00\x00\x00\x00\x00o\xc1\x9e\xc18\x00\x10\x00\x01\x00\x00\x00\n\x00"
        b"u\ttxtvers=1\x15Manufacturer=ZZZZzzzz\x0cModel=tuvwxy\x17SerialNumber=0123456789/"
        b"FirmwareVersion=D-33-33-33-33-33-33-33-33-33-00\xc1h\x00!\x00\x01\x00\x00\x00\n\x00\x08"
        b"\x00\x00\x00\x00\x13\x10\xc1\x9e\xc1h\x00\x10\x00\x01\x00\x00\x00\n\x00u\ttxtvers=1\x15"
        b"Manufacturer=00000000\x0cModel=000000\x17SerialNumber=0000000000/"
        b"FirmwareVersion=0000000000000000000000000000000\xc1\x9e\x00\x01\x00\x01\x00\x00\x00\n"
        b"\x00\x04\xa9\xfed\x0f"
    )

    dns = _DNSRecord(reply)
    assert dns.questions == [
        {"name": "_vxi-11._tcp.local.", "type": 12, "class": 1},
        {"name": "_hislip._tcp.local.", "type": 12, "class": 1},
        {"name": "_http._tcp.local.", "type": 12, "class": 1},
        {"name": "_lxi._tcp.local.", "type": 12, "class": 1},
        {"name": "_scpi-raw._tcp.local.", "type": 12, "class": 1},
        {"name": "_scpi-telnet._tcp.local.", "type": 12, "class": 1},
    ]
    assert dns.answers == [
        {
            "name": "_http._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 0 Product Number - 0._http._tcp.local.",
        },
        {
            "name": "_lxi._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 0 Product Number - 1._lxi._tcp.local.",
        },
        {
            "name": "_scpi-raw._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 1 Product Number - 0._scpi-raw._tcp.local.",
        },
        {
            "name": "_scpi-telnet._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 2 Product Number - 7._scpi-telnet._tcp.local.",
        },
        {
            "name": "_vxi-11._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 9 Product Number - 9._vxi-11._tcp.local.",
        },
        {
            "name": "_hislip._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 10,
            "data": "Manufacturer 6 Product Number - 2._hislip._tcp.local.",
        },
    ]
    assert len(dns.authority) == 0
    assert dns.additional == [
        {
            "name": "Manufacturer 0 Product Number - 0._http._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 80, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 0 Product Number - 0._http._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {"txtvers": "1", "path": "/"},
        },
        {
            "name": "Manufacturer 0 Product Number - 1._lxi._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 80, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 0 Product Number - 1._lxi._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {
                "txtvers": "1",
                "Manufacturer": "ABCD1234",
                "Model": "123456",
                "SerialNumber": "MY_SERIAL1",
                "FirmwareVersion": "A.00.01-02.03-04.05-06.07-08-09",
            },
        },
        {
            "name": "Manufacturer 1 Product Number - 0._scpi-raw._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 5025, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 1 Product Number - 0._scpi-raw._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {
                "txtvers": "1",
                "Manufacturer": "ABCDEFGH",
                "Model": "987654",
                "SerialNumber": "MY_SERIAL2",
                "FirmwareVersion": "B.10.11-12.13-14.15-16.17-18-19",
            },
        },
        {
            "name": "Manufacturer 2 Product Number - 7._scpi-telnet._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 5024, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 2 Product Number - 7._scpi-telnet._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {
                "txtvers": "1",
                "Manufacturer": "AAAAAAAA",
                "Model": "BBBBBB",
                "SerialNumber": "1234567890",
                "FirmwareVersion": "C.20.21-22.23-24.25-26.27-28-29",
            },
        },
        {
            "name": "Manufacturer 9 Product Number - 9._vxi-11._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 111, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 9 Product Number - 9._vxi-11._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {
                "txtvers": "1",
                "Manufacturer": "ZZZZzzzz",
                "Model": "tuvwxy",
                "SerialNumber": "0123456789",
                "FirmwareVersion": "D-33-33-33-33-33-33-33-33-33-00",
            },
        },
        {
            "name": "Manufacturer 6 Product Number - 2._hislip._tcp.local.",
            "type": 33,
            "class": 1,
            "ttl": 10,
            "data": {"priority": 0, "weight": 0, "port": 4880, "target": "X-123456-0000-0.local."},
        },
        {
            "name": "Manufacturer 6 Product Number - 2._hislip._tcp.local.",
            "type": 16,
            "class": 1,
            "ttl": 10,
            "data": {
                "txtvers": "1",
                "Manufacturer": "00000000",
                "Model": "000000",
                "SerialNumber": "0000000000",
                "FirmwareVersion": "0000000000000000000000000000000",
            },
        },
        {"name": "X-123456-0000-0.local.", "type": 1, "class": 1, "ttl": 10, "data": (169, 254, 100, 15)},
    ]


def test_dns_record2():
    reply = (
        b"\x00\x00\x84\x00\x00\x00\x00\x02\x00\x00\x00\x00\x05_http\x04_tcp\x05local"
        b"\x00\x00\x0c\x00\x01\x00\x00\x0e\x10\x001\x1eabcdefghijklmnopqrstuvwxyz-123"
        b"\x05_http\x04_tcp\x05local\x00\t_services\x07_dns-sd\x04_udp\x05local\x00"
        b"\x00\x0c\x00\x01\x00\x00\x0e\x10\x00\x12\x05_http\x04_tcp\x05local\x00"
    )

    dns = _DNSRecord(reply)
    assert len(dns.questions) == 0
    assert dns.answers == [
        {
            "name": "_http._tcp.local.",
            "type": 12,
            "class": 1,
            "ttl": 3600,
            "data": "abcdefghijklmnopqrstuvwxyz-123._http._tcp.local.",
        },
        {"name": "_services._dns-sd._udp.local.", "type": 12, "class": 1, "ttl": 3600, "data": "_http._tcp.local."},
    ]
    assert len(dns.authority) == 0
    assert len(dns.additional) == 0


def test_find_lxi():
    for ipv4, device in find_lxi().items():
        assert isinstance(ipv4, str)
        assert device["description"]
        assert device["webserver"]
        for address in device["addresses"]:
            assert address.startswith("TCPIP::")
            assert (
                address.endswith("::inst0::INSTR")
                or address.endswith("::inst0,1024::INSTR")
                or address.endswith("::SOCKET")
                or address.endswith("::hislip0::INSTR")
            )
