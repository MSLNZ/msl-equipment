"""
This module provides all the functionality required to control a
KCube Piezo controller (KPZ101).
adapted by @byquip 05/04/2024
"""
from ctypes import c_int16, c_uint, c_int64, byref, c_short, c_int32
import time

from msl.equipment.resources import register
from msl.equipment.resources.utils import WORD, DWORD
from msl.equipment.resources.thorlabs.kinesis.motion_control import MotionControl
from msl.equipment.resources.thorlabs.kinesis.api_functions import KCube_Piezo_FCNS
from msl.equipment.resources.thorlabs.kinesis.structs import (
    KPZ_MMIParams,
    KPZ_TriggerConfig,
)
from msl.equipment.resources.thorlabs.kinesis.enums import (
    PPC_IOOutputBandwidth,
    PPC_DisplayIntensity,
    PPC_IOControlMode, PPC_IOFeedbackSourceDefinition, PPC_NotchFilterState,
    PPC_DerivFilterState, PPC_NotchFilterChannel, KPZ_WheelMode,
    KPZ_TriggerPortMode, KPZ_TriggerPortPolarity, KPZ_WheelChangeRate,
    KPZ_WheelDirectionSense,
)


@register(manufacturer=r'Thorlabs', model=r'KPZ101')
class KCubePiezo(MotionControl):

    def __init__(self, record):
        """A wrapper around ``Thorlabs.MotionControl.KCube.P``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a KCubeSolenoid connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'device_name': str, the device name found in ThorlabsDefaultSettings.xml [default: None]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(KCubePiezo, self).__init__(record, KCube_Piezo_FCNS)
        self.j_mode = 2  # joystick mode: 1 = voltage adjust, 2 = jogging, 3 = set voltage
        self.j_rate = 1  # voltage adjust speed (1-3) = (slow-fast)
        self.j_dir = 1  # joystick direction sense
        self.v_set1 = 0.0  # voltage setting 1 as a percentage of the total voltage
        self.v_set2 = 0.0  # voltage setting 2 as a percentage of the total voltage
        self.dspI = 50  # display intensity (from 0 to 100)
        self.v_step = 1  # voltage step size as a percentage of the total voltage
    
    def get_zero_offset(self):
        """Get the zero offset.

        Returns
        -------
        :class:`int`
            The zero offset as a percentage (0-100) of the total output voltage
        """
        self.get_output_voltage()
        v_before = self.stage_output_voltage
        self.set_output_voltage(v_before)
        time.sleep(1)
        self.get_output_voltage()
        self.zero_offset = self.stage_output_voltage - v_before
        self.set_output_voltage(v_before - self.zero_offset)
        print(f'Stage {self._serial} zero set to {self.zero_offset}')
    
    def get_output_voltage(self):
        """Get the output voltage.

        Returns
        -------
        :class:`float`
            The output voltage as a percentage (0-100) of the total output voltage
        """
        actual_v_out = self.sdk.PCC_GetOutputVoltage(self._serial)
        self.stage_output_voltage = 100.0 * float(actual_v_out) / 32767
        return self.stage_output_voltage
    
    def set_output_voltage(self, voltage):
        """Set the output voltage.

        Parameters
        ----------
        voltage : :class:`float`
            The output voltage is a percentage (0-100) of the total output voltage
        """
        if voltage > 100:
            voltage = 100
        if voltage < 0:
            voltage = 0
        self.sdk.PCC_SetOutputVoltage(self._serial, int(round(voltage / 100.0 * 32767)))
    
    def set_step_voltage(self, v_step_set, wait_for_update=True):
        """Set the voltage step size.

        Parameters
        ----------
        v_step : :class:`int`
            The voltage step size as a percentage of the total voltage.
        """
        if v_step_set > 100:
            v_step_set = 100
        if v_step_set < 0:
            v_step_set = 0

        self.set_mmi_params(intensity=self.dspI, v_step=v_step_set)
        
        if wait_for_update:
            time.sleep(.1)  # wait for the device to update

            params = self.get_mmi_params()
            v_step = params[2]
            v_step_actual = 100.0 * float(v_step) / 32767

        self.stage_step_voltage = v_step_actual
    
    def set_voltage_source(self, voltage_source=0):
        """Set the voltage source.

        Parameters
        ----------
        voltage_source : :class:`int`
            The voltage source. 0 is software only. 1 is software and external. 2 is software and potentiometer, 3 is all three.
        """
        self.sdk.PCC_SetVoltageSource(self._serial, voltage_source)
    
    def enable(self):
        """Enable the device.

        Parameters
        ----------
        serial : :class:`int`
            The serial number of the device.
        """
        self.sdk.PCC_Enable(self._serial)
    
    def get_mmi_params(self):
        """Get the MMI Parameters for the KCube Display Interface.

        Returns
        -------
        :class:`int`
            The display intensity, range 0 to 100%.
        :class:`int`
            The display timeout, range 0 to 480 in minutes (0 is off, otherwise
            the inactivity period before dimming the display).
        :class:`int`
            The display dimmed intensity, range 0 to 10 (after the timeout
            period the device display will dim).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        j_mode = c_short(0)
        j_rate = c_short(0)
        v_step = c_int32(0)
        j_dir = c_short(0)
        v_set1 = c_int32(0)
        v_set2 = c_int32(0)
        dspI = c_int16(0)
        self.sdk.PCC_GetMMIParams(self._serial, byref(j_mode), byref(j_rate), byref(v_step), byref(j_dir),
                                    byref(v_set1), byref(v_set2), byref(dspI))
        
        return j_mode.value, j_rate.value, v_step.value, j_dir.value, v_set1.value, v_set2.value, dspI.value
    
    def set_mmi_params(self, intensity=50, v_step=1):
        """Set the MMI Parameters for the KCube Display Interface.

        Parameters
        ----------
        intensity : :class:`int`
            The display intensity, range 0 to 100%.
        timeout : :class:`int`
            The display timeout, range 0 to 480 in minutes (0 is off, otherwise
            the inactivity period before dimming the display).
        dim_intensity : :class:`int`
            The display dimmed intensity, range 0 to 10 (after the timeout
            period the device display will dim).
        """

        self.dspI = intensity
        self.v_step = v_step
        
        self.sdk.PCC_SetMMIParams(self._serial, self.j_mode, self.j_rate, int(round(self.v_step / 100.0 * 32767)),
                                  self.j_dir, int(round(self.v_set1 / 100.0 * 32767)),
                                  int(round(self.v_set2 / 100.0 * 32767)), self.dspI)
    
    def set_hub_analog_input(self, input_source=3):
        """Set the hub analog input.

        Parameters
        ----------
        input_source : :class:`int`
            The input source.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_SetHubAnalogInput(self._serial, input_source)
    
    def set_position_control_mode(self, loop_mode=1):
        """Set the position control mode.

        Parameters
        ----------
        loop_mode : :class:`int`
            1 for open loop, 2 for closed loop.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_SetPositionControlMode(self._serial, loop_mode)
    
    def set_feedback_loop_pi_consts(self, prop_term=100, int_term=15):
        """Set the feedback loop PI constants.

        Parameters
        ----------
        prop_term : :class:`int`
            The proportional term.
        int_term : :class:`int`
            The integral term.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_SetFeedbackLoopPIconsts(self._serial, prop_term, int_term)
    
    def set_max_output_voltage(self, voltage=750):
        """Set the maximum output voltage.

        Parameters
        ----------
        voltage : :class:`float`
            The maximum output voltage in volts * 10 (750 = 75 Volts).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_SetMaxOutputVoltage(self._serial, voltage)

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :class:`bool`
            Whether the USB is listed by the FTDI controller.
        """
        return self.sdk.PCC_CheckConnection(self._serial)

    def clear_message_queue(self):
        """Clears the device message queue."""
        self.sdk.PCC_ClearMessageQueue(self._serial)

    def close(self):
        """Disconnect and close the device."""
        self.sdk.PCC_Close(self._serial)

    def enable_last_msg_timer(self, enable, msg_timeout=0):
        """Enables the last message monitoring timer.

        This can be used to determine whether communications with the device is
        still good.

        Parameters
        ----------
        enable : :class:`bool`
            :data:`True` to enable monitoring otherwise :data:`False` to disable.
        msg_timeout : :class:`int`
            The last message error timeout in ms. Set to 0 to disable.
        """
        self.sdk.PCC_EnableLastMsgTimer(self._serial, enable, msg_timeout)

    def get_hardware_info(self):
        """Gets the hardware information from the device.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self._get_hardware_info(self.sdk.PCC_GetHardwareInfo)

    def get_hardware_info_block(self):
        """Gets the hardware information in a block.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        info = TLI_HardwareInformation()
        self.sdk.PCC_GetHardwareInfoBlock(self._serial, byref(info))
        return info

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
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.PCC_GetNextMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :class:`str`
            The device software version.
        """
        return self.to_version(self.sdk.PCC_GetSoftwareVersion(self._serial))

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
        return self.sdk.PCC_GetStatusBits(self._serial)

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
            received is less than ``lastMsgTimeout``.
        """
        return self.sdk.PCC_HasLastMsgTimerOverrun(self._serial)

    def identify(self):
        """Sends a command to the device to make it identify itself."""
        self.sdk.PCC_Identify(self._serial)

    def load_settings(self):
        """Update device with stored settings.

        The settings are read from ``ThorlabsDefaultSettings.xml``, which
        gets created when the Kinesis software is installed.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_LoadSettings(self._serial)

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
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_LoadSettings(self._serial, settings_name.encode())

    def message_queue_size(self):
        """Gets the size of the message queue.

        Returns
        -------
        :class:`int`
            The number of messages in the queue.
        """
        return self.sdk.PCC_MessageQueueSize(self._serial)

    def open(self):
        """Open the device for communication.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        return self.sdk.PCC_Open(self._serial)

    def persist_settings(self):
        """Persist the devices current settings.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_PersistSettings(self._serial)

    def polling_duration(self):
        """Gets the polling loop duration.

        Returns
        -------
        :class:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.PCC_PollingDuration(self._serial)

    def register_message_callback(self, callback):
        """Registers a callback on the message queue.

        Parameters
        ----------
        callback : :class:`~msl.equipment.resources.thorlabs.kinesis.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.
        """
        self.sdk.PCC_RegisterMessageCallback(self._serial, callback)

    def request_settings(self):
        """Requests that all settings are download from device.

        This function requests that the device upload all it's settings to the DLL.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_RequestSettings(self._serial)

    def request_status(self):
        """Requests the status from the device.

        This needs to be called to get the device to send it's current status bits.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_RequestStatus(self._serial)

    def request_status_bits(self):
        """Request the status bits which identify the current motor state.

        This needs to be called to get the device to send it's current status bits.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_RequestStatusBits(self._serial)

    def start_polling(self, milliseconds):
        """Starts the internal polling loop.

        This function continuously requests position and status messages.

        Parameters
        ----------
        milliseconds : :class:`int`
            The polling rate, in milliseconds.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.PCC_StartPolling(self._serial, int(milliseconds))

    def stop_polling(self):
        """Stops the internal polling loop."""
        self.sdk.PCC_StopPolling(self._serial)

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
        self.sdk.PCC_TimeSinceLastMsgReceived(self._serial, byref(ms))
        return ms.value

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
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.PCC_WaitForMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value


if __name__ == '__main__':
    from msl.equipment.resources.thorlabs.kinesis import _print
    _print(KCubePiezo, KCube_Piezo_FCNS, 'Thorlabs.MotionControl.KCube.Piezo.h')
