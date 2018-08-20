"""
Encapsulate some of the commands to communicate with a Digital Multimeter.
"""
import re

_curly = re.compile(r'{.*}')


class _DMM1(object):
    models = ('34465A',)
    commands = {
        'voltage': 'MEASURE:VOLTAGE:{ACDC}? [{RANGE}[,{RESOLUTION}]]',
    }


class _DMM2(object):
    models = ('3458A',)
    commands = {
        'voltage': 'FUNC {ACDC}V[,{RANGE}[,{RESOLUTION}]]',
    }


def dmm_factory(connection_record, connection_class):
    """Returns a class that encapsulates some of the commands to communicate with a Digital Multimeter.

    *To add a DMM to the list of supported DMM's see the source code of this module to follow the template.*

    This function is not meant to be called directly. Use the :meth:`~.EquipmentRecord.connect`
    method to connect to the equipment.

    Parameters
    ----------
    connection_record : :class:`~.record_types.ConnectionRecord`
        A connection record from a :ref:`connections_database`.
    connection_class : :class:`~.connection_message_based.ConnectionMessageBased` or :class:`~pyvisa.resources.MessageBasedResource`
        A connection subclass that communicates with the equipment through `read` and `write` commands.

    Returns
    -------
    :class:`~.connection.Connection`
        The `connection_class` that was passed in with additional methods for communicating with the DMM, provided
        that the model number of the DMM is one of the DMM's that is supported. Otherwise returns the original,
        unmodified `connection_class` object.
    """
    class DMM(connection_class):

        def __init__(self, record):
            """Base class for all supported Digital Multimeter's.

            Parameters
            ----------
            record : :class:`~.record_types.EquipmentRecord`
                A record from an :ref:`equipment_database`.
            """
            super(DMM, self).__init__(record)

        def _cmd(self, key, **kwargs):
            """Parse a formatted command string to construct the command message.

            Parameters
            ----------
            key : :class:`str`
                A key in the `commands` dictionary.
            kwargs
                The keyword arguments to do a "find and replace" in the formatted command string.

            Returns
            -------
            :class:`str`
                The command message to send to the equipment.
            """
            cmd = ''
            for item in self.commands[key].split('['):
                text = re.search(_curly, item)
                if text is None:
                    cmd += item
                    break
                curly = text.group()
                value = kwargs[curly[1:-1]]
                if value is None:
                    break
                cmd += re.sub(curly, str(value), item)
            cmd = cmd.replace(']', '').rstrip()
            self.log_debug('{} -> {}'.format(self, cmd))
            return cmd

        def voltage_dc(self, range=None, resolution=None):
            cmd = self._cmd('voltage', ACDC='DC', RANGE=range, RESOLUTION=resolution)
            return float(self.query(cmd))

        def voltage_ac(self, range=None, resolution=None):
            cmd = self._cmd('voltage', ACDC='AC', RANGE=range, RESOLUTION=resolution)
            return float(self.query(cmd))

    #
    # return the _DMM# class that this model number belongs to
    #
    for cls in (_DMM1, _DMM2):
        if connection_record.model in cls.models:
            dmm = DMM
            dmm.commands = cls.commands
            return dmm
    return connection_class
