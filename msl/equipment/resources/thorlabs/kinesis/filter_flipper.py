"""
This module provides all the functionality required to control a 
Filter Flipper (MFF101, MFF102).
"""
from ctypes import byref, c_int64

from msl.equipment.resources import register
from msl.equipment.resources.utils import WORD, DWORD
from msl.equipment.resources.thorlabs.kinesis.motion_control import MotionControl
from msl.equipment.resources.thorlabs.kinesis.api_functions import FilterFlipper_FCNS
from msl.equipment.resources.thorlabs.kinesis.structs import FF_IOSettings
from msl.equipment.resources.thorlabs.kinesis.enums import FF_IOModes, FF_SignalModes


@register(manufacturer=r'Thorlabs', model=r'MFF10[1|2]')
class FilterFlipper(MotionControl):

    MIN_TRANSIT_TIME = 300
    MAX_TRANSIT_TIME = 2800
    MIN_PULSE_WIDTH = 10
    MAX_PULSE_WIDTH = 200

    def __init__(self, record):
        """A wrapper around ``Thorlabs.MotionControl.FilterFlipper.dll``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a FilterFlipper connection supports the following key-value pairs in the
        :ref:`connections_database`::

            'device_name': str, the device name found in ThorlabsDefaultSettings.xml [default: None]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        name = record.connection.properties.get('device_name')
        if name is None:
            record.connection.properties['device_name'] = 'MFF Filter Flipper'

        super(FilterFlipper, self).__init__(record, FilterFlipper_FCNS)

    def open(self):
        """Open the device for communication.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_Open(self._serial)

    def close(self):
        """Disconnect and close the device."""
        self.sdk.FF_Close(self._serial)

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :class:`bool`
            Whether the USB is listed by the FTDI controller.
        """
        return self.sdk.FF_CheckConnection(self._serial)

    def identify(self):
        """Sends a command to the device to make it identify itself."""
        self.sdk.FF_Identify(self._serial)

    def get_hardware_info(self):
        """Gets the hardware information from the device.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        return self._get_hardware_info(self.sdk.FF_GetHardwareInfo)

    def get_firmware_version(self):
        """Gets version number of the device firmware.

        Returns
        -------
        :class:`str`
            The firmware version.
        """
        return self.to_version(self.sdk.FF_GetFirmwareVersion(self._serial))

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :class:`str`
            The device software version.
        """
        return self.to_version(self.sdk.FF_GetSoftwareVersion(self._serial))

    def load_settings(self):
        """Update device with stored settings.

        The settings are read from ``ThorlabsDefaultSettings.xml``, which
        gets created when the Kinesis software is installed.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_LoadSettings(self._serial)

    def load_named_settings(self, settings_name):
        """Update device with named settings.

        Parameters
        ----------
        settings_name : :class:`str`
            The name of the device to load the settings for. Examples for the value
            of `setting_name` can be found in `ThorlabsDefaultSettings.xml``, which
            gets created when the Kinesis software is installed.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_LoadNamedSettings(self._serial, settings_name)

    def persist_settings(self):
        """Persist the devices current settings.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_PersistSettings(self._serial)

    def get_number_positions(self):
        """Get number of positions available from the device.
        
        Returns
        -------
        :class:`int`
            The number of positions.
        """
        return self.sdk.FF_GetNumberPositions(self._serial)

    def home(self):
        """Home the device. 
        
        Homing the device will set the device to a known state and determine 
        the home position.
        
        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_Home(self._serial)

    def move_to_position(self, position):
        """Move the device to the specified position (index).

        Parameters
        ----------
        position : :class:`int`
            The required position. Must be 1 or 2. 

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_MoveToPosition(self._serial, position)

    def get_position(self):
        """Get the current position (index).
        
        Returns
        -------
        :class:`int`
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        settings = FF_IOSettings()
        self.sdk.FF_GetIOSettings(self._serial, byref(settings))
        return settings

    def request_io_settings(self):
        """Requests the I/O settings from the filter flipper. 
        
        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_RequestIOSettings(self._serial)

    def set_io_settings(self, transit_time=500,
                        oper1=FF_IOModes.FF_ToggleOnPositiveEdge, sig1=FF_SignalModes.FF_InputButton, pw1=200,
                        oper2=FF_IOModes.FF_ToggleOnPositiveEdge, sig2=FF_SignalModes.FF_OutputLevel, pw2=200):
        """
        Sets the settings on filter flipper.
        
        Parameters
        ----------
        transit_time : :class:`int`, optional
            Time taken to get from one position to other in milliseconds.
        oper1 : :class:`~.enums.FF_IOModes`, optional
            I/O 1 Operating Mode.
        sig1 : :class:`~.enums.FF_SignalModes`, optional
            I/O 1 Signal Mode.
        pw1 : :class:`int`, optional
            Digital I/O 1 pulse width in milliseconds. 
        oper2 : :class:`~.enums.FF_IOModes`, optional
            I/O 2 Operating Mode.
        sig2 : :class:`~.enums.FF_SignalModes`, optional
            I/O 2 Signal Mode.
        pw2 : :class:`int`, optional
            Digital I/O 2 pulse width in milliseconds. 

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
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
        self.sdk.FF_SetIOSettings(self._serial, byref(settings))

    def get_transit_time(self):
        """Gets the transit time.
        
        Returns
        -------
        :class:`int`
            The transit time in milliseconds.
        """
        return self.sdk.FF_GetTransitTime(self._serial)

    def set_transit_time(self, transit_time):
        """Sets the transit time.
        
        Parameters
        ----------
        transit_time : :class:`int`
            The transit time in milliseconds.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if transit_time > self.MAX_TRANSIT_TIME or transit_time < self.MIN_TRANSIT_TIME:
            msg = 'Invalid transit time value of {} ms; {} <= transit_time <= {}'.format(
                transit_time, self.MIN_TRANSIT_TIME, self.MAX_TRANSIT_TIME)
            self.raise_exception(msg)
        self.sdk.FF_SetTransitTime(self._serial, int(transit_time))

    def request_status(self):
        """Request status bits.
        
        This needs to be called to get the device to send it's current status.
        
        This is called automatically if Polling is enabled for the device using 
        :meth:`.start_polling`.
        
        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_RequestStatus(self._serial)

    def get_status_bits(self):
        """Get the current status bits.
        
        This returns the latest status bits received from the device. To get 
        new status bits, use :meth:`.request_status` or use the polling 
        function, :meth:`.start_polling`
        
        Returns
        -------
        :class:`int`
            The status bits from the device.
        """
        return self.sdk.FF_GetStatusBits(self._serial)

    def start_polling(self, milliseconds):
        """Starts the internal polling loop.
        
        This function continuously requests position and status messages.
        
        Parameters
        ----------
        milliseconds : :class:`int`
            The polling rate, in milliseconds.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_StartPolling(self._serial, int(milliseconds))

    def polling_duration(self):
        """Gets the polling loop duration.
        
        Returns
        -------
        :class:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.FF_PollingDuration(self._serial)

    def stop_polling(self):
        """Stops the internal polling loop."""
        self.sdk.FF_StopPolling(self._serial)

    def time_since_last_msg_received(self):
        """Gets the time, in milliseconds, since tha last message was received.
        
        This can be used to determine whether communications with the device is 
        still good.
        
        Returns
        -------
        :class:`int`
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
        enable : :class:`bool`
            :data:`True` to enable monitoring otherwise :data:`False` to disable.
        msg_timeout : :class:`int`, optional
            The last message error timeout in ms. Set to 0 to disable.
        """
        self.sdk.FF_EnableLastMsgTimer(self._serial, enable, msg_timeout)

    def has_last_msg_timer_overrun(self):
        """Queries if the time since the last message has exceeded the 
        ``lastMsgTimeout`` set by :meth:`.enable_last_msg_timer`.
        
        This can be used to determine whether communications with the device is 
        still good.
        
        Returns
        -------
        :class:`bool`
            :data:`True` if last message timer has elapsed or
            :data:`False` if monitoring is not enabled or if time of last message
            received is less than ``msg_timeout``.
        """
        return self.sdk.FF_HasLastMsgTimerOverrun(self._serial)

    def request_settings(self):
        """Requests that all settings are downloaded from the device.
        
        This function requests that the device upload all it's settings to the 
        DLL.
        
        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.FF_RequestSettings(self._serial)

    def clear_message_queue(self):
        """Clears the device message queue."""
        self.sdk.FF_ClearMessageQueue(self._serial)

    def register_message_callback(self, callback):
        """Registers a callback on the message queue.
        
        Parameters
        ----------
        callback : :class:`~msl.equipment.resources.thorlabs.kinesis.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.
        """
        self.sdk.FF_RegisterMessageCallback(self._serial, callback)

    def message_queue_size(self):
        """Gets the size of the message queue.
        
        Returns
        -------
        :class:`int`
            The number of messages in the queue.        
        """
        return self.sdk.FF_MessageQueueSize(self._serial)

    def get_next_message(self):
        """Get the next Message Queue item. See :mod:`.messages`.
        
        Returns
        -------
        :class:`int`
            The message type.
        :class:`int`
            The message ID.
        :class:`int`
            The message data.        

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
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
        :class:`int`
            The message type.
        :class:`int`
            The message ID.
        :class:`int`
            The message data.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.FF_WaitForMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value


if __name__ == '__main__':
    from msl.equipment.resources.thorlabs.kinesis import _print
    _print(FilterFlipper, FilterFlipper_FCNS, 'Thorlabs.MotionControl.FilterFlipper.h')
