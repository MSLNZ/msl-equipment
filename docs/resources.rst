.. _resources:

MSL Resources
=============
MSL resources that are available for establishing a connection to equipment.

SDK Wrapper Classes
-------------------
The following classes, which are a wrapper around the Software Development Kit (SDK) provided
by the manufacturer, are available to use when defining the **Address** field in a **Connections**
database.

The format of an **Address** is ``SDK::PythonClassName::PathToLibrary`` where ``PathToLibrary``
is the full path to the SDK file (or only the filename if the library path is available on
:obj:`os.environ['PATH'] <os.environ>`, see :obj:`~msl.equipment.config.Config` for more details)
and ``PythonClassName`` can be one of the following classes.

For example, the **Address** field for equipment from **Bentham Instruments Ltd** can be
``SDK::Bentham::benhw32_cdecl.dll``.

* Bentham Instruments Ltd

  * :class:`~msl.equipment.resources.bentham.benhw64.Bentham` - The benhw32_ library

* Pico Technology

  * PicoScope_

    * :class:`~msl.equipment.resources.picotech.picoscope.ps2000.PicoScope2000` - ps2000
    * :class:`~msl.equipment.resources.picotech.picoscope.ps2000a.PicoScope2000A` - ps2000a
    * :class:`~msl.equipment.resources.picotech.picoscope.ps3000.PicoScope3000` - ps3000
    * :class:`~msl.equipment.resources.picotech.picoscope.ps3000a.PicoScope3000A` - ps3000a
    * :class:`~msl.equipment.resources.picotech.picoscope.ps4000.PicoScope4000` - ps4000
    * :class:`~msl.equipment.resources.picotech.picoscope.ps4000a.PicoScope4000A` - ps4000a
    * :class:`~msl.equipment.resources.picotech.picoscope.ps5000.PicoScope5000` - ps5000
    * :class:`~msl.equipment.resources.picotech.picoscope.ps5000a.PicoScope5000A` - ps5000a
    * :class:`~msl.equipment.resources.picotech.picoscope.ps6000.PicoScope6000` - ps6000

* Thorlabs

  * Kinesis_ - Wrapper package around ``Thorlabs.MotionControl.C_API``.

    * :class:`~msl.equipment.resources.thorlabs.kinesis.filter_flipper.FilterFlipper` - MFF101, MFF102
    * :class:`~msl.equipment.resources.thorlabs.kinesis.integrated_stepper_motors.IntegratedStepperMotors` - LTS150, LTS300, MLJ050, K10CR1
    * :class:`~msl.equipment.resources.thorlabs.kinesis.kcube_solenoid.KCubeSolenoid` - KSC101

  * :class:`~msl.equipment.resources.thorlabs.fw102c.FilterWheel102C` - FW102C, FW212C

.. _benhw32: http://support.bentham.co.uk/support/solutions/articles/5000615653-sdk-manual
.. _PicoScope: https://www.picotech.com/downloads
.. _Kinesis: https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
