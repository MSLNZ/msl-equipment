"""Common utility functions."""

from __future__ import annotations

import logging
import re
import socket
import struct
import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.request import HTTPError, urlopen
from xml.etree.ElementTree import XML, ParseError

import numpy as np

if TYPE_CHECKING:
    from ._types import EnumType, MessageDataType, MessageFormat, NumpyArray1D, Sequence1D


logger = logging.getLogger(__package__)


def to_enum(obj: object, enum: type[EnumType], *, prefix: str | None = None, to_upper: bool = False) -> EnumType:
    """Convert an object into the specified [enum.Enum][] member.

    Args:
        obj: An object that can be converted to the specified `enum`.
            Can be a _value_ or a _member_ name of the specified `enum`.
        enum: The [enum.Enum][] subclass that `obj` should be converted to.
        prefix: If `obj` is a string, ensures that `prefix` is included at the beginning
            of `obj` before converting `obj` to the `enum`.
        to_upper: If `obj` is a string, then whether to change `obj` to upper case before
            converting `obj` to the `enum`.

    Returns:
        The `obj` converted to `enum`.

    Raises:
        ValueError: If `obj` is not in `enum`.
    """
    try:
        return enum(obj)
    except ValueError:
        pass

    # then `obj` must the Enum member name
    name = f"{obj}".replace(" ", "_")
    if prefix and not name.startswith(prefix):
        name = prefix + name
    if to_upper:
        name = name.upper()

    try:
        return enum[name]
    except KeyError:
        pass

    msg = f"Cannot create {enum} from {obj!r}"
    raise ValueError(msg)


def to_primitive(text: str | bytes) -> bool | float | str:
    """Convert text into a [bool][], [int][] or [float][].

    Args:
        text: The text to convert.

    Returns:
        The `text` as a Python primitive type: [bool][], [int][] or [float][].
            Returns the original `text` (decoded if `bytes`) if it cannot be
            converted to any of these types. The text `"0"` and `"1"` are
            converted to an integer not a boolean.
    """
    if isinstance(text, bytes):
        text = text.decode()

    for t in (int, float):  # order matters
        try:
            return t(text)
        except (ValueError, TypeError):  # noqa: PERF203
            pass

    upper = text.upper().strip()
    if upper == "TRUE":
        return True
    if upper == "FALSE":
        return False

    return text


def to_bytes(seq: Sequence1D, *, fmt: MessageFormat = None, dtype: MessageDataType = "<f") -> bytes:
    """Convert a sequence of numbers into bytes.

    Args:
        seq: A 1-dimensional sequence of numbers (not a multidimensional array).
        fmt: The format to use to convert the sequence.
        dtype: The data type to use to convert each element in `seq` to.

    Returns:
        The `seq` converted to bytes.
    """
    if fmt == "ascii":
        if not isinstance(dtype, str):
            msg = f"dtype must be of type str, got {type(dtype)}"
            raise TypeError(msg)

        format_spec = dtype.lstrip("@=<>!")
        return ",".join(format(item, format_spec) for item in seq).encode("ascii")

    array = seq.astype(dtype=dtype) if isinstance(seq, np.ndarray) else np.fromiter(seq, dtype=dtype, count=len(seq))

    if fmt == "ieee":
        nbytes = str(array.nbytes)
        len_nbytes = len(nbytes)
        if len_nbytes > 9:  # noqa: PLR2004
            # The IEEE-488.2 format allows for 1 digit to specify the number
            # of bytes in the array. This is extremely unlikely to occur in
            # practice since the instrument would require > 1GB of memory.
            msg = "length too big for IEEE-488.2 specification"
            raise OverflowError(msg)
        return f"#{len_nbytes}{nbytes}".encode() + array.tobytes()

    if fmt == "hp":
        byteorder = array.dtype.byteorder
        if byteorder == "|":
            # | means not applicable for the dtype specified, assign little endian
            # this redefinition is also declared in from_bytes()
            byteorder = "<"
        return b"#A" + struct.pack(byteorder + "H", array.nbytes) + array.tobytes()

    return array.tobytes()


def from_bytes(  # noqa: C901, PLR0912, PLR0915
    buffer: bytes | bytearray | str, fmt: MessageFormat = "ieee", dtype: MessageDataType = "<f"
) -> NumpyArray1D:
    """Convert bytes into an array.

    Args:
        buffer: A byte buffer. Can be an already-decoded buffer of type [str][], but only if `fmt` is `"ascii"`.
        fmt: The format that `buffer` is in.
        dtype: The data type of each element in `buffer`.

    Returns:
        The input buffer as a numpy array.
    """
    if fmt == "ascii":
        if isinstance(buffer, (bytes, bytearray)):
            buffer = buffer.decode("ascii")
        return np.fromstring(buffer, dtype=dtype, sep=",")

    if not isinstance(buffer, (bytes, bytearray)):
        msg = f"buffer must be of type bytes | bytearray, got {type(buffer)}"
        raise TypeError(msg)

    _dtype: np.dtype
    if fmt == "ieee":
        offset = buffer.find(b"#")
        if offset == -1:
            msg = "Invalid IEEE-488.2 format, cannot find # character"
            raise ValueError(msg)

        try:
            len_nbytes = int(buffer[offset + 1 : offset + 2])
        except ValueError:
            len_nbytes = None

        if len_nbytes is None:
            msg = "Invalid IEEE-488.2 format, character after # is not an integer"
            raise ValueError(msg)

        if len_nbytes == 0:
            # <INDEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>
            # Section 8.7.10, IEEE 488.2-1992
            nbytes = len(buffer) - offset

            # The standard states that the buffer must end in a NL (\n) character,
            # but it may have already been stripped from the buffer
            if buffer.endswith(b"\n"):
                nbytes -= 1
        else:
            # <DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>
            # Section 8.7.9, IEEE 488.2-1992
            try:
                nbytes = int(buffer[offset + 2 : offset + 2 + len_nbytes])
            except ValueError:
                nbytes = None

        if nbytes is None:
            msg = f"Invalid IEEE-488.2 format, characters after #{len_nbytes} are not integers"
            raise ValueError(msg)

        _dtype = np.dtype(dtype)
        offset += 2 + len_nbytes
        count = nbytes // _dtype.itemsize
        return np.frombuffer(buffer, dtype=_dtype, count=count, offset=offset)

    if fmt == "hp":
        offset = buffer.find(b"#A")
        if offset == -1:
            msg = "Invalid HP format, cannot find #A character"
            raise ValueError(msg)

        _dtype = np.dtype(dtype)
        i, j = offset + 2, offset + 4

        byteorder = _dtype.byteorder
        if byteorder == "|":
            # | means not applicable for the dtype specified, assign little endian
            # this redefinition is also declared in to_bytes()
            byteorder = "<"

        try:
            (nbytes,) = struct.unpack(byteorder + "H", buffer[i:j])
        except struct.error:
            nbytes = None

        if nbytes is None:
            msg = "Invalid HP format, characters after #A are not an unsigned short integer"
            raise ValueError(msg)

        count = nbytes // _dtype.itemsize
        return np.frombuffer(buffer, dtype=_dtype, count=count, offset=j)

    return np.frombuffer(buffer, dtype=dtype)


def ipv4_addresses() -> set[str]:
    """Get all IPv4 addresses on all network interfaces."""
    if sys.platform == "win32":
        interfaces = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        addresses = {str(ip[-1][0]) for ip in interfaces}
    elif sys.platform == "linux":
        out = subprocess.check_output(["hostname", "--all-ip-addresses"])  # pyright: ignore[reportUnreachable] # noqa: S607
        # --all-ip-addresses can return IPv6 addresses, which contain :
        addresses = {a for a in out.decode().split() if a[4] != ":"}
    else:
        ps = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)  # pyright: ignore[reportUnreachable]  # noqa: S607
        output = subprocess.check_output(("grep", "inet "), stdin=ps.stdout)
        _ = ps.wait()
        addresses = {line.split()[1] for line in output.decode().splitlines()}
    addresses.discard("127.0.0.1")
    return addresses


@dataclass
class LXIInterface:
    """Information about the interface for an LXI device.

    Args:
        type: For LXI devices, this value is `LXI`, but other vendors may use something different
            (e.g., VXI, PXI, GPIB, Serial, USB, ...).
        addresses: The VISA-like string addresses that are supported to communicate with the device.
        mac_address: The MAC address of the interface.
        hostname: The hostname of the interface.
    """

    type: str = ""
    addresses: tuple[str, ...] = ()
    mac_address: str = ""
    hostname: str = ""


@dataclass
class LXIDevice:
    """Information about an LXI device.

    Args:
        manufacturer: Device manufacturer.
        model: Manufacturer's model number.
        serial: Manufacturer's serial number.
        description: Either the manufacturer's product description, if the
            `lxi/identification/` endpoint exists, or the value of the `<title>`
            tag if the webserver is an HTML source file.
        firmware: Device firmware revision number.
        interfaces: Network interfaces.
    """

    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    description: str = ""
    firmware: str = ""
    interfaces: tuple[LXIInterface, ...] = ()


def parse_lxi_webserver(host: str, port: int = 80, timeout: float = 10) -> LXIDevice:
    """Get the information about an LXI device from the device's webserver.

    Args:
        host: The IP address or hostname of the LXI device.
        port: The port number of the device's web service.
        timeout: The maximum number of seconds to wait for a reply.

    Returns:
        The information about the LXI device.
    """
    http = "https" if port == 443 else "http"  # noqa: PLR2004
    port_str = "" if port in {80, 443} else f":{port}"
    base_url = f"{http}://{host}{port_str}"
    try:
        # Check for the XML document
        # LXI Device Specification 2022 (Revision 1.6), Section 10.2
        response = urlopen(f"{base_url}/lxi/identification", timeout=timeout)  # noqa: S310
    except HTTPError as e:
        if e.getcode() == 404:  # noqa: PLR2004
            # The URL for the XML document does not exist, parse the webserver's homepage
            with urlopen(base_url, timeout=timeout) as r:  # noqa: S310
                return _parse_lxi_html(r.read().decode("utf-8"))
        raise
    else:
        content = response.read().decode("utf-8")
        response.close()
        try:
            return _parse_lxi_xml(content)
        except ParseError:
            # Some LXI webserver's redirect all invalid URLs to the
            # webserver's homepage instead of raising an HTTPError
            return _parse_lxi_html(content)


def _parse_lxi_html(content: str) -> LXIDevice:
    """Parse an HTML document from an LXI-device webpage.

    The `<title>` tag is parsed and, if found, is included as the `description`
    of the `LXIDevice`

    Args:
        content: The content of an HTML document.
    """
    title = re.search(r"<title>(.+)</title>", content, flags=re.DOTALL)
    if title:
        return LXIDevice(description=title.group(1).strip())
    return LXIDevice()


def _parse_lxi_xml(content: str) -> LXIDevice:  # noqa: C901
    """Parse an XML document from an LXI-device webpage.

    Args:
        content: The string representation of an XML document.

    Returns:
        The information about the LXI device.
    """
    device = LXIDevice()
    root = XML(content)
    if not root.tag.endswith("LXIDevice"):
        return device

    # Using str.endswith() allows for ignoring the LXI namespace
    for e in root:
        if e.tag.endswith("Manufacturer"):
            device.manufacturer = e.text or ""
        elif e.tag.endswith("Model"):
            device.model = e.text or ""
        elif e.tag.endswith("SerialNumber"):
            device.serial = e.text or ""
        elif e.tag.endswith("ManufacturerDescription"):
            device.description = e.text or ""
        elif e.tag.endswith("FirmwareRevision"):
            device.firmware = e.text or ""
        elif e.tag.endswith("Interface"):
            interface = LXIInterface(type=e.get("InterfaceType", ""))
            for i in e:
                if i.tag.endswith("InstrumentAddressString") and i.text:
                    interface.addresses += (i.text,)
                elif i.tag.endswith("MACAddress") and i.text:
                    interface.mac_address = i.text
                elif i.tag.endswith("Hostname") and i.text:
                    interface.hostname = i.text
            device.interfaces += (interface,)

    return device
