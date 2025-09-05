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
    from collections.abc import Sequence
    from enum import Enum
    from typing import Any, Literal

    from numpy.typing import DTypeLike, NDArray


logger = logging.getLogger(__package__)


def to_enum(obj: object, enum: type[Enum], *, prefix: str | None = None, to_upper: bool = False) -> Enum:
    """Convert an object into the specified [enum.Enum][]{:target="_blank"} member.

    Args:
        obj: An object that can be converted to the specified `enum`.
            Can be a _value_ or a _member_ name of the specified `enum`.
        enum: The [enum.Enum][]{:target="_blank"} subclass that `obj` should be converted to.
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


def to_bytes(
    seq: Sequence[float] | np.ndarray, fmt: Literal[None, "ascii", "hp", "ieee"] = "ieee", dtype: DTypeLike = "<f"
) -> bytes:
    """Convert a sequence of numbers into bytes.

    Args:
        seq: A 1-dimensional sequence of numbers (not a multidimensional array).
        fmt: The format to use to convert the sequence. Possible values are:

            * `None` &mdash; convert `seq` to bytes without a header.

              !!! example
                 `<byte><byte><byte>...`

            * `ascii` &mdash; comma-separated ASCII characters, see the
                  `<PROGRAM DATA SEPARATOR>` standard that is defined in Section 7.4.2.2 of
                  [IEEE 488.2-1992](https://standards.ieee.org/ieee/488.2/718/){:target="_blank"}.

               !!! example
                   `<string>,<string>,<string>,...`

            * `ieee` &mdash; arbitrary block data for `SCPI` messages, see the
                  `<DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>` standard that is defined in
                  Section 8.7.9 of [IEEE 488.2-1992](https://standards.ieee.org/ieee/488.2/718/){:target="_blank"}.

               !!! example
                   `#<length of num bytes value><num bytes><byte><byte><byte>...`

            * `hp` &mdash; the HP-IB data transfer standard, i.e., the `FORM#` command
                  option. See the programming guide for an
                  [HP 8530A](https://www.keysight.com/us/en/product/8530A/microwave-receiver.html#resources){:target="_blank"}
                  for more details.

               !!! example
                   `#A<num bytes as uint16><byte><byte><byte>...`

        dtype: The data type to use to convert each element in `seq` to. If `fmt` is
            `ascii` then `dtype` must be of type [str][] and it is used as the `format_spec`
            argument in [format][] to first convert each element in `seq` to a string,
            and then it is encoded (e.g., ``'.2e'`` converts each element to scientific
            notation with two digits after the decimal point). If `dtype` includes a
            byte-order character, it is ignored. For all other values of `fmt`, the
            `dtype` can be any object that [numpy.dtype][] supports (e.g., `'H'`,
            `'uint16'` and [numpy.ushort][] are equivalent values to convert each element
            to an `unsigned short`). If a byte-order character is specified then it
            is used, otherwise the native byte order of the CPU architecture is used.
            See [struct-format-strings][] for more details.

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
    buffer: bytes | bytearray | str, fmt: Literal[None, "ascii", "hp", "ieee"] = "ieee", dtype: DTypeLike = "<f"
) -> NDArray[Any]:
    """Convert bytes into an array.

    Args:
        buffer: A byte buffer. Can be an already-decoded buffer of type [str][], but only if
            `fmt` is `"ascii"`.
        fmt: The format that `buffer` is in. See [to_bytes][msl.equipment.utils.to_bytes] for more details.
        dtype: The data type of each element in `buffer`. Can be any object that [numpy.dtype][] supports.
        See [to_bytes][msl.equipment.utils.to_bytes] for more details.

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

        dtype = np.dtype(dtype)
        offset += 2 + len_nbytes
        count = nbytes // dtype.itemsize
        return np.frombuffer(buffer, dtype=dtype, count=count, offset=offset)

    if fmt == "hp":
        offset = buffer.find(b"#A")
        if offset == -1:
            msg = "Invalid HP format, cannot find #A character"
            raise ValueError(msg)

        dtype = np.dtype(dtype)
        i, j = offset + 2, offset + 4

        byteorder = dtype.byteorder
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

        count = nbytes // dtype.itemsize
        return np.frombuffer(buffer, dtype=dtype, count=count, offset=j)

    return np.frombuffer(buffer, dtype=dtype)


def ipv4_addresses() -> set[str]:
    """Get all IPv4 addresses on all network interfaces."""
    if sys.platform == "win32":
        interfaces = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        addresses = {str(ip[-1][0]) for ip in interfaces}
    elif sys.platform == "linux":
        out = subprocess.check_output(["hostname", "--all-ip-addresses"])  # noqa: S607
        addresses = set(out.decode().split())
    else:
        ps = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)  # noqa: S607
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
    """

    type: str = ""
    addresses: tuple[str, ...] = ()
    mac_address: str = ""


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
            device.interfaces += (interface,)

    return device
