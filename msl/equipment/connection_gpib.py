"""
Base class for equipment that is connected through GPIB.
"""
from __future__ import annotations

import os
import sys
from bisect import bisect_right
from ctypes import POINTER
from ctypes import byref
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_long
from ctypes import c_short
from ctypes import c_wchar_p
from ctypes import create_string_buffer
from functools import partial
from typing import Callable
from typing import TYPE_CHECKING

from msl.loadlib import LoadLibrary

from .config import Config
from .connection_message_based import ConnectionMessageBased
from .constants import IS_LINUX
from .constants import REGEX_GPIB
from .exceptions import GPIBError
from .exceptions import MSLConnectionError
from .exceptions import MSLTimeoutError
from .utils import logger

if TYPE_CHECKING:
    from .record_types import EquipmentRecord

_gpib_library: LoadLibrary | None = None

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
    EDVR: 'A system call has failed; ibcnt/ibcntl will be set to the value of errno',
    ECIC: 'Your interface board needs to be controller-in-charge, but is not',
    ENOL: 'You have attempted to write data or command bytes, but there are no listeners currently addressed',
    EADR: 'The interface board has failed to address itself properly before starting an io operation',
    EARG: 'One or more arguments to the function call were invalid',
    ESAC: 'The interface board needs to be system controller, but is not',
    EABO: 'A read or write of data bytes has been aborted, possibly due to a timeout '
          'or reception of a device clear command',
    ENEB: 'The GPIB interface board does not exist, its driver is not loaded, or it is in use by another process',
    EDMA: 'Not used (DMA error), included for compatibility purposes',
    EOIP: 'Function call can not proceed due to an asynchronous IO operation '
          '(ibrda(), ibwrta(), or ibcmda()) in progress',
    ECAP: 'Incapable of executing function call, due the GPIB board lacking the capability, '
          'or the capability being disabled in software',
    EFSO: 'File system error. ibcnt/ibcntl will be set to the value of errno',
    EBUS: 'An attempt to write command bytes to the bus has timed out',
    ESTB: 'One or more serial poll status bytes have been lost. This can occur due to too many '
          'status bytes accumulating (through automatic serial polling) without being read',
    ESRQ: 'The serial poll request service line is stuck on',
    ETAB: 'This error can be returned by ibevent(), FindLstn(), or FindRQS() '
          '(see their descriptions for more information)',

    # ni4882.h
    ELCK: 'Address or board is locked',
    EARM: 'The ibnotify Callback failed to rearm',
    EHDL: 'The input handle is invalid for this operation',
    EWIP: 'Wait already in progress on input handle',
    ERST: 'The event notification was cancelled due to a reset of the interface',
    EPWR: 'The system or board has lost power or gone to standby',

    # https://documentation.help/NI-488.2/trou4xyt.html
    -535560148: 'The board number is within the range of allowed board numbers, '
                'but it has not been assigned to a GPIB interface',
    -535560155: 'The board number is not within the range of allowed board numbers',
    -535560139: 'The device name is not listed in the logical device templates that '
                'are part of Measurement & Automation Explorer',
    -519569280: 'You are using a removable interface (for example, a GPIB-USB-HS) and you removed or '
                'ejected the interface while the software is trying to communicate with it',
    -519569279: 'You are using a removable interface (for example, a GPIB-USB-HS) and you removed or '
                'ejected the interface while the software is trying to communicate with it',
    -536215481: 'The driver encountered an access violation when attempting to access an '
                'object supplied by the user',
    -519897021: 'You have enabled DOS NI-488.2 support and attempted to run an existing DOS NI-488.2 '
                'application that was compiled with an older, unsupported DOS application interface',
    -519700363: 'The driver is unable to communicate with a GPIB-ENET/100 during an ibfind or ibdev call',
    -519700360: 'You are using a GPIB-ENET/100 and the network link is broken between the host and the '
                'GPIB-ENET/100 interface',
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
    1,
    3,
    10,
    30,
    100,
    300,
    1000,
)


def _load_library(errcheck: Callable[[int, Callable, tuple], int] | None = None) -> None:
    """Load a GPIB library.

    :param errcheck: A callable function assigned to ctypes._FuncPtr.errcheck
        for each function in the GPIB library that returns the ibsta status value.
    """
    global _gpib_library
    if _gpib_library is not None:
        return

    libtype = 'windll' if sys.platform == 'win32' else 'cdll'
    if Config.GPIB_LIBRARY:
        _gpib_library = LoadLibrary(Config.GPIB_LIBRARY, libtype=libtype)
    else:
        files: list[str] = []
        if sys.platform == 'win32':
            files.extend([
                'ni4882.dll',
                'gpib-32.dll',
            ])
        elif sys.platform == 'linux':
            files.extend([
                'gpib',  # use ctypes.util.find_library in LoadLibrary
                'libgpib.so.0',
                '/usr/local/lib/libgpib.so.0',
                'gpib-32.so',
            ])
        elif sys.platform == 'darwin':
            files.extend([
                '/Library/Frameworks/NI4882.framework/NI4882',
                'macosx_gpib_lib_1.0.3a.dylib',
            ])
        else:
            raise OSError(f'GPIB is not yet implemented on platform {sys.platform!r}')

        for file in files:
            try:
                _gpib_library = LoadLibrary(file, libtype=libtype)
                break
            except OSError:
                pass

        if _gpib_library is None:
            raise OSError(f'Cannot load a GPIB library: {", ".join(files)}\n'
                          f'If you have a GPIB library available, set '
                          f'Config.GPIB_LIBRARY to be equal to the path '
                          f'to the library file')

    lib = _gpib_library.lib

    if errcheck is None:
        def _error_check(result, func, arguments):
            logger.debug('gpib.%s%s -> 0x%x', func.__name__, arguments, result)
            if result & TIMO:
                raise MSLTimeoutError(
                    'If you are confident that the GPIB device received a\n'
                    'valid message, you may want to check the manual to '
                    'determine if the device sets the EOI line\nat the end '
                    'of a message transfer. If EOI is not set, you may '
                    'need to specify a value for the\nread_termination '
                    'character.')

            if result & ERR:
                # mimic _SetGpibError in linux-gpib-user/language/python/gpibinter.c
                iberr = lib.ThreadIberr()
                if iberr == EDVR or iberr == EFSO:
                    iberr = lib.ibcntl()
                    if IS_LINUX:
                        try:
                            message = os.strerror(iberr)
                        except (OverflowError, ValueError):
                            message = 'Invalid os.strerror code'
                    else:
                        message = _ERRORS.get(iberr, 'Unknown error')
                else:
                    message = _ERRORS.get(iberr, 'Unknown error')
                raise GPIBError(message, name=func.__name__, ibsta=result, iberr=iberr)

            return result

        errcheck = _error_check

    definitions = [
        ('ibask', True, c_int, [c_int, c_int, POINTER(c_int)]),
        ('ibcac', True, c_int, [c_int, c_int]),
        ('ibclr', True, c_int, [c_int]),
        ('ibcmd', True, c_int, [c_int, c_char_p, c_long]),
        ('ibconfig', True, c_int, [c_int, c_int, c_int]),
        ('ibdev', False, c_int, [c_int, c_int, c_int, c_int, c_int, c_int]),
        ('ibgts', True, c_int, [c_int, c_int]),
        ('iblines', True, c_int, [c_int, POINTER(c_short)]),
        ('ibln', True, c_int, [c_int, c_int, c_int, POINTER(c_short)]),
        ('ibloc', True, c_int, [c_int]),
        ('ibonl', True, c_int, [c_int, c_int]),
        ('ibpct', True, c_int, [c_int]),
        ('ibrd', True, c_int, [c_int, c_char_p, c_long]),
        ('ibrsp', True, c_int, [c_int, c_char_p]),
        ('ibsic', True, c_int, [c_int]),
        ('ibspb', True, c_int, [c_int, POINTER(c_short)]),
        ('ibtrg', True, c_int, [c_int]),
        ('ibwait', True, c_int, [c_int, c_int]),
        ('ibwrt', True, c_int, [c_int, c_char_p, c_long]),
        ('ibwrta', True, c_int, [c_int, c_char_p, c_long]),
        ('ThreadIbsta', False, c_int, []),
        ('ThreadIberr', False, c_int, []),
    ]

    if sys.platform == 'win32':
        definitions.extend([
            ('ibfindW', False, c_int, [c_wchar_p]),
        ])
    else:
        definitions.extend([
            ('ibfind', False, c_int, [c_char_p]),
            ('ibvers', False, None, [POINTER(c_char_p)]),
        ])

    for fcn, err_check, restype, argtypes in definitions:
        try:
            function = getattr(lib, fcn)
        except AttributeError:
            def not_implement(*ignore, f=fcn):  # noqa: ignore is not used
                raise MSLConnectionError(f'{f!r} is not implement on {sys.platform!r}')
            setattr(lib, fcn, partial(not_implement, f=fcn))
            continue

        function.argtypes = argtypes
        function.restype = restype
        if err_check:
            function.errcheck = errcheck

    try:
        lib.ThreadIbcntl.restype = c_long
        setattr(lib, 'ibcntl', lib.ThreadIbcntl)
    except AttributeError:
        lib.ThreadIbcnt.restype = c_long
        setattr(lib, 'ibcntl', lib.ThreadIbcnt)


def find_listeners(include_sad: bool = True) -> list[str]:
    """Find GPIB listeners.

    :param include_sad: Whether to scan all secondary GPIB addresses.
    :return: The GPIB addresses that were found.
    """
    logger.debug('find GPIB listeners: include_sad=%s', include_sad)
    devices: list[str] = []

    def error_check(result: int, func: Callable, arguments: tuple) -> int:
        if result & ERR:
            iberr = lib.ThreadIberr()
            if iberr == EDVR or iberr == EFSO:
                iberr = lib.ibcntl()
                if IS_LINUX:
                    try:
                        message = os.strerror(iberr)
                    except (OverflowError, ValueError):
                        message = 'Invalid os.strerror code'
                else:
                    message = _ERRORS.get(iberr, 'Unknown error')
            else:
                message = _ERRORS.get(iberr, 'Unknown error')
            name = func.__name__
            if name == 'ibln':
                arguments = arguments[:3]
            elif name == 'ibask':
                arguments = arguments[:2]
            elif name == 'ibpct':
                arguments = arguments[:1]
            logger.debug('gpib.%s%s -> %s | %s (iberr: %s)',
                         name, arguments, hex(result), message, hex(iberr))
        return result

    try:
        _load_library(error_check)
    except (OSError, AttributeError) as e:
        logger.debug(str(e).splitlines()[0])
        return devices

    lib = _gpib_library.lib
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
                devices.append(f'GPIB{board}::{pad}::INSTR')
                continue

            if include_sad:
                for sad in range(96, 127):
                    if lib.ibln(board, pad, sad, byref(exists)) & ERR:
                        continue
                    if exists.value:
                        devices.append(f'GPIB{board}::{pad}::{sad}::INSTR')

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


class ConnectionGPIB(ConnectionMessageBased):

    _gpib_library: LoadLibrary | None = None

    def __init__(self, record: EquipmentRecord) -> None:
        """Base class for equipment that is connected through GPIB.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a GPIB connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'eos_mode': int, the end-of-string mode [default: 0]
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
            'read_termination': str or None, read until this termination sequence is found [default: None]
            'rstrip': bool, whether to remove trailing whitespace from "read" messages [default: False]
            'send_eoi': bool, enables or disables the assertion of the EOI signal [default: True]
            'termination': shortcut for setting both 'read_termination' and 'write_termination' to this value
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]
            'write_termination': str or None, termination sequence appended to write messages [default: '\\r\\n']

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by
        setting the value in the **Backend** field for a connection record
        in the :ref:`connections-database` to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        self._own = True
        self._handle = -1
        self._record = record

        address = record.connection.address
        info: dict | None = ConnectionGPIB.parse_address(address)
        if not info:
            raise ValueError(f'Invalid GPIB address {address!r}')

        props = record.connection.properties
        props.setdefault('read_termination', None)

        _load_library()
        self._lib = _gpib_library.lib

        if info['name']:
            # a board or device object from a name in a gpib.conf file
            self._handle = self._get_ibfind_handle(info['name'])
        elif info['pad'] is None:
            # a board object with the given board number
            self._handle = info['board']
            self._own = False
        else:
            # a device object
            send_eoi = int(props.get('send_eoi', True))
            eos_mode = int(props.get('eos_mode', 0))
            sad = 0 if info['sad'] is None else info['sad']
            if sad != 0 and sad < 0x60:
                # NI's unfortunate convention of adding 0x60 to secondary addresses
                sad += 0x60
            info['sad'] = sad
            timeout = _convert_timeout(props.get('timeout', None))
            args = info['board'], info['pad'], sad, timeout, send_eoi, eos_mode
            self._handle = self._get_ibdev_handle(*args)

        # keep this reference assignment after the if/else condition since the
        # value of the secondary address may have been updated
        self._address_info = info

        # check if the handle corresponds to a system controller (INTFC)
        self._is_board: bool
        try:
            self._is_board = bool(self.ask(0xa))  # IbaSC = 0xa
        except GPIBError:
            # asking IbaSC for a GPIB device raises EHDL error
            self._is_board = False

        super().__init__(record)

    def _get_ibfind_handle(self, name: str) -> int:
        if sys.platform == 'win32':
            handle = self._lib.ibfindW(name)
        else:
            handle = self._lib.ibfind(name.encode('ascii'))
        logger.debug('gpib.ibfind(%r) -> %d', name, handle)
        if handle < 0:
            raise GPIBError(f'Cannot acquire a handle for the '
                            f'GPIB board/device with name {name!r}')
        return handle

    def _get_ibdev_handle(self, *args: int) -> int:
        # board_index, pad, sad, timeout, send_eoi, eos_mode
        handle = self._lib.ibdev(*args)
        logger.debug('gpib.ibdev%s -> %d', args, handle)
        if handle < 0:
            raise GPIBError(f'Cannot acquire a handle for the '
                            f'GPIB device using {args}')
        return handle

    def _read(self, size: int | None) -> bytearray:
        """Overrides method in ConnectionMessageBased."""
        chunk_size = 20480  # 20kB = 20 * 1024
        data = create_string_buffer(chunk_size)
        buffer = bytearray()
        while True:
            sta = self._lib.ibrd(self._handle, data, chunk_size)
            buffer.extend(data[:self.count()])
            if len(buffer) > self._max_read_size:
                self.raise_exception(
                    f'Maximum read size exceeded: '
                    f'{len(buffer)} > {self._max_read_size}\n'
                    f'buffer: {buffer}')
            if sta & 0x2000:  # END
                break

        # always read until END so that the next _read() is correct,
        # but if size is specified, return the requested size
        if size is not None:
            return buffer[:size]
        return buffer

    def _set_backend_timeout(self) -> None:
        """Overrides method in ConnectionMessageBased."""
        if self._is_board:
            self.raise_exception('Cannot set a timeout value for a GPIB board')

        # set the timeout to one of the discrete values (IbcTMO = 0x3)
        self.config(0x3, _convert_timeout(self._timeout))

        # read back the actual timeout (IbaTMO = 0x3)
        index = self.ask(0x3)
        self._timeout = None if index == 0 else _TIMEOUTS[index]

    def _write(self, message: bytes) -> int:
        """Overrides method in ConnectionMessageBased."""
        self._lib.ibwrt(self._handle, message, len(message))
        return self.count()

    def ask(self, option: int, *, handle: int | None = None) -> int:
        """Get a configuration setting (board or device).

        This method is the `ibask <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibask.html>`_
        function, it should not be confused with the :meth:`~.ConnectionMessageBased.query` method.

        :param option: A configuration setting to get the value of.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The value of the configuration setting.
        """
        if handle is None:
            handle = self._handle
        setting = c_int()
        self._lib.ibask(handle, option, byref(setting))
        return setting.value

    @property
    def board(self) -> int:
        """Returns the board index."""
        return self._address_info['board']

    def clear(self, *, handle: int | None = None) -> int:
        """Send the clear command (device).

        This method is the `ibclr <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibclr.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibclr(handle)

    def command(self, data: bytes, *, handle: int | None = None) -> int:
        """Write command bytes (board).

        This method is the `ibcmd <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibcmd.html>`_
        function.

        :param data:
            The `commands <https://linux-gpib.sourceforge.io/doc_html/gpib-protocol.html#REFERENCE-COMMAND-BYTES>`_
            to write to the bus.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibcmd(handle, data, len(data))

    def config(self, option: int, value: int, *, handle: int | None = None) -> int:
        """Change configuration settings (board or device).

        This method is the `ibconfig <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibconfig.html>`_
        function.

        :param option: A configuration setting to change the value of.
        :param value: The new configuration setting value.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibconfig(handle, option, value)

    def control_atn(self, state: int, *, handle: int | None = None) -> int:
        """Set the state of the ATN line (board).

        This method mimics the PyVISA-py implementation.

        :param state: The state of the ATN line or the active controller.

            Allowed values are:

                * 0: ATN_DEASSERT
                * 1: ATN_ASSERT
                * 2: ATN_DEASSERT_HANDSHAKE
                * 3: ATN_ASSERT_IMMEDIATE

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        if state == ATN_DEASSERT:
            return self._lib.ibgts(handle, 0)
        if state == ATN_ASSERT:
            return self._lib.ibcac(handle, 0)
        if state == ATN_DEASSERT_HANDSHAKE:
            return self._lib.ibgts(handle, 1)
        if state == ATN_ASSERT_IMMEDIATE:
            return self._lib.ibcac(handle, 1)
        self.raise_exception(f'Invalid ATN {state=}')

    def control_ren(self, state: int, *, handle: int | None = None) -> int:
        """Controls the state of the GPIB Remote Enable (REN) interface line.

        Optionally the remote/local state of the device is also controlled.

        This method mimics the PyVISA-py implementation.

        :param state: Specifies the state of the REN line and optionally
            the device remote/local state.

            Allowed values are:

                * 0: REN_DEASSERT
                * 1: REN_ASSERT
                * 2: REN_DEASSERT_GTL
                * 3: REN_ASSERT_ADDRESS
                * 4: REN_ASSERT_LLO
                * 5: REN_ASSERT_ADDRESS_LLO
                * 6: REN_ADDRESS_GTL

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle

        sta = 0
        if self._is_board and state not in (REN_ASSERT, REN_DEASSERT, REN_ASSERT_LLO):
            self.raise_exception(f'Invalid REN {state=} for INTFC')

        if state == REN_DEASSERT_GTL:
            sta = self.command(b'\x01', handle=handle)  # GTL = 0x1

        if state in (REN_DEASSERT, REN_DEASSERT_GTL):
            sta = self.remote_enable(False, handle=handle)

        if state == REN_ASSERT_LLO:
            sta = self.command(b'\x11', handle=handle)  # LLO = 0x11
        elif state == REN_ADDRESS_GTL:
            sta = self.command(b'\x01', handle=handle)  # GTL = 0x1
        elif state == REN_ASSERT_ADDRESS_LLO:
            pass
        elif state in (REN_ASSERT, REN_ASSERT_ADDRESS):
            sta = self.remote_enable(True, handle=handle)
            if not self._is_board and state == REN_ASSERT_ADDRESS:
                sta = self.listener(self._address_info['pad'],
                                    sad=self._address_info['sad'],
                                    handle=handle)

        return sta

    def count(self) -> int:
        """Get the number of bytes sent or received.

        This method is the `ibcntl <https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibcnt.html>`_
        function.
        """
        return self._lib.ibcntl()

    def disconnect(self) -> None:
        """Close the GPIB connection."""
        if self._own and self._handle > 0:
            try:
                self.online(False, handle=self._handle)
            except GPIBError:
                pass
            self._own = False
            self.log_debug('Disconnected from %s', self.equipment_record.connection)

    @property
    def handle(self) -> int:
        """Returns the handle of the instantiated board or device."""
        return self._handle

    def interface_clear(self, *, handle: int | None = None) -> int:
        """Perform interface clear (board).

        Resets the GPIB bus by asserting the *interface clear* (IFC) bus line
        for a duration of at least 100 microseconds.

        This method is the `ibsic <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibsic.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibsic(handle)

    @property
    def library_path(self) -> str:
        """Returns the path to the GPIB library."""
        return _gpib_library.path

    def lines(self, *, handle: int | None = None) -> int:
        """Returns the status of the control and handshaking bus lines (board).

        This method is the `iblines <https://linux-gpib.sourceforge.io/doc_html/reference-function-iblines.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        """
        if handle is None:
            handle = self._handle
        status = c_short()
        self._lib.iblines(handle, byref(status))
        return status.value

    def listener(self, pad: int, sad: int = 0, *, handle: int | None = None) -> bool:
        """Check if a listener is present (board or device).

        This method is the `ibln <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibln.html>`_
        function.

        :param pad: Primary address of the GPIB device.
        :param sad: Secondary address of the GPIB device.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: Whether a listener is present.
        """
        if handle is None:
            handle = self._handle
        listener = c_short()
        self._lib.ibln(handle, pad, sad, byref(listener))
        return bool(listener.value)

    def local(self, *, handle: int | None = None) -> int:
        """Go to local mode (board or device).

        This method is the `ibloc <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibloc.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibloc(handle)

    def online(self, value: bool, *, handle: int | None = None) -> int:
        """Close or reinitialize descriptor (board or device).

        This method is the `ibonl <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibonl.html>`_
        function.

        If you want to close the connection for the GPIB board or device that was
        instantiated, use :meth:`.disconnect`.

        :param value: If :data:`False`, closes the connection. If :data:`True`,
            then all settings associated with the descriptor (GPIB address,
            end-of-string mode, timeout, etc.) are reset to their *default*
            values. The *default* values are the settings the descriptor had
            when it was first obtained.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibonl(handle, int(value))

    @property
    def name(self) -> str | None:
        """Returns the name of the board or device or :data:`None` if a name
        was not specified in the :attr:`~.ConnectionRecord.address`."""
        return self._address_info['name']

    @staticmethod
    def parse_address(address: str) -> dict | None:
        """Get the board, interface name, primary address and secondary address.

        :param address:
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`

        :return:
            The information about the GPIB connection or :data:`None` if `address`
            is not valid for a GPIB interface.
        """
        match = REGEX_GPIB.match(address)
        if not match:
            return

        return {
            'board': int(match['board']) if match['board'] else 0,
            'name': match['name'] if match['name'] != 'INTFC' else None,
            'pad': int(match['pad']) if match['pad'] else None,
            'sad': int(match['sad']) if match['sad'] else None,
        }

    def pass_control(self,
                     *,
                     handle: int | None = None,
                     name: str | None = None,
                     board: int | None = None,
                     pad: int = 0,
                     sad: int = NO_SEC_ADDR) -> int:
        """Set a GPIB board or device to become the controller-in-charge (CIC).

        This method is the `ibpct <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibpct.html>`_
        function.

        If no arguments are specified, the instantiated class becomes the CIC.

        :param handle: Board or device descriptor. If specified, `name`,
            `board`, `pad` and `sad` are ignored.
        :param name: The name of a GPIB board or device. If specified,
            `board`, `pad` and `sad` are ignored.
        :param board: Index of the GPIB interface board.
        :param pad: Primary address of the GPIB device.
        :param sad: Secondary address of the GPIB device.
        :return: The handle of the board or device that became CIC.
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
    def primary_address(self) -> int | None:
        """Returns the primary address of the GPIB device or :data:`None` if a
        primary address was not specified in the :attr:`~.ConnectionRecord.address`."""
        return self._address_info['pad']

    @property
    def read_termination(self) -> bytes | None:
        """The termination character sequence that is used for the
        :meth:`~.ConnectionMessageBased.read` method.

        By default, reading stops when the EOI line is asserted.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination: str | bytes | None) -> None:
        self._read_termination = self._encode_termination(termination)
        if self._read_termination is not None:
            # enable end-of-string character, IbcEOSrd = 0xc
            self.config(0xc, 1)

            # set end-of-string character, IbcEOSchar = 0xf
            self.config(0xf, self._read_termination[-1])

    def remote_enable(self, value: bool, *, handle: int | None = None) -> int:
        """Set remote enable (board).

        This method is the `ibsre <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibsre.html>`_
        function.

        :param value: If :data:`True`, the board asserts the REN line. Otherwise, the REN line
            is unasserted. The board must be the system controller.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        # ibsre was removed from ni4882.dll, use ibconfig instead (IbcSRE = 0xb)
        return self.config(0xb, int(value), handle=handle)

    @property
    def secondary_address(self) -> int | None:
        """Returns the secondary address of the GPIB device."""
        return self._address_info['sad']

    def serial_poll(self, *, handle: int | None = None) -> int:
        """Read status byte / serial poll (device).

        This method is the `ibrsp <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibrsp.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status byte.
        """
        if handle is None:
            handle = self._handle
        status = create_string_buffer(1)
        self._lib.ibrsp(handle, status)
        return ord(status.value)

    def spoll_bytes(self, *, handle: int | None = None) -> int:
        """Get the length of the serial poll bytes queue (device).

        This method is the `ibspb <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibspb.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        """
        if handle is None:
            handle = self._handle
        length = c_short()
        self._lib.ibspb(handle, byref(length))
        return length.value

    def status(self) -> int:
        """Returns the status value
        (`ibsta <https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html>`_)."""
        return self._lib.ThreadIbsta()

    def trigger(self, *, handle: int | None = None) -> int:
        """Trigger device.

        This method is the `ibtrg <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibtrg.html>`_
        function.

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibtrg(handle)

    def version(self) -> str:
        """Returns the version of the GPIB library (linux)."""
        try:
            version = c_char_p()
            self._lib.ibvers(byref(version))
            return version.value.decode()
        except AttributeError:
            return ''

    def wait(self, mask: int, *, handle: int | None = None) -> int:
        """Wait for an event (board or device).

        This method is the `ibwait <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibwait.html>`_
        function.

        :param mask: Wait until one of the conditions specified in `mask` is true.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibwait(handle, mask)

    def wait_for_srq(self, *, handle: int | None = None) -> int:
        """Wait for the SRQ line to be asserted (board or device).

        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        return self.wait(0x1000, handle=handle)  # SRQI = 0x1000

    def write_async(self, message: bytes, *, handle: int | None = None) -> int:
        """Write a message asynchronously (board or device).

        This method is the `ibwrta <https://linux-gpib.sourceforge.io/doc_html/reference-function-ibwrta.html>`_
        function.

        :param message: The data to send.
        :param handle: Board or device descriptor. Default is the handle of the instantiated class.
        :return: The status value (ibsta).
        """
        if handle is None:
            handle = self._handle
        return self._lib.ibwrta(handle, message, len(message))
