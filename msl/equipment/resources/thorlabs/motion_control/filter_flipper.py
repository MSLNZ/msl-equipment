"""
A wrapper around Thorlabs.MotionControl.FilterFlipper.dll
"""
from ctypes import create_string_buffer, byref, c_int64
from ctypes.wintypes import WORD, DWORD

from .motion_control import MotionControl
from .api_functions import FilterFlipper_FCNS
from .structs import TLI_HardwareInformation, FF_IOSettings
from .enums import FF_IOModes, FF_SignalModes


class FilterFlipper(MotionControl):

    MIN_TRANSIT_TIME = 300
    MAX_TRANSIT_TIME = 2800
    MIN_PULSE_WIDTH = 10
    MAX_PULSE_WIDTH = 200

    def __init__(self, record):
        """A wrapper around Thorlabs.MotionControl.FilterFlipper.dll

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~.database.Database`.
        """
        MotionControl.__init__(self, record, FilterFlipper_FCNS)

    def open(self):
        """Open the device for communication.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_Open(self._serial)

    def close(self):
        """list of int: Disconnect and close the device."""
        return self.sdk.FF_Close(self._serial)

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :obj:`bool`
            Whether the USB is listed by the FTDI controller.
        """
        return self.sdk.FF_CheckConnection(self._serial)

    def identify(self):
        """Sends a command to the device to make it identify iteself."""
        return self.sdk.FF_Identify(self._serial)

    def get_hardware_info(self):
        """Gets the hardware information from the device.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        firmware_version = DWORD()
        hardware_version = WORD()
        modification_state = WORD()
        typ = WORD()
        num_channels = WORD()
        model_size = TLI_HardwareInformation.modelNumber.size
        model = create_string_buffer(model_size)
        notes_size = TLI_HardwareInformation.notes.size
        notes = create_string_buffer(notes_size)

        self.sdk.FF_GetHardwareInfo(self._serial, model, model_size, byref(typ), byref(num_channels),
                                    notes, notes_size, byref(firmware_version), byref(hardware_version),
                                    byref(modification_state))

        info = TLI_HardwareInformation()
        info.serialNumber = int(self._serial)
        info.modelNumber = model.value
        info.type = typ.value
        info.numChannels = num_channels.value
        info.notes = notes.value
        info.firmwareVersion = firmware_version.value
        info.hardwareVersion = hardware_version.value
        info.modificationState = modification_state.value
        return info

    def get_firmware_version(self):
        """Gets version number of the device firmware.

        Returns
        -------
        :obj:`str`
            The firmware version.
        """
        return self.to_version(self.sdk.FF_GetFirmwareVersion(self._serial))

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :obj:`str`
            The device software version.
        """
        return self.to_version(self.sdk.FF_GetSoftwareVersion(self._serial))

    def load_settings(self):
        """Update device with stored settings.

        Returns
        -------
        :obj:`bool`
            Whether loading the settings was successful.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_LoadSettings(self._serial)

    def persist_settings(self):
        """Persist the devices current settings.

        Returns
        -------
        :obj:`bool`: 
            Whether successful.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_PersistSettings(self._serial)

    def get_number_positions(self):
        """Get number of positions available from the device.
        
        Returns
        -------
        :obj:`int`
            The number of positions.
        """
        return self.sdk.FF_GetNumberPositions(self._serial)

    def home(self):
        """Home the device. 
        
        Homing the device will set the device to a known state and determine 
        the home position.
        
        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_Home(self._serial)

    def move_to_position(self, position, wait=False):
        """Move the device to the specified position (index).
        
        Parameters
        ----------
        position : :obj:`int`
            The required position. Must be 1 or 2. 
        wait : :obj:`bool`
            Whether to wait until the movement is complete before returning to 
            the calling program.
        
        Raises
        ------
        ConnectionError
            If not successful.
        """
        ret = self.sdk.FF_MoveToPosition(self._serial, position)
        if wait:
            self.clear_message_queue()
            msg_type, msg_id, msg_data = self.wait_for_message()
            while msg_type != 2 or msg_id != 1:
                msg_type, msg_id, msg_data = self.wait_for_message()
            assert self.get_position() == position, 'Wait until move finished is not working'
        return ret

    def get_position(self):
        """Get the current position (index).
        
        Returns
        -------
        :obj:`int`
            The current position, 1 or 2.
        """
        return self.sdk.FF_GetPosition(self._serial)

    def get_io_settings(self):
        """Gets the I/O settings from filter flipper.
        
        Returns
        -------
        :class:`~.structs.FF_IOSettings`
            The Filter Flipper I/O settings.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        settings = FF_IOSettings()
        self.sdk.FF_GetIOSettings(self._serial, byref(settings))
        return settings

    def request_io_settings(self):
        """Requests the I/O settings from the filter flipper. 
        
        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_RequestIOSettings(self._serial)

    def set_io_settings(self, transit_time=500,
                        oper1=FF_IOModes.FF_ToggleOnPositiveEdge, sig1=FF_SignalModes.FF_InputButton, pw1=200,
                        oper2=FF_IOModes.FF_ToggleOnPositiveEdge, sig2=FF_SignalModes.FF_OutputLevel, pw2=200):
        """
        Sets the settings on filter flipper.
        
        Parameters
        ----------
        transit_time : :obj:`int`
            Time taken to get from one position to other in milliseconds.
        oper1 : :class:`~.enums.FF_IOModes`
            I/O 1 Operating Mode.
        sig1 : :class:`~.enums.FF_SignalModes`
            I/O 1 Signal Mode.
        pw1 : :obj:`int`
            Digital I/O 1 pulse width in milliseconds. 
        oper2 : :class:`~.enums.FF_IOModes`
            I/O 2 Operating Mode.
        sig2 : :class:`~.enums.FF_SignalModes`
            I/O 2 Signal Mode.
        pw2 : :obj:`int`
            Digital I/O 2 pulse width in milliseconds. 

        Raises
        ------
        ConnectionError
            If not successful.
        """
        if transit_time > self.MAX_TRANSIT_TIME or transit_time < self.MIN_TRANSIT_TIME:
            msg = 'Invalid transit time value of {} ms; {} <= transit_time <= {}'.format(
                transit_time, self.MIN_TRANSIT_TIME, self.MAX_TRANSIT_TIME)
            self.raise_exception(msg)
        if pw1 > self.MAX_PULSE_WIDTH or pw1 < self.MIN_PULSE_WIDTH:
            msg = 'Invalid digital I/O 1 pulse width of {} ms; {} <= pw <= {}'.format(
                pw1, self.MIN_PULSE_WIDTH, self.MAX_PULSE_WIDTH)
            self.raise_exception(msg)
        if pw2 > self.MAX_PULSE_WIDTH or pw2 < self.MIN_PULSE_WIDTH:
            msg = 'Invalid digital I/O 2 pulse width of {} ms; {} <= pw <= {}'.format(
                pw2, self.MIN_PULSE_WIDTH, self.MAX_PULSE_WIDTH)
            self.raise_exception(msg)

        settings = FF_IOSettings()
        settings.transitTime = int(transit_time)
        settings.digIO1OperMode = self.convert_to_enum(oper1, FF_IOModes, prefix='FF_')
        settings.digIO1SignalMode = self.convert_to_enum(sig1, FF_SignalModes, prefix='FF_')
        settings.digIO1PulseWidth = int(pw1)
        settings.digIO2OperMode = self.convert_to_enum(oper2, FF_IOModes, prefix='FF_')
        settings.digIO2SignalMode = self.convert_to_enum(sig2, FF_SignalModes, prefix='FF_')
        settings.digIO2PulseWidth = int(pw2)
        return self.sdk.FF_SetIOSettings(self._serial, byref(settings))

    def get_transit_time(self):
        """Gets the transit time.
        
        Returns
        -------
        :obj:`int`
            The transit time in milliseconds.
        """
        return self.sdk.FF_GetTransitTime(self._serial)

    def set_transit_time(self, transit_time):
        """Sets the transit time.
        
        Parameters
        ----------
        transit_time : :obj:`int`
            The transit time in milliseconds.

        Raises
        ------
        ConnectionError
            If not successful.
        """
        if transit_time > self.MAX_TRANSIT_TIME or transit_time < self.MIN_TRANSIT_TIME:
            msg = 'Invalid transit time value of {} ms; {} <= transit_time <= {}'.format(
                transit_time, self.MIN_TRANSIT_TIME, self.MAX_TRANSIT_TIME)
            self.raise_exception(msg)
        return self.sdk.FF_SetTransitTime(self._serial, int(transit_time))

    def request_status(self):
        """Request status bits.
        
        This needs to be called to get the device to send it's current status.
        
        This is called automatically if Polling is enabled for the device using 
        :meth:`.start_polling`.
        
        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_RequestStatus(self._serial)

    def get_status_bits(self):
        """
        This returns the latest status bits received from the device.
        
        To get new status bits, use :meth:`.request_status` or use the polling 
        function, :meth:`.start_polling`
        
        Returns
        -------
        :obj:`int`
            The status bits from the device
        """
        return self.sdk.FF_GetStatusBits(self._serial)

    def start_polling(self, milliseconds):
        """Starts the internal polling loop.
        
        This function continuously requests position and status messages.
        
        Parameters
        ----------
        milliseconds : :obj:`int`
            The milliseconds polling rate.

        Returns
        -------
        :obj:`bool`
            Whether setting the polling interval was successful.
        """
        return self.sdk.FF_StartPolling(self._serial, int(milliseconds))

    def polling_duration(self):
        """Gets the polling loop duration.
        
        Returns
        -------
        :obj:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.FF_PollingDuration(self._serial)

    def stop_polling(self):
        """Stops the internal polling loop."""
        return self.sdk.FF_StopPolling(self._serial)

    def time_since_last_msg_received(self):
        """Gets the time, in milliseconds, since tha last message was received.
        
        This can be used to determine whether communications with the device is 
        still good.
        
        Returns
        -------
        :obj:`int`
            The time, in milliseconds, since the last message was received.
        """
        ms = c_int64()
        self.sdk.FF_TimeSinceLastMsgReceived(self._serial, byref(ms))
        return ms.value

    def enable_last_msg_timer(self, enable, msg_timeout=0):
        """Enables the last message monitoring timer.
        
        This can be used to determine whether communications with the device is 
        still good.
        
        Parameters
        ----------
        enable : :obj:`bool`
            :obj:`True` to enable monitoring otherwise :obj:`False` to disable.
        msg_timeout : :obj:`int`
            The last message error timeout in ms. Set to 0 to disable.
        """
        return self.sdk.FF_EnableLastMsgTimer(self._serial, enable, msg_timeout)

    def has_last_msg_timer_overrun(self):
        """Queries if the time since the last message has exceeded the 
        ``lastMsgTimeout`` set by :meth:`.enable_last_msg_timer`.
        
        This can be used to determine whether communications with the device is 
        still good.
        
        Returns
        -------
        :obj:`bool`
            :obj:`True` if last message timer has elapsed or 
            :obj:`False` if monitoring is not enabled or if time of last message 
            received is less than ``msg_timeout``.
        """
        return self.sdk.FF_HasLastMsgTimerOverrun(self._serial)

    def request_settings(self):
        """Requests that all settings are downloaded from the device.
        
        This function requests that the device upload all it's settings to the 
        DLL.
        
        Raises
        ------
        ConnectionError
            If not successful.
        """
        return self.sdk.FF_RequestSettings(self._serial)

    def clear_message_queue(self):
        """Clears the device message queue."""
        return self.sdk.FF_ClearMessageQueue(self._serial)

    def register_message_callback(self, callback):
        """Registers a callback on the message queue.
        
        Parameters
        ----------
        callback : :obj:`.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.
        """
        return self.sdk.FF_RegisterMessageCallback(self._serial, callback)

    def message_queue_size(self):
        """Gets the MessageQueue size.
        
        Returns
        -------
        :obj:`int`
            The number of messages in the queue.        
        """
        return self.sdk.FF_MessageQueueSize(self._serial)

    def get_next_message(self):
        """Get the next Message Queue item. See :mod:`.messages`.
        
        Returns
        -------
        :obj:`int`
            The message type.
        :obj:`int`
            The message ID.
        :obj:`int`
            The message data.        
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.FF_GetNextMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value

    def wait_for_message(self):
        """Wait for next Message Queue item. See :mod:`.messages`.
        
        Returns
        -------
        :obj:`int`
            The message type.
        :obj:`int`
            The message ID.
        :obj:`int`
            The message data.        
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.FF_WaitForMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value


if __name__ == '__main__':
    from msl.equipment.resources.utils import camelcase_to_underscore as convert

    for item in FilterFlipper_FCNS:
        method_name = convert(item[0].split('_')[1])
        args_p = ''
        args_c = ''
        for i, arg in enumerate(item[3]):
            if i == 0 and 'c_char_p' in str(arg[0]):
                args_c += 'self._serial, '
            elif 'PyCPointerType' in str(type(arg[0])):
                args_c += 'byref({}), '.format(convert(arg[1]))
            else:
                a = convert(arg[1])
                args_p += '{}, '.format(a)
                args_c += '{}, '.format(a)

        args_p = args_p[:-2]
        if args_p:
            print('    def {}(self, {}):'.format(method_name, args_p))
        else:
            print('    def {}(self):'.format(method_name))
        print('        return self.sdk.{}({})\n'.format(item[0], args_c[:-2]))
