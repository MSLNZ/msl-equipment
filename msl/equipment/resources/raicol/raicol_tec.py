"""
Control a TEC (Peltier-based) oven from Raicol Crystals.
"""
from msl.equipment.resources import register
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import RaicolCrystalsError


@register(manufacturer=r'Raicol', model=r'TEC')
class RaicolTEC(ConnectionSerial):

    def __init__(self, record):
        """Control a TEC (Peltier-based) oven from Raicol Crystals.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(RaicolTEC, self).__init__(record)
        self.write_termination = self.LF
        self.set_exception_class(RaicolCrystalsError)

    def get_setpoint(self):
        """Get the setpoint temperature.

        Returns
        -------
        :class:`float`
            The setpoint temperature, in Celsius.
        """
        return float(self.query('Get_T_Set', size=6)[2:])

    def off(self):
        """Turn the TEC off."""
        reply = self.query('OFF', size=4)
        if reply != 'ofOK':
            self.raise_exception('Cannot turn the TEC off')

    def on(self):
        """Turn the TEC on."""
        reply = self.query('ON', size=4)
        if reply != 'onOK':
            self.raise_exception('Cannot turn the TEC on')

    def set_setpoint(self, temperature):
        """Set the setpoint temperature.

        Parameters
        ----------
        temperature : :class:`float`
            The setpoint temperature, in Celsius. Must be in the range [20.1, 60.0].
        """
        t = round(temperature, 1)
        if t < 20.1 or t > 60.0:
            raise ValueError('The setpoint temperature must be between '
                             '20.1 and 60.0, got {}'.format(t))

        reply = self.query('Set_T{:.1f}'.format(t), size=4, delay=0.05)
        if reply != 'stOK':
            self.raise_exception('Cannot change the setpoint temperature')

    def temperature(self):
        """Returns the current temperature of the oven.

        The temperature is measured by a PT1000-Platinum resistor temperature
        sensor that is located near the crystal in the metalic mount.

        Returns
        -------
        :class:`float`
            The temperature of the oven, in Celsius.
        """
        return float(self.query('Data_T', size=7)[2:])
