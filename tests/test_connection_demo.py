from msl.equipment.connection import Connection
from msl.equipment.connection_demo import ConnectionDemo
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.resources.picotech.picoscope.picoscope import PicoScope
from msl.equipment.resources.picotech.picoscope.channel import PicoScopeChannel


class MyConnection(Connection):

    def __init__(self, record):
        super(MyConnection, self).__init__(record)

    def get_none1(self):
        """No return type is specified."""
        pass

    def get_none2(self, channel):
        """This function takes 1 input but returns nothing.

        Parameters
        ----------
        channel : :obj:`str`
            Some channel number
        """
        pass

    def get_bool1(self):
        """:obj:`bool`: A boolean value."""
        pass

    def get_bool2(self):
        """Returns a boolean value.

        Returns
        -------
        :obj:`bool`
            A boolean value.
        """
        pass

    def get_string1(self):
        """:obj:`str`: A string value."""
        pass

    def get_string2(self):
        """Returns a string value.

        Returns
        -------
        :obj:`str`
            A string value.
        """
        pass

    def get_bytes1(self):
        """:obj:`bytes`: A bytes value."""
        pass

    def get_bytes2(self):
        """Returns a bytes value.

        Returns
        -------
        :obj:`bytes`
            A bytes value.
        """
        pass

    def get_int1(self):
        """:obj:`int`: An integer value."""
        pass

    def get_int2(self):
        """Returns an integer value.

        Returns
        -------
        :obj:`int`
            An integer value.
        """
        pass

    def get_float1(self):
        """:obj:`float`: A floating-point value."""
        pass

    def get_float2(self):
        """Returns a floating-point value.

        Returns
        -------
        :obj:`float`
            A floating-point value.
        """
        pass

    def get_list_of_bool1(self):
        """:obj:`list` of :obj:`bool`: A list of boolean values."""
        pass

    def get_list_of_bool2(self):
        """A list of boolean values.

        Returns
        -------
        :obj:`list` of :obj:`bool`
            A list of boolean values.
        """
        pass

    def get_list_of_str1(self):
        """:obj:`list` of :obj:`str`: A list of string values."""
        pass

    def get_list_of_str2(self):
        """A list of string values.

        Returns
        -------
        :obj:`list` of :obj:`str`
            A list of string values.
        """
        pass

    def get_list_of_bytes1(self):
        """:obj:`list` of :obj:`bytes`: A list of bytes values."""
        pass

    def get_list_of_bytes2(self):
        """A list of bytes values.

        Returns
        -------
        :obj:`list` of :obj:`bytes`
            A list of bytes values.
        """
        pass

    def get_list_of_int1(self):
        """:obj:`list` of :obj:`int`: A list of integer values."""
        pass

    def get_list_of_int2(self):
        """A list of integer values.

        Returns
        -------
        :obj:`list` of :obj:`int`
            A list of integer values.
        """
        pass

    def get_list_of_float1(self):
        """:obj:`list` of :obj:`float`: A list of floating-point values."""
        pass

    def get_list_of_float2(self):
        """A list of floating-point values.

        Returns
        -------
        :obj:`list` of :obj:`float`
            A list of floating-point values.
        """
        pass

    def get_dict_of_bool1(self):
        """:obj:`dict` of :obj:`bool`: A dictionary of boolean values."""
        pass

    def get_dict_of_bool2(self):
        """A dictionary of boolean values.

        Returns
        -------
        :obj:`dict` of :obj:`bool`
            A dictionary of boolean values.
        """
        pass

    def get_dict_of_str1(self):
        """:obj:`dict` of :obj:`str`: A dictionary of string values."""
        pass

    def get_dict_of_str2(self):
        """A dictionary of string values.

        Returns
        -------
        :obj:`dict` of :obj:`str`
            A dictionary of string values.
        """
        pass

    def get_dict_of_bytes1(self):
        """:obj:`dict` of :obj:`bytes`: A dictionary of bytes values."""
        pass

    def get_dict_of_bytes2(self):
        """A dictionary of bytes values.

        Returns
        -------
        :obj:`dict` of :obj:`bytes`
            A dictionary of bytes values.
        """
        pass

    def get_dict_of_int1(self):
        """:obj:`dict` of :obj:`int`: A dictionary of integer values."""
        pass

    def get_dict_of_int2(self):
        """A dictionary of integer values.

        Returns
        -------
        :obj:`dict` of :obj:`int`
            A dictionary of integer values.
        """
        pass

    def get_dict_of_float1(self):
        """:obj:`dict` of :obj:`float`: A dictionary of floating-point values."""
        pass

    def get_dict_of_float2(self):
        """A dictionary of floating-point values.

        Returns
        -------
        :obj:`dict` of :obj:`float`
            A dictionary of floating-point values.
        """
        pass

    def get_multiple1(self):
        """Many different data types.

        Returns
        -------
        :obj:`str`
            A string value.
        :obj:`float`
            A floating-point value.
        :obj:`float`
            A floating-point value.
        :obj:`dict` of :obj:`int`
            A dictionary of integer values.
        :obj:`bytes`
            A bytes value.
        """
        pass


def test_return_type_builtin():
    demo = ConnectionDemo(EquipmentRecord(), MyConnection)

    assert demo.get_none1() is None
    assert demo.get_none2() is None

    assert isinstance(demo.get_bool1(), bool)
    assert isinstance(demo.get_bool2(), bool)

    assert isinstance(demo.get_string1(), str)
    assert isinstance(demo.get_string2(), str)

    assert isinstance(demo.get_bytes1(), bytes)
    assert isinstance(demo.get_bytes2(), bytes)

    assert isinstance(demo.get_int1(), int)
    assert isinstance(demo.get_int2(), int)

    assert isinstance(demo.get_float1(), float)
    assert isinstance(demo.get_float2(), float)

    x = demo.get_list_of_bool1()
    assert isinstance(x, list) and isinstance(x[0], bool)

    x = demo.get_list_of_bool2()
    assert isinstance(x, list) and isinstance(x[0], bool)

    x = demo.get_list_of_str1()
    assert isinstance(x, list) and isinstance(x[0], str)

    x = demo.get_list_of_str2()
    assert isinstance(x, list) and isinstance(x[0], str)

    x = demo.get_list_of_bytes1()
    assert isinstance(x, list) and isinstance(x[0], bytes)

    x = demo.get_list_of_bytes2()
    assert isinstance(x, list) and isinstance(x[0], bytes)

    x = demo.get_list_of_int1()
    assert isinstance(x, list) and isinstance(x[0], int)

    x = demo.get_list_of_int2()
    assert isinstance(x, list) and isinstance(x[0], int)

    x = demo.get_list_of_float1()
    assert isinstance(x, list) and isinstance(x[0], float)

    x = demo.get_list_of_float2()
    assert isinstance(x, list) and isinstance(x[0], float)

    x = demo.get_dict_of_bool1()
    assert isinstance(x, dict) and isinstance(x['demo'], bool)

    x = demo.get_dict_of_bool2()
    assert isinstance(x, dict) and isinstance(x['demo'], bool)

    x = demo.get_dict_of_str1()
    assert isinstance(x, dict) and isinstance(x['demo'], str)

    x = demo.get_dict_of_str2()
    assert isinstance(x, dict) and isinstance(x['demo'], str)

    x = demo.get_dict_of_bytes1()
    assert isinstance(x, dict) and isinstance(x['demo'], bytes)

    x = demo.get_dict_of_bytes2()
    assert isinstance(x, dict) and isinstance(x['demo'], bytes)

    x = demo.get_dict_of_int1()
    assert isinstance(x, dict) and isinstance(x['demo'], int)

    x = demo.get_dict_of_int2()
    assert isinstance(x, dict) and isinstance(x['demo'], int)

    x = demo.get_dict_of_float1()
    assert isinstance(x, dict) and isinstance(x['demo'], float)

    x = demo.get_dict_of_float2()
    assert isinstance(x, dict) and isinstance(x['demo'], float)

    x = demo.get_multiple1()
    assert len(x) == 5
    assert isinstance(x[0], str)
    assert isinstance(x[1], float)
    assert isinstance(x[2], float)
    assert isinstance(x[3], dict) and isinstance(x[3]['demo'], int)
    assert isinstance(x[4], bytes)


def test_return_type_object():
    scope = ConnectionDemo(EquipmentRecord(), PicoScope)

    x = scope.channel()
    assert isinstance(x, dict) and x['demo'] == PicoScopeChannel
