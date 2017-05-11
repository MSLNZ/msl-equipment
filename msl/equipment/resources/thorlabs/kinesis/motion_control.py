"""
Base **Thorlabs.MotionControl** class.
"""
from ctypes import c_int, byref, create_string_buffer
from ctypes.wintypes import WORD, DWORD

from msl.loadlib import LoadLibrary

from msl.equipment.connection_msl import ConnectionSDK
from .errors import ERROR_CODES, FT_OK
from .structs import TLI_DeviceInfo, TLI_HardwareInformation
from .messages import MessageTypes, MessageID

_motion_control_device_manager = None


def device_manager(root_path='C:/Program Files/Thorlabs/Kinesis'):
    """Returns a reference to the DeviceManager library. 
    
    Parameters
    ----------
    root_path : :obj:`str`
        The path to the Thorlabs.MotionControl.DeviceManager.dll library.

    Returns
    -------
    :class:`ctypes.CDLL`
        A reference to the library.
    """
    global _motion_control_device_manager
    if _motion_control_device_manager is None:
        import os
        path = os.path.join(root_path, 'Thorlabs.MotionControl.DeviceManager.dll')
        _motion_control_device_manager = LoadLibrary(path).lib
    return _motion_control_device_manager


class MotionControl(ConnectionSDK):

    Benchtop_Brushless_Motor = 73  #: Benchtop Brushless Motor device ID
    Benchtop_NanoTrak = 22  #: Benchtop NanoTrak device ID
    Benchtop_Piezo_1_Channel = 41  #: Benchtop Piezo 1-Channel device ID
    Benchtop_Piezo_3_Channel = 71  #: Benchtop Piezo 3-Channel device ID
    Benchtop_Stepper_Motor_1_Channel = 40  #: Benchtop Stepper Motor 1-Channel device ID
    Benchtop_Stepper_Motor_3_Channel = 70  #: Benchtop Stepper Motor 3-Channel device ID
    Filter_Flipper = 37  #: Filter Flipper device ID
    Filter_Wheel = 47  #: Filter Wheel device ID
    KCube_Brushless_Motor = 28  #: KCube Brushless Motor device ID
    KCube_DC_Servo = 27  #: KCube DC Servo device ID
    KCube_LaserSource = 56  #: KCube Laser Source device ID
    KCube_Piezo = 29  #: KCube Piezo device ID
    KCube_Solenoid = 68  #: KCube Solenoid device ID
    KCube_Stepper_Motor = 26  #: KCube Stepper Motor device ID
    Long_Travel_Stage = 45  #: Long Travel Stage device ID
    Cage_Rotator = 55  #: Cage Rotator device ID
    LabJack_490 = 46  #: LabJack 490 device ID
    LabJack_050 = 49  #: LabJack 050 device ID
    Modular_NanoTrak = 52  #: Modular NanoTrak device ID
    Modular_Piezo = 51  #: Modular Piezo device ID
    Modular_Stepper_Motor = 50  #: Modular Stepper Motor device ID
    TCube_Brushless_Motor = 67  #: TCube Brushless Motor device ID
    TCube_DC_Servo = 83  #: TCube DC Servo device ID
    TCube_Inertial_Motor = 65  #: TCube Inertial Motor device ID
    TCube_LaserSource = 86  #: TCube Laser Source device ID
    TCube_LaserDiode = 64  #: TCube Laser Diode device ID
    TCube_NanoTrak = 82  #: TCube NanoTrak device ID
    TCube_Quad = 89  #: TCube Quad device ID
    TCube_Solenoid = 85  #: TCube Solenoid device ID
    TCube_Stepper_Motor = 80  #: TCube Stepper_Motor device ID
    TCube_Strain_Gauge = 84  #: TCube Strain Gauge device ID
    TCube_TEC = 87  #: TCube TEC device ID

    # a serial number is 8 characters, 1 for null terminated, 1 for the comma, allow for up to 50 devices
    SERIAL_NUMBER_BUFFER_SIZE = (8 + 1 + 1) * 50

    def __init__(self, record, api_function):
        """
        Base **Thorlabs.MotionControl** class.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~msl.equipment.database.Database`.
        api_function : :mod:`.api_functions` 
            An API function list from :mod:`.api_functions` that the subclass 
            is a wrapper around.
            
        Raises
        ------
        ConnectionError
            If a connection to the device cannot be established.
        """
        self._is_open = False
        ConnectionSDK.__init__(self, record, 'cdll')

        for item in api_function:
            func = getattr(self.sdk, item[0])
            func.restype = item[1]
            func.errcheck = getattr(self, item[2])
            func.argtypes = [v[0] for v in item[3]]

        self._serial = record.serial.encode()
        self.build_device_list()
        self.open()
        self._is_open = True

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
        """Disconnect and close the device."""
        if self._is_open:
            self.close()
            self._is_open = False

    @staticmethod
    def build_device_list():
        """Build the device list. 
    
        This function builds an internal collection of all devices found on a 
        USB port that are not currently open.
         
        Note
        ----
        If a device is open, it will not appear in the list until the device 
        has been closed.
        
        Raises
        ------
        ConnectionError
            If the device list cannot be built. 
        """
        ret = device_manager().TLI_BuildDeviceList()
        if ret != 0:
            raise ConnectionError('Error building device list')
        return ret

    @staticmethod
    def get_device_list_size():
        """:obj:`int`: The number of devices in the device list."""
        return device_manager().TLI_GetDeviceListSize()

    @staticmethod
    def get_device_list(*device_ids):
        """Get the contents of the device list which match the supplied device IDs.
    
        Parameters
        ----------
        device_ids : :obj:`int`
            A sequence of device ID's.
    
        Returns
        -------
        :obj:`list` of :obj:`str`
            A list of device serial numbers for the specified device ID(s).

        Raises
        ------
        ConnectionError
            If there was an error getting the device list. 
        """
        n = MotionControl.SERIAL_NUMBER_BUFFER_SIZE
        buffer = create_string_buffer(n)
        ids = (c_int * len(device_ids))(*device_ids)
        if len(device_ids) == 0:
            ret = device_manager().TLI_GetDeviceListExt(buffer, n)
        else:
            ret = device_manager().TLI_GetDeviceListByTypesExt(buffer, n, ids, len(device_ids))
        if ret != 0:
            raise ConnectionError('Error getting device list for {}'.format(device_ids))
        return [sn for sn in buffer.value.decode().split(',') if sn]

    @staticmethod
    def get_device_info(serial_number):
        """Get the device information from a USB port.
    
        The device info is read from the USB port not from the device itself.
    
        Parameters
        ----------
        serial_number : :obj:`str`
            The serial number of the device.
    
        Returns
        -------
        :class:`.structs.TLI_DeviceInfo`
            A DeviceInfo structure.

        Raises
        ------
        ConnectionError
            If there was an error getting the device information. 
        """
        info = TLI_DeviceInfo()
        ret = device_manager().TLI_GetDeviceInfo(str(serial_number).encode(), byref(info))
        if ret == 0:
            raise ConnectionError('Error getting device info for {}'.format(serial_number))
        return info

    @staticmethod
    def to_version(dword):
        """Convert the firmware or software number to a string.
        
        The number is made up of 4-byte parts.
        
        See the *get_firmware_version()* or the *get_software_version()* method 
        of the appropriate Thorlabs MotionControl subclass.
        
        Parameters
        ----------
        dword : :obj:`int`
            The firmware or software number.

        Returns
        -------
        :obj:`str`
            The string representation of the version number.
        """
        first = (dword >> 24) & 0xff
        second = (dword >> 16) & 0xff
        third = (dword >> 8) & 0xff
        fourth = dword & 0xff
        return '{}.{}.{}.{}'.format(first, second, third, fourth)

    @staticmethod
    def convert_message(msg_type, msg_id, msg_data):
        """Converts the message into a string representation.

        See the *get_next_message()* or the *wait_for_message()* method of 
        the appropriate Thorlabs MotionControl subclass.
        
        Parameters
        ----------
        msg_type : :obj:`int`
            The message type defines the device type which raised the message.
        msg_id : :obj:`int`
            The message ID for the `msg_type`. 
        msg_data : :obj:`int`
            The message data.

        Returns
        -------
        :obj:`str`
            The message as a string, with the type, id and data separated 
            by a semicolon.
        """
        _type = MessageTypes[msg_type]
        _id = MessageID[_type][msg_id]
        return 'Type:{}; ID:{}; Data:{}'.format(_type, _id, msg_data)

    def _get_hardware_info(self, sdk_function):
        """Gets the hardware information from the device.
        
        The SDK function signature must be
                
        sdk_function(char const * serialNo, char * modelNo, DWORD sizeOfModelNo, WORD * type, WORD * numChannels, 
        char * notes, DWORD sizeOfNotes, DWORD * firmwareVersion, WORD * hardwareVersion, WORD * modificationState);

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

        sdk_function(self._serial, model, model_size, byref(typ), byref(num_channels),
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
