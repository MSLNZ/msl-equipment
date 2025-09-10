"""Implementation of the Multicast DNS and DNS-Based Service Discovery protocols.

# References

* [RFC-1035] &mdash; *Domain Names - Implementation and Specification*, **ISI**, November 1987.
* [RFC-6762] &mdash; *Multicast DNS*, **Apple Inc.**, February 2013.
* [RFC-6763] &mdash; *DNS-Based Service Discovery*, **Apple Inc.**, February 2013.

[RFC-1035]: https://www.rfc-editor.org/rfc/rfc1035
[RFC-6762]: https://www.rfc-editor.org/rfc/rfc6762
[RFC-6763]: https://www.rfc-editor.org/rfc/rfc6763
"""

from __future__ import annotations

import select
import socket
import struct
import threading
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from .utils import ipv4_addresses, logger, parse_lxi_webserver

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from .utils import LXIDevice


# RFC 6762, Section 5.1
MDNS_ADDR = "224.0.0.251"
MDNS_ADDR6 = "ff02::fb"
MDNS_PORT = 5353

HTTP_PORT = 80
HISLIP_PORT = 4880
VXI11_PORT = 111


class _QType(IntEnum):
    """TYPE fields used in Resource Records."""

    UNHANDLED = 0

    # RFC 1035, Section 3.2.2
    A = 1  # a host address
    PTR = 12  # a domain name pointer
    TXT = 16  # text strings

    # RFC 2782, Page 2
    SRV = 33  # location of services

    # RFC 1035, Section 3.2.4
    IN = 1  # the internet

    # RFC 3596, IPv6 address
    IPv6 = 28

    @classmethod
    def _missing_(cls, value: object) -> _QType:  # noqa: ARG003  # pyright: ignore[reportImplicitOverride]
        return _QType.UNHANDLED


class _Buffer:
    def __init__(self, data: bytes) -> None:
        self.data: bytes = data
        self.offset: int = 0

    def get(self, length: int) -> bytes:
        start = self.offset
        self.offset += length
        return self.data[start : start + length]

    def unpack(self, fmt: str | bytes) -> tuple[Any, ...]:
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.get(size))

    def decode_name(self) -> list[str]:
        # RFC 1035, Section 4.1.2
        # a domain name represented as a sequence of labels, where
        # each label consists of a length octet followed by that
        # number of octets. The domain name terminates with the
        # zero length octet for the null label of the root.
        names: list[str] = []
        while True:
            (length,) = self.unpack("!B")
            if length == 0:
                names.append("")
                break

            if length & 0b11000000:
                # RFC 1035, Section 4.1.4 (Pointer)
                self.offset -= 1
                pointer = self.unpack("!H")[0] & 0b0011111111111111
                offset = self.offset
                self.offset = pointer
                names.extend(self.decode_name())
                self.offset = offset
                break

            names.append(self.get(length).decode())

        return names


@dataclass
class _Question:
    """RFC 1035, Section 4.1.2: Question section format."""

    q_name: str
    q_type: int
    q_class: int


@dataclass
class _DomainNamePointer:
    """RFC 1035, 3.2.2."""

    value: str


@dataclass
class _Service:
    """RFC 2782."""

    priority: int
    weight: int
    port: int
    target: str


@dataclass
class _Text:
    """RFC 1035, Section 3.3.14 and LXI Device Specification 2022 (Revision 1.6), Section 10.4.3."""

    mapping: dict[str, str]


@dataclass
class _HostAddress:
    """RFC 1035, Section 3.4.1."""

    address: tuple[int, int, int, int]


@dataclass
class _ResourceRecord:
    rr_name: str
    rr_type: _QType
    rr_class: int
    rr_ttl: int
    rr_data: _DomainNamePointer | _HostAddress | _Service | _Text | bytes | None


@dataclass
class _ServiceDiscoveryDevice:
    """A Device that support the mDNS and DNS Service Discovery protocols."""

    webserver: str
    description: str
    addresses: list[str]


class _DNSRecord(_Buffer):
    def __init__(self, reply: bytes) -> None:
        super().__init__(reply)

        # RFC 1035, Section 4.1.1
        tid, flags, qd_count, an_count, ns_count, ar_count = self.unpack("!6H")
        assert tid == 0  # get the same transaction identifier back  # noqa: S101
        assert flags & 0b1000010000000000  # QR=1, OPCODE=0, AA=1, TC=0, RD=0, RA=0, Z=0, RCODE=0  # noqa: S101

        self.questions: list[_Question] = [self.parse_question() for _ in range(qd_count)]
        self.answers: list[_ResourceRecord] = [self.parse_resource_record() for _ in range(an_count)]
        self.authority: list[_ResourceRecord] = [self.parse_resource_record() for _ in range(ns_count)]
        self.additional: list[_ResourceRecord] = [self.parse_resource_record() for _ in range(ar_count)]

    def parse_question(self) -> _Question:
        # RFC 1035, Section 4.1.2
        q_name = ".".join(self.decode_name())
        q_type, q_class = self.unpack("!2H")
        return _Question(q_name, q_type, q_class)

    def parse_resource_record(self) -> _ResourceRecord:
        # RFC 1035, Section 4.1.3
        rr_name = ".".join(self.decode_name())
        rr_type, rr_class, rr_ttl, rd_length = self.unpack("!2HIH")
        rr = _ResourceRecord(rr_name, _QType(rr_type), rr_class, rr_ttl, None)
        if rd_length == 0:
            return rr

        if rr_type == _QType.PTR:  # RFC 1035, Section 3.3.12
            rr.rr_data = _DomainNamePointer(".".join(self.decode_name()))
            return rr

        if rr_type == _QType.SRV:  # RFC 2782
            priority, weight, port = self.unpack("!3H")
            rr.rr_data = _Service(priority, weight, port, ".".join(self.decode_name()))
            return rr

        if rr_type == _QType.TXT:  # RFC 1035, Section 3.3.14
            txt_data: list[str] = []
            stop = self.offset + rd_length
            while self.offset < stop:
                (txt_length,) = self.unpack("!B")
                txt_data.append(self.get(txt_length).decode())

            # LXI Device Specification 2022 (Revision 1.6), Section 10.4.3
            rr.rr_data = _Text(dict(item.split("=") for item in txt_data))
            return rr

        if rr_type == _QType.A:  # RFC 1035, Section 3.4.1
            rr.rr_data = _HostAddress(self.unpack("!4B"))
            return rr

        rr.rr_data = self.get(rd_length)
        return rr


def find_lxi(*, ip: Sequence[str] | None = None, timeout: float = 1) -> dict[str, _ServiceDiscoveryDevice]:  # noqa: C901, PLR0915
    """Find all LXI devices that support the mDNS and DNS Service Discovery protocols.

    Args:
        ip: The IP address(es) on the local computer to use to broadcast the discovery message.
            If not specified, broadcast on all network interfaces.
        timeout: The maximum number of seconds to wait for a reply.

    Returns:
        The information about the HiSLIP, VXI-11 and SCPI-RAW devices that were found.
            Each _key_ is the IPv4 address of the LXI device.
    """
    all_ips = ipv4_addresses() if not ip else set(ip)
    logger.debug("find LXI devices: interfaces=%s, timeout=%s", all_ips, timeout)

    services = [
        # VXI-11 Discovery and Identification Extended Function (Revision 1.1), Section 10.1.5
        b"_vxi-11._tcp.local.",
        # LXI HiSLIP Extended Function (Revision 1.3), Section 20.7.1
        b"_hislip._tcp.local.",
        # LXI Device Specification 2022 (Revision 1.6), Section 10.4.3
        b"_http._tcp.local.",
        b"_lxi._tcp.local.",
        b"_scpi-raw._tcp.local.",
        b"_scpi-telnet._tcp.local.",
    ]

    # RFC 1035, Section 4
    id_ = 0  # transaction identifier
    flags = 0  # QR=0, OPCODE=0, AA=0, TC=0, RD=0, RA=0, Z=0, RCODE=0
    qd_count = len(services)  # the number of Questions
    an_count = 0  # No Resource Records in the Answer section
    ns_count = 0  # No Name Server Resource Records in the Authority Records section
    ar_count = 0  # No Resource Records in the Additional Records section
    header = struct.pack("!6H", id_, flags, qd_count, an_count, ns_count, ar_count)

    # Initialize the DNS message
    message = bytearray(header)

    # Add the Questions to the DNS message
    for service in services:
        for name in service.split(b"."):
            message.extend(struct.pack("!B", len(name)))
            message.extend(name)
        message.extend(struct.pack("!2H", _QType.PTR, _QType.IN))

    def parse_xml(ip_address: str, port: int = 80) -> LXIDevice | None:
        try:
            return parse_lxi_webserver(ip_address, port=port, timeout=timeout)
        except:  # noqa: E722
            return None

    def discover(host: str) -> None:  # noqa: C901, PLR0912, PLR0915
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        sock.bind((host, 0))
        _ = sock.sendto(message, (MDNS_ADDR, MDNS_PORT))
        select_timeout = min(timeout * 0.1, 0.1)
        t0 = time.time()
        while True:
            r, _, _ = select.select([sock], [], [], select_timeout)
            if time.time() - t0 > timeout:
                break
            if not r:
                continue

            reply, (ip_address, _) = sock.recvfrom(8192)
            try:
                record = _DNSRecord(reply)
            except Exception as e:  # noqa: BLE001
                logger.warning("%s: %s", e.__class__.__name__, e)
                continue

            device: dict[str, str] = {}
            addresses: set[str] = set()
            found_lxi_srv = False

            # Check SRV and TXT records
            for a in record.additional:
                if isinstance(a.rr_data, _Service):
                    port = a.rr_data.port
                    if a.rr_name.endswith("_scpi-raw._tcp.local."):
                        addresses.add(f"TCPIP::{ip_address}::{port}::SOCKET")
                    elif a.rr_name.endswith("_vxi-11._tcp.local."):
                        port_str = "" if port == VXI11_PORT else f",{port}"
                        addresses.add(f"TCPIP::{ip_address}::inst0{port_str}::INSTR")
                    elif a.rr_name.endswith("_hislip._tcp.local."):
                        port_str = "" if port == HISLIP_PORT else f",{port}"
                        addresses.add(f"TCPIP::{ip_address}::hislip0{port_str}::INSTR")
                    elif a.rr_name.endswith("_lxi._tcp.local."):
                        found_lxi_srv = True
                        port_str = "" if port == HTTP_PORT else f":{port}"
                        device["webserver"] = f"http://{ip_address}{port_str}"
                        parsed = parse_xml(ip_address, port=port)
                        if parsed is not None:
                            device["description"] = parsed.description
                            for interface in parsed.interfaces:
                                for address in interface.addresses:
                                    addresses.add(address)

            # Fetch the XML identification document (if it hasn't already been fetched)
            if not found_lxi_srv:
                for a in record.answers:
                    if a.rr_name in {"_lxi._tcp.local.", "_http._tcp.local."}:
                        parsed = parse_xml(ip_address)
                        if parsed is not None:
                            device["webserver"] = f"http://{ip_address}"
                            device["description"] = parsed.description
                            for interface in parsed.interfaces:
                                for address in interface.addresses:
                                    addresses.add(address)

            key = tuple(int(s) for s in ip_address.split("."))
            devices[key] = _ServiceDiscoveryDevice(
                webserver=device.get("webserver", ""),
                description=device.get("description", "Unknown LXI device"),
                addresses=sorted(addresses),
            )

        sock.close()

    devices: dict[tuple[int, ...], _ServiceDiscoveryDevice] = {}
    threads = [threading.Thread(target=discover, args=(ip,)) for ip in all_ips]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # sort by the IPv4 addresses, which are tuple[int, int, int, int]
    return {".".join(str(v) for v in k): devices[k] for k in sorted(devices)}
