"""Base class for GPIB communication."""

from __future__ import annotations

import contextlib
import os
import re
import sys
from bisect import bisect_right
from ctypes import POINTER, byref, c_char_p, c_int, c_long, c_short, c_wchar_p, create_string_buffer
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from msl.equipment.utils import logger
from msl.loadlib import LoadLibrary

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from ctypes import _NamedFuncPointer, _Pointer  # pyright: ignore[reportPrivateUsage]
    from typing import Any, Callable, Never

    from msl.equipment.schema import Equipment

    ArgType = type[c_int | c_char_p | c_long | c_wchar_p | _Pointer[c_int | c_short | c_char_p]]


IS_WINDOWS: bool = sys.platform == "win32"
IS_LINUX: bool = sys.platform == "linux"
IS_DARWIN: bool = sys.platform == "darwin"

REGEX = re.compile(r"GPIB(?P<board>\d{0,2})(::((?P<pad>\d+)|(?P<name>[^\s:]+)))?(::(?P<sad>\d+))?", flags=re.IGNORECASE)

# NI VI_GPIB
REN_DEASSERT = 0
REN_ASSERT = 1
REN_DEASSERT_GTL = 2
REN_ASSERT_ADDRESS = 3
REN_ASSERT_LLO = 4
REN_ASSERT_ADDRESS_LLO = 5
REN_ADDRESS_GTL = 6
ATN_DEASSERT = 0
ATN_ASSERT = 1
ATN_DEASSERT_HANDSHAKE = 2
ATN_ASSERT_IMMEDIATE = 3

# IBERR error codes
# linux-gpib-user/include/gpib/gpib_user.h
EDVR = 0
ECIC = 1
ENOL = 2
EADR = 3
EARG = 4
ESAC = 5
EABO = 6
ENEB = 7
EDMA = 8
EOIP = 10
ECAP = 11
EFSO = 12
EBUS = 14
ESTB = 15
ESRQ = 16
ETAB = 20

# defined in ni4882.h
ELCK = 21
EARM = 22
EHDL = 23
EWIP = 26
ERST = 27
EPWR = 28

NO_SEC_ADDR = 0xFFFF
TIMO = 0x4000
ERR = 0x8000

_ERRORS = {
    # linux-gpib-user/language/python/gpibinter.c
    EDVR: "A system call has failed; ibcnt/ibcntl will be set to the value of errno",
    ECIC: "Your interface board needs to be controller-in-charge, but is not",
    ENOL: "You have attempted to write data or command bytes, but there are no listeners currently addressed",
    EADR: "The interface board has failed to address itself properly before starting an io operation",
    EARG: "One or more arguments to the function call were invalid",
    ESAC: "The interface board needs to be system controller, but is not",
    EABO: "A read or write of data bytes has been aborted, possibly due to a timeout or reception of a device clear command",  # noqa: E501
    ENEB: "The GPIB interface board does not exist, its driver is not loaded, or it is in use by another process",
    EDMA: "Not used (DMA error), included for compatibility purposes",
    EOIP: "Function call can not proceed due to an asynchronous IO operation (ibrda(), ibwrta(), or ibcmda()) in progress",  # noqa: E501
    ECAP: "Incapable of executing function call, due the GPIB board lacking the capability, or the capability being disabled in software",  # noqa: E501
    EFSO: "File system error. ibcnt/ibcntl will be set to the value of errno",
    EBUS: "An attempt to write command bytes to the bus has timed out",
    ESTB: "One or more serial poll status bytes have been lost. This can occur due to too many status bytes accumulating (through automatic serial polling) without being read",  # noqa: E501
    ESRQ: "The serial poll request service line is stuck on",
    ETAB: "This error can be returned by ibevent(), FindLstn(), or FindRQS() (see their descriptions for more information)",  # noqa: E501
    # ni4882.h
    ELCK: "Address or board is locked",
    EARM: "The ibnotify Callback failed to rearm",
    EHDL: "The input handle is invalid for this operation",
    EWIP: "Wait already in progress on input handle",
    ERST: "The event notification was cancelled due to a reset of the interface",
    EPWR: "The system or board has lost power or gone to standby",
    # https://documentation.help/NI-488.2/trou4xyt.html
    -535560148: "The board number is within the range of allowed board numbers, but it has not been assigned to a GPIB interface",  # noqa: E501
    -535560155: "The board number is not within the range of allowed board numbers",
    -535560139: "The device name is not listed in the logical device templates that are part of Measurement & Automation Explorer",  # noqa: E501
    -519569280: "You are using a removable interface (for example, a GPIB-USB-HS) and you removed or ejected the interface while the software is trying to communicate with it",  # noqa: E501
    -519569279: "You are using a removable interface (for example, a GPIB-USB-HS) and you removed or ejected the interface while the software is trying to communicate with it",  # noqa: E501
    -536215481: "The driver encountered an access violation when attempting to access an object supplied by the user",
    -519897021: "You have enabled DOS NI-488.2 support and attempted to run an existing DOS NI-488.2 application that was compiled with an older, unsupported DOS application interface",  # noqa: E501
    -519700363: "The driver is unable to communicate with a GPIB-ENET/100 during an ibfind or ibdev call",
    -519700360: "You are using a GPIB-ENET/100 and the network link is broken between the host and the GPIB-ENET/100 interface",  # noqa: E501
}

# linux-gpib-user/include/gpib/gpib_user.h
_TIMEOUTS = (
    0,
    10e-6,
    30e-6,
    100e-6,
    300e-6,
    1e-3,
    3e-3,
    10e-3,
    30e-3,
    100e-3,
    300e-3,
    1.0,
    3.0,
    10.0,
    30.0,
    100.0,
    300.0,
    1000.0,
)


def _load_library(errcheck: Callable[[int, _NamedFuncPointer, tuple[int, ...]], int]) -> None:  # noqa: C901, PLR0912, PLR0915
    """Load a GPIB library.

    Args:
        errcheck: A callable function assigned to ctypes._FuncPtr.errcheck for each function in
            the GPIB library that returns the ibsta status value.
    """
    if GPIB.gpib_library is not None:
        return

    _library: LoadLibrary | None = None
    env_lib = os.getenv("GPIB_LIBRARY")
    libtype = "windll" if IS_WINDOWS else "cdll"
    if env_lib:
        _library = LoadLibrary(env_lib, libtype=libtype)  # type: ignore[arg-type]
    else:
        files: list[str] = []
        if IS_WINDOWS:
            files.extend(["ni4882.dll", "gpib-32.dll"])
        elif IS_LINUX:
            files.extend(
                [
                    "gpib",  # use ctypes.util.find_library in LoadLibrary
                    "libgpib.so.0",
                    "/usr/local/lib/libgpib.so.0",
                    "gpib-32.so",
                ]
            )
        elif IS_DARWIN:
            files.extend(
                [
                    "/Library/Frameworks/NI4882.framework/NI4882",
                    "macosx_gpib_lib_1.0.3a.dylib",
                ]
            )
        else:
            msg = f"GPIB is not yet implemented on platform {sys.platform!r}"
            raise OSError(msg)

        for file in files:
            try:
                _library = LoadLibrary(file, libtype=libtype)  # type: ignore[arg-type]
                break
            except OSError:
                pass

        if _library is None:
            msg = (
                f"Cannot load a GPIB library: {', '.join(files)}\n"
                f"If you have a GPIB library available, create a GPIB_LIBRARY environment variable "
                f"with the value equal to the path to the GPIB library file."
            )
            raise OSError(msg)

    GPIB.gpib_library = _library
    lib = _library.lib

    definitions: list[tuple[str, bool, type[c_int] | None, tuple[ArgType, ...]]] = [
        ("ibask", True, c_int, (c_int, c_int, POINTER(c_int))),
        ("ibcac", True, c_int, (c_int, c_int)),
        ("ibclr", True, c_int, (c_int,)),
        ("ibcmd", True, c_int, (c_int, c_char_p, c_long)),
        ("ibconfig", True, c_int, (c_int, c_int, c_int)),
        ("ibdev", False, c_int, (c_int, c_int, c_int, c_int, c_int, c_int)),
        ("ibgts", True, c_int, (c_int, c_int)),
        ("iblines", True, c_int, (c_int, POINTER(c_short))),
        ("ibln", True, c_int, (c_int, c_int, c_int, POINTER(c_short))),
        ("ibloc", True, c_int, (c_int,)),
        ("ibonl", True, c_int, (c_int, c_int)),
        ("ibpct", True, c_int, (c_int,)),
        ("ibrd", True, c_int, (c_int, c_char_p, c_long)),
        ("ibrsp", True, c_int, (c_int, c_char_p)),
        ("ibsic", True, c_int, (c_int,)),
        ("ibspb", True, c_int, (c_int, POINTER(c_short))),
        ("ibtrg", True, c_int, (c_int,)),
        ("ibwait", True, c_int, (c_int, c_int)),
        ("ibwrt", True, c_int, (c_int, c_char_p, c_long)),
        ("ibwrta", True, c_int, (c_int, c_char_p, c_long)),
        ("ThreadIbsta", False, c_int, ()),
        ("ThreadIberr", False, c_int, ()),
    ]

    if IS_WINDOWS:
        definitions.extend(
            [
                ("ibfindW", False, c_int, (c_wchar_p,)),
            ]
        )
    else:
        definitions.extend(
            [
                ("ibfind", False, c_int, (c_char_p,)),
                ("ibvers", False, None, (POINTER(c_char_p),)),
            ]
        )

    for fcn, err_check, restype, argtypes in definitions:
        try:
            function = getattr(lib, fcn)
        except AttributeError:

            def not_implement(*_: int, f: str = fcn) -> Never:
                msg = f"{f!r} is not implement on {sys.platform!r}"
                raise RuntimeError(msg)

            setattr(lib, fcn, partial(not_implement, f=fcn))
            continue

        function.argtypes = argtypes
        function.restype = restype
        if err_check:
            function.errcheck = errcheck

    try:
        lib.ThreadIbcntl.restype = c_long
        lib.ibcntl = lib.ThreadIbcntl
    except AttributeError:
        lib.ThreadIbcnt.restype = c_long
        lib.ibcntl = lib.ThreadIbcnt


def find_listeners(*, include_sad: bool = False) -> list[str]:  # noqa: C901
    """Find GPIB listeners.

    Args:
        include_sad: Whether to scan all secondary GPIB addresses.

    Returns:
        The GPIB addresses that were found.
    """
    logger.debug("Searching for GPIB devices (include_sad=%s)", include_sad)
    devices: list[str] = []

    def error_check(result: int, *_: object) -> int:
        return result

    try:
        _load_library(error_check)
    except (OSError, AttributeError) as e:
        logger.debug(str(e).splitlines()[0])
        return devices

    assert GPIB.gpib_library is not None  # noqa: S101
    lib = GPIB.gpib_library.lib
    asked = c_int()
    exists = c_short()
    for board in range(16):
        if lib.ibask(board, 0x1, byref(asked)) & ERR:  # IbaPAD = 0x1
            continue

        # the board must be controller-in-charge for ibln to succeed
        handle = lib.ibdev(board, asked.value, 0, 8, 1, 0)  # T30ms = 8
        if handle < 0 or lib.ibpct(handle) & ERR:
            continue

        for pad in range(31):
            if pad == asked.value:
                continue

            if lib.ibln(board, pad, 0, byref(exists)) & ERR:
                continue

            if exists.value:
                devices.append(f"GPIB{board}::{pad}::INSTR")

            if include_sad:
                for sad in range(96, 127):
                    if lib.ibln(board, pad, sad, byref(exists)) & ERR:
                        continue
                    if exists.value:
                        devices.append(f"GPIB{board}::{pad}::{sad}::INSTR")

        # close handle
        lib.ibonl(handle, 0)

    return devices


def _convert_timeout(value: float | None) -> int:
    # convert a floating-point timeout value into a timeout enum value
    if not value or value < 0:
        return 0  # infinite timeout (disabled)

    try:
        return _TIMEOUTS.index(value)
    except ValueError:
        return min(bisect_right(_TIMEOUTS, value), len(_TIMEOUTS) - 1)


class GPIB(MessageBased, regex=REGEX):
    """Base class for GPIB communication."""

    gpib_library: LoadLibrary | None = None

    def __init__(self, equipment: Equipment) -> None:
        """Base class for GPIB communication.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the GPIB communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Attributes: Connection Properties:
            eos_mode (int): Specifies the end-of-string character and mode
                (see [eos](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibeos.html) for details).
                _Default: `0`_
            send_eoi (bool): Whether to enable (`True`) or disable (`False`) the assertion of the EOI signal.
                _Default: `True`_
        """
        self._own: bool = True
        self._handle: int = -1
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        info = parse_gpib_address(equipment.connection.address)
        if not info:
            msg = f"Invalid GPIB address {equipment.connection.address!r}"
            raise ValueError(msg)

        props = equipment.connection.properties
        _ = props.setdefault("read_termination", None)

        _load_library(self._error_check)
        assert GPIB.gpib_library is not None  # noqa: S101
        self._lib: Any = GPIB.gpib_library.lib

        if info.name:
            # a board or device object from a name in a gpib.conf file
            self._handle = self._get_ibfind_handle(info.name)
        elif info.pad is None:
            # a board object with the given board number
            self._handle = info.board
            self._own = False
        else:
            # a device object
            send_eoi = int(props.get("send_eoi", 1))
            eos_mode = int(props.get("eos_mode", 0))
            sad = 0 if info.sad is None else info.sad
            if sad != 0 and sad < 0x60:  # noqa: PLR2004
                sad += 0x60
            info.sad = sad
            timeout = _convert_timeout(props.get("timeout", None))
            self._handle = self._get_ibdev_handle(info.board, info.pad, sad, timeout, send_eoi, eos_mode)

        # keep this reference assignment after the if/else condition since the
        # value of the secondary address may have been updated
        self._address_info: ParsedGPIBAddress = info

        # check if the handle corresponds to a system controller (INTFC)
        self._is_board: bool
        try:
            self._is_board = bool(self.ask(0xA))  # IbaSC = 0xa
        except MSLConnectionError:
            # asking IbaSC for a GPIB device raises EHDL error
            self._is_board = False

        if not self._is_board:
            self._set_interface_timeout()

    def _get_ibdev_handle(self, *args: int) -> int:
        # board_index, pad, sad, timeout, send_eoi, eos_mode
        handle: int = self._lib.ibdev(*args)
        logger.debug("gpib.ibdev%s -> %d", args, handle)
        if handle < 0:
            msg = f"Cannot acquire a handle for the GPIB device using {args}"
            raise MSLConnectionError(self, message=msg)
        return handle

    def _get_ibfind_handle(self, name: str) -> int:
        handle: int = self._lib.ibfindW(name) if IS_WINDOWS else self._lib.ibfind(name.encode("ascii"))
        logger.debug("gpib.ibfind(%r) -> %d", name, handle)
        if handle < 0:
            msg = f"Cannot acquire a handle for the GPIB board/device with name {name!r}"
            raise MSLConnectionError(self, message=msg)
        return handle

    def _error_check(self, result: int, func: _NamedFuncPointer, arguments: tuple[int, ...]) -> int:
        logger.debug("gpib.%s%s -> 0x%x", func.__name__, arguments, result)
        if result & TIMO:
            msg = (
                "If you are confident that the GPIB device received a\n"
                "valid message, you may want to check the manual to "
                "determine if the device sets the EOI line\nat the end "
                "of a message transfer. If EOI is not set, you may "
                "need to specify a value for the\nread_termination "
                "character."
            )
            raise MSLTimeoutError(self, msg)

        if result & ERR:
            # mimic _SetGpibError in linux-gpib-user/language/python/gpibinter.c
            iberr = self._lib.ThreadIberr()
            if iberr in {EDVR, EFSO}:
                iberr = self._lib.ibcntl()
                if IS_LINUX:
                    try:
                        message = os.strerror(iberr)
                    except (OverflowError, ValueError):
                        message = "Invalid os.strerror code"
                else:
                    message = _ERRORS.get(iberr, "Unknown error")
            else:
                message = _ERRORS.get(iberr, "Unknown error")

            msg = f"{message} [{func.__name__}, ibsta:{hex(result)}, iberr:{hex(iberr)}]"
            raise MSLConnectionError(self, msg)

        return result

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if not hasattr(self, "_is_board"):
            return

        if self._is_board:
            msg = "Cannot set a timeout value for a GPIB board"
            raise MSLConnectionError(self, message=msg)

        # set the timeout to one of the discrete values (IbcTMO = 0x3)
        _ = self.config(0x3, _convert_timeout(self._timeout))

        # read back the actual timeout (IbaTMO = 0x3)
        index = self.ask(0x3)
        self._timeout: float | None = None if index == 0 else _TIMEOUTS[index]

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        chunk_size = 20480  # 20kB = 20 * 1024
        data = create_string_buffer(chunk_size)
        buffer = bytearray()
        while True:
            sta: int = self._lib.ibrd(self._handle, data, chunk_size)
            buffer.extend(data[: self.count()])  # type: ignore[arg-type]
            if len(buffer) > self._max_read_size:
                msg = f"Maximum read size exceeded: {len(buffer)} > {self._max_read_size}\nbuffer: {buffer}"
                raise MSLConnectionError(self, message=msg)
            if sta & 0x2000:  # END
                break

        # always read until END so that the next _read() is correct,
        # but if size is specified, return the requested size
        if size is not None:
            return bytes(buffer[:size])
        return bytes(buffer)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        self._lib.ibwrt(self._handle, message, len(message))
        return self.count()

    def ask(self, option: int, *, handle: int | None = None) -> int:
        """Get a configuration setting (board or device).

        This method is the [ibask](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibask.html)
        function, it should not be confused with the [query][msl.equipment.interfaces.message_based.MessageBased.query]
        method.

        Args:
            option: A configuration setting to get the value of.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The value of the configuration setting.
        """
        if handle is None:
            handle = self._handle
        setting = c_int()
        self._lib.ibask(handle, option, byref(setting))
        return setting.value

    @property
    def board(self) -> int:
        """Returns the board descriptor."""
        return self._address_info.board

    def clear(self, *, handle: int | None = None) -> int:
        """Send the clear command (device).

        This method is the [ibclr](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibclr.html) function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibclr(handle)
        return ibsta

    def command(self, data: bytes, *, handle: int | None = None) -> int:
        """Write command bytes (board).

        This method is the [ibcmd](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibcmd.html) function.

        Args:
            data: The [commands](https://linux-gpib.sourceforge.io/doc_html/gpib-protocol.html#REFERENCE-COMMAND-BYTES)
                to write to the bus.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibcmd(handle, data, len(data))
        return ibsta

    def config(self, option: int, value: int, *, handle: int | None = None) -> int:
        """Change configuration settings (board or device).

        This method is the [ibconfig](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibconfig.html)
        function.

        Args:
            option: A configuration setting to change the value of.
            value: The new configuration setting value.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibconfig(handle, option, value)
        return ibsta

    def control_atn(self, state: int, *, handle: int | None = None) -> int:
        """Set the state of the ATN line (board).

        This method mimics the PyVISA-py implementation.

        Args:
            state: The state of the ATN line or the active controller. Allowed values are:

                * 0: ATN_DEASSERT
                * 1: ATN_ASSERT
                * 2: ATN_DEASSERT_HANDSHAKE
                * 3: ATN_ASSERT_IMMEDIATE

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        ibsta: int
        if handle is None:
            handle = self._handle
        if state == ATN_DEASSERT:
            ibsta = self._lib.ibgts(handle, 0)
            return ibsta
        if state == ATN_ASSERT:
            ibsta = self._lib.ibcac(handle, 0)
            return ibsta
        if state == ATN_DEASSERT_HANDSHAKE:
            ibsta = self._lib.ibgts(handle, 1)
            return ibsta
        if state == ATN_ASSERT_IMMEDIATE:
            ibsta = self._lib.ibcac(handle, 1)
            return ibsta

        msg = f"Invalid ATN {state=}"
        raise MSLConnectionError(self, message=msg)

    def control_ren(self, state: int, *, handle: int | None = None) -> int:
        """Controls the state of the GPIB Remote Enable (REN) interface line.

        Optionally the remote/local state of the device is also controlled.

        This method mimics the PyVISA-py implementation.

        Args:
            state: Specifies the state of the REN line and optionally the device remote/local state.
                Allowed values are:

                * 0: REN_DEASSERT
                * 1: REN_ASSERT
                * 2: REN_DEASSERT_GTL
                * 3: REN_ASSERT_ADDRESS
                * 4: REN_ASSERT_LLO
                * 5: REN_ASSERT_ADDRESS_LLO
                * 6: REN_ADDRESS_GTL

            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle

        ibsta = 0
        if self._is_board and state not in (REN_ASSERT, REN_DEASSERT, REN_ASSERT_LLO):
            msg = f"Invalid REN {state=} for INTFC"
            raise MSLConnectionError(self, message=msg)

        if state == REN_DEASSERT_GTL:
            ibsta = self.command(b"\x01", handle=handle)  # GTL = 0x1

        if state in (REN_DEASSERT, REN_DEASSERT_GTL):
            ibsta = self.remote_enable(state=False, handle=handle)

        if state == REN_ASSERT_LLO:
            ibsta = self.command(b"\x11", handle=handle)  # LLO = 0x11
        elif state == REN_ADDRESS_GTL:
            ibsta = self.command(b"\x01", handle=handle)  # GTL = 0x1
        elif state == REN_ASSERT_ADDRESS_LLO:
            pass
        elif state in (REN_ASSERT, REN_ASSERT_ADDRESS):
            ibsta = self.remote_enable(state=True, handle=handle)
            if not self._is_board and state == REN_ASSERT_ADDRESS:
                assert self._address_info.pad is not None  # noqa: S101
                ibsta = int(self.listener(self._address_info.pad, sad=self._address_info.sad or 0, handle=handle))

        return ibsta

    def count(self) -> int:
        """Get the number of bytes sent or received.

        This method is the [ibcntl](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibcnt.html) function.
        """
        return int(self._lib.ibcntl())

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the GPIB connection."""
        if self._own and self._handle > 0:
            with contextlib.suppress(MSLConnectionError):
                _ = self.online(state=False, handle=self._handle)
            self._handle = -1
            super().disconnect()

    @property
    def handle(self) -> int:
        """Returns the handle of the instantiated board or device."""
        return self._handle

    def interface_clear(self, *, handle: int | None = None) -> int:
        """Perform interface clear (board).

        Resets the GPIB bus by asserting the *interface clear* (IFC) bus line for a duration of at
        least 100 microseconds.

        This method is the [ibsic](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibsic.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibsic(handle)
        return ibsta

    def lines(self, *, handle: int | None = None) -> int:
        """Returns the status of the control and handshaking bus lines (board).

        This method is the [iblines](https://linux-gpib.sourceforge.io/doc_html/reference-function-iblines.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.
        """
        if handle is None:
            handle = self._handle
        status = c_short()
        self._lib.iblines(handle, byref(status))
        return status.value

    def listener(self, pad: int, sad: int = 0, *, handle: int | None = None) -> bool:
        """Check if a listener is present (board or device).

        This method is the [ibln](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibln.html)
        function.

        Args:
            pad: Primary address of the GPIB device.
            sad: Secondary address of the GPIB device.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            Whether a listener is present.
        """
        if handle is None:
            handle = self._handle
        listener = c_short()
        self._lib.ibln(handle, pad, sad, byref(listener))
        return bool(listener.value)

    def local(self, *, handle: int | None = None) -> int:
        """Go to local mode (board or device).

        This method is the [ibloc](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibloc.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Return:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibloc(handle)
        return ibsta

    def online(self, *, state: bool, handle: int | None = None) -> int:
        """Close or reinitialize descriptor (board or device).

        This method is the [ibonl](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibonl.html)
        function.

        If you want to close the connection for the GPIB board or device that was instantiated,
        use [disconnect][msl.equipment.interfaces.gpib.GPIB.disconnect].

        Args:
            state: If `False`, closes the connection. If `True`, then all settings associated with the
                descriptor (GPIB address, end-of-string mode, timeout, etc.) are reset to their *default*
                values. The *default* values are the settings the descriptor had when it was first obtained.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibonl(handle, int(state))
        return ibsta

    def pass_control(
        self,
        *,
        handle: int | None = None,
        name: str | None = None,
        board: int | None = None,
        pad: int = 0,
        sad: int = NO_SEC_ADDR,
    ) -> int:
        """Set a GPIB board or device to become the controller-in-charge (CIC).

        This method is the [ibpct](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibpct.html)
        function.

        If no arguments are specified, the instantiated class becomes the CIC.

        Args:
            handle: Board or device descriptor. If specified, `name`, `board`, `pad` and `sad` are ignored.
            name: The name of a GPIB board or device. If specified, `board`, `pad` and `sad` are ignored.
            board: Index of the GPIB interface board.
            pad: Primary address of the GPIB device.
            sad: Secondary address of the GPIB device.

        Returns:
            The handle of the board or device that became CIC.
        """
        if handle is not None:
            pass
        elif name is not None:
            handle = self._get_ibfind_handle(name)
        elif board is not None:
            handle = self._get_ibdev_handle(board, pad, sad, 13, 1, 0)  # T10s = 13
        else:
            handle = self._handle

        self._lib.ibpct(handle)
        return handle

    @property
    def read_termination(self) -> bytes | None:  # pyright: ignore[reportImplicitOverride]
        """The termination character sequence that is used for the [read][msl.equipment.interfaces.message_based.MessageBased.read] method.

        By default, reading stops when the EOI line is asserted.
        """  # noqa: E501
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if not hasattr(self, "_lib"):
            return

        if isinstance(termination, str):
            termination = termination.encode()

        self._read_termination: bytes | None = termination
        if self._read_termination is not None:
            # enable end-of-string character, IbcEOSrd = 0xc
            _ = self.config(0xC, 1)

            # set end-of-string character, IbcEOSchar = 0xf
            _ = self.config(0xF, self._read_termination[-1])

    def remote_enable(self, *, state: bool, handle: int | None = None) -> int:
        """Set remote enable (board).

        This method is the [ibsre](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibsre.html)
        function.

        Args:
            state: If `True`, the board asserts the REN line. Otherwise, the REN line is not asserted.
                The board must be the system controller.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns: The status value (`ibsta`).
        """
        # ibsre was removed from ni4882.dll, use ibconfig instead (IbcSRE = 0xb)
        ibsta: int = self.config(0xB, int(state), handle=handle)
        return ibsta

    def serial_poll(self, *, handle: int | None = None) -> int:
        """Read status byte / serial poll (device).

        This method is the [ibrsp](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibrsp.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status byte.
        """
        if handle is None:
            handle = self._handle
        status = create_string_buffer(1)
        self._lib.ibrsp(handle, status)
        return ord(status.value)

    def spoll_bytes(self, *, handle: int | None = None) -> int:
        """Get the length of the serial poll bytes queue (device).

        This method is the [ibspb](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibspb.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.
        """
        if handle is None:
            handle = self._handle
        length = c_short()
        self._lib.ibspb(handle, byref(length))
        return length.value

    def status(self) -> int:
        """Returns the status value [ibsta](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html)."""
        return int(self._lib.ThreadIbsta())

    def trigger(self, *, handle: int | None = None) -> int:
        """Trigger device.

        This method is the [ibtrg](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibtrg.html)
        function.

        Args:
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibtrg(handle)
        return ibsta

    def version(self) -> str:
        """Returns the version of the GPIB library (linux only)."""
        try:
            version = c_char_p()
            self._lib.ibvers(byref(version))
            assert version.value is not None  # noqa: S101
            return version.value.decode()
        except AttributeError:
            return ""

    def wait(self, mask: int, *, handle: int | None = None) -> int:
        """Wait for an event (board or device).

        This method is the [ibwait](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibwait.html)
        function.

        Args:
            mask: Wait until one of the conditions specified in `mask` is true.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibwait(handle, mask)
        return ibsta

    def wait_for_srq(self, *, board: int | None = None) -> int:
        """Wait for the SRQ interrupt (SRQI, 0x1000) line to be asserted (board).

        This method will return when the board receives a service request from *any* device.
        If there are multiple devices connected to the board, you must determine which
        device asserted the service request.

        Args:
            board: Board descriptor. Default is the board descriptor of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if board is None:
            board = self._address_info.board
        return self.wait(0x1000, handle=board)  # SRQI = 0x1000

    def write_async(self, message: bytes, *, handle: int | None = None) -> int:
        """Write a message asynchronously (board or device).

        This method is the [ibwrta](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibwrta.html) function.

        Args:
            message: The data to send.
            handle: Board or device descriptor. Default is the handle of the instantiated class.

        Returns:
            The status value (`ibsta`).
        """
        if handle is None:
            handle = self._handle
        ibsta: int = self._lib.ibwrta(handle, message, len(message))
        return ibsta


@dataclass
class ParsedGPIBAddress:
    """The parsed result of a VISA-style address for the ZeroMQ interface.

    Args:
        board: The GPIB board number.
        name: The interface name.
        pad: Primary address.
        sad: Secondary address.
    """

    board: int
    name: str | None
    pad: int | None
    sad: int | None


def parse_gpib_address(address: str) -> ParsedGPIBAddress | None:
    """Get the board, interface name, primary address and secondary address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the GPIB interface.
    """
    match = REGEX.match(address)
    if not match:
        return None

    name = match["name"]
    if name and name.upper() == "INTFC":
        name = None

    return ParsedGPIBAddress(
        board=int(match["board"]) if match["board"] else 0,
        name=name,
        pad=int(match["pad"]) if match["pad"] else None,
        sad=int(match["sad"]) if match["sad"] else None,
    )
