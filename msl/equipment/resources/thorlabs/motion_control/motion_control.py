"""
Base **Thorlabs.MotionControl** class.
"""
from ctypes import c_int, byref, create_string_buffer

from msl.loadlib import LoadLibrary

from msl.equipment.connection_msl import ConnectionSDK
from .errors import ERROR_CODES, FT_OK
from .structs import TLI_DeviceInfo
from .messages import MessageTypes, MessageID


class MotionControl(ConnectionSDK):

    # Currently defined Device ID numbers (device serial-number prefix), as of Kinesis v1.11.0
    Benchtop_Brushless_Motor = 73
    Benchtop_NanoTrak = 22
    Benchtop_Piezo_1_Channel = 41
    Benchtop_Piezo_3_Channel = 71
    Benchtop_Stepper_Motor_1_Channel = 40
    Benchtop_Stepper_Motor_3_Channel = 70
    Filter_Flipper = 37
    Filter_Wheel = 47
    KCube_Brushless_Motor = 28
    KCube_DC_Servo = 27
    KCube_LaserSource = 56
    KCube_Piezo = 29
    KCube_Solenoid = 68
    KCube_Stepper_Motor = 26
    Long_Travel_Stage = 45
    Cage_Rotator = 55
    LabJack_490 = 46
    LabJack_050 = 49
    Modular_NanoTrak = 52
    Modular_Piezo = 51
    Modular_Stepper_Motor = 50
    TCube_Brushless_Motor = 67
    TCube_DC_Servo = 83
    TCube_Inertial_Motor = 65
    TCube_LaserSource = 86
    TCube_LaserDiode = 64
    TCube_NanoTrak = 82
    TCube_Quad = 89
    TCube_Solenoid = 85
    TCube_Stepper_Motor = 80
    TCube_Strain_Gauge = 84
    TCube_TEC = 87

    # a serial number is 8 characters, 1 for null terminated, 1 for the comma, allow for up to 50 devices
    SERIAL_NUMBER_BUFFER_SIZE = (8 + 1 + 1) * 50

    DeviceManager = LoadLibrary('Thorlabs.MotionControl.DeviceManager.dll').lib

    def __init__(self, record, api_function):
        """
        Base **Thorlabs.MotionControl** class.
         
        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment
                record (a row) from the :class:`~msl.equipment.database.Database`.
            api_function (list): An API function list from :mod:`.api_functions` that the 
                subclass is a wrapper around.
            
        Raises:
            ConnectionError: If a connection to the device cannot be established.
        """
        ConnectionSDK.__init__(self, record, 'cdll')

        for item in api_function:
            func = getattr(self.sdk, item[0])
            func.restype = item[1]
            func.errcheck = getattr(self, item[2])
            func.argtypes = [v[0] for v in item[3]]

        self._serial = record.serial.encode()
        self.open()

    def errcheck_api(self, result, func, args):
        """The API function returns OK if the function call was successful."""
        self.log_errcheck(result, func, args)
        if result != FT_OK:
            self.raise_exception('{}: {}'.format(*ERROR_CODES[result]))
        return result

    def errcheck_true(self, result, func, args):
        """The API function returns :py:data:`True` if the function call was successful."""
        self.log_errcheck(result, func, args)
        if not result:
            msg = '{}.{}{} -> {}'.format(self.__class__.__name__, func.__name__, args, result)
            self.raise_exception(msg)
        return result

    def disconnect(self):
        """
        Disconnect and close the device.
        """
        self.close()

    @staticmethod
    def build_device_list():
        """
        Build the device list. 
    
        This function builds an internal collection of all devices found on the USB that are not currently open. 
        NOTE, if a device is open, it will not appear in the list until the device has been closed.
        
        Raises:
            ConnectionError: If the device list cannot be built. 
        """
        ret = MotionControl.DeviceManager.TLI_BuildDeviceList()
        if ret != 0:
            raise ConnectionError('Error building device list')
        return ret

    @staticmethod
    def get_device_list_size():
        """    
        Returns:
            :py:class:`int`: The number of devices in the device list. 
        """
        return MotionControl.DeviceManager.TLI_GetDeviceListSize()

    @staticmethod
    def get_device_list(*device_ids):
        """
        Get the contents of the device list which match the supplied device IDs.
    
        Args:
            device_ids (int): The devices in the device list.
    
        Returns:
            :py:class:`list`: A list of device serial numbers.

        Raises:
            ConnectionError: If there was an error getting the device list. 
        """
        n = MotionControl.SERIAL_NUMBER_BUFFER_SIZE
        buffer = create_string_buffer(n)
        ids = (c_int * len(device_ids))(*device_ids)
        if len(device_ids) == 0:
            ret = MotionControl.DeviceManager.TLI_GetDeviceListExt(buffer, n)
        else:
            ret = MotionControl.DeviceManager.TLI_GetDeviceListByTypesExt(buffer, n, ids, len(device_ids))
        if ret != 0:
            raise ConnectionError('Error getting device list for {}'.format(device_ids))
        return [sn for sn in buffer.value.decode().split(',') if sn]

    @staticmethod
    def get_device_info(serial_number):
        """
        Get the device information from the USB port.
    
        The device info is read from the USB port not from the device itself.
    
        Args:
            serial_number (str): The serial number of the device.
    
        Returns:
            :class:`.structs.TLI_DeviceInfo`: A DeviceInfo object.

        Raises:
            ConnectionError: If there was an error getting the device info. 
        """
        info = TLI_DeviceInfo()
        ret = MotionControl.DeviceManager.TLI_GetDeviceInfo(str(serial_number).encode(), byref(info))
        if ret == 0:
            raise ConnectionError('Error getting device info for {}'.format(serial_number))
        return info

    @staticmethod
    def to_version(dword):
        """
        Convert the firmware or software number (made up of 4 byte parts) to a string representation.
        
        See, get_firmware_version() or get_software_version() of the device class.
        
        Args:
            dword (int): The firmware or software number.

        Returns:
            :py:class:`str`: The string representation of the version number.
        """
        first = (dword >> 24) & 0xff
        second = (dword >> 16) & 0xff
        third = (dword >> 8) & 0xff
        fourth = dword & 0xff
        return '{}.{}.{}.{}'.format(first, second, third, fourth)

    @staticmethod
    def convert_message(msg_type, msg_id, msg_data):
        """
        Converts the message into a string representation.
        
        Args:
            msg_type (int): The message type defines the device type which raised the message.
            msg_id (int): The message ID for the ``message type``. 
            msg_data (int): The message data.

        Returns:
            :py:class:`str`: The message as a string.
        """
        _type = MessageTypes[msg_type]
        _id = MessageID[_type][msg_id]
        return 'Type:{}; ID:{}; Data:{}'.format(_type, _id, msg_data)

