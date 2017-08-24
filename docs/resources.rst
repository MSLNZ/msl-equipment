.. _resources:

=============
MSL Resources
=============
MSL resource are used to control equipment.

The following classes are available to use as the **PythonClassName** when defining the :ref:`address_syntax`
in a :ref:`connection_database`. For example, to use the ``benhw32_cdecl.dll`` SDK that is provided from
**Bentham Instruments Ltd** the **Address** value should be ``SDK::Bentham::benhw32_cdecl.dll``.

* `Bentham Instruments Ltd`_

  * :class:`~msl.equipment.resources.bentham.benhw64.Bentham` - The benhw32_ library

* CMI_ (Czech Metrology Institute)

  * :class:`~msl.equipment.resources.cmi.sia3.SIA3` - Switched Integrator Amplifier

* `Pico Technology`_

  * PicoScope_

    * :class:`~msl.equipment.resources.picotech.picoscope.ps2000.PicoScope2000` - PicoScope 2000 Series
    * :class:`~msl.equipment.resources.picotech.picoscope.ps2000a.PicoScope2000A` - PicoScope 2000 Series A
    * :class:`~msl.equipment.resources.picotech.picoscope.ps3000.PicoScope3000` - PicoScope 3000 Series
    * :class:`~msl.equipment.resources.picotech.picoscope.ps3000a.PicoScope3000A` - PicoScope 3000 Series A
    * :class:`~msl.equipment.resources.picotech.picoscope.ps4000.PicoScope4000` - PicoScope 4000 Series
    * :class:`~msl.equipment.resources.picotech.picoscope.ps4000a.PicoScope4000A` - PicoScope 4000 Series A
    * :class:`~msl.equipment.resources.picotech.picoscope.ps5000.PicoScope5000` - PicoScope 5000 Series
    * :class:`~msl.equipment.resources.picotech.picoscope.ps5000a.PicoScope5000A` - PicoScope 5000 Series A
    * :class:`~msl.equipment.resources.picotech.picoscope.ps6000.PicoScope6000` - PicoScope 6000 Series

* Thorlabs_

  * Kinesis_ - Wrapper package around the ``Thorlabs.MotionControl.C_API`` SDK.

    * :class:`~msl.equipment.resources.thorlabs.kinesis.filter_flipper.FilterFlipper` - MFF101, MFF102
    * :class:`~msl.equipment.resources.thorlabs.kinesis.integrated_stepper_motors.IntegratedStepperMotors` - LTS150, LTS300, MLJ050, K10CR1
    * :class:`~msl.equipment.resources.thorlabs.kinesis.kcube_solenoid.KCubeSolenoid` - KSC101

  * :class:`~msl.equipment.resources.thorlabs.fw102c.FilterWheel102C` - FW102C, FW212C

.. _new_resource:

Creating A New MSL Resource
---------------------------
When adding a new MSL resource class the following steps should be performed.

1. Create a new Python package in **msl.equipment.resources** with the name of the Manufacturer of the equipment
   as the package name (if the package folder does not already exist). Follow the structure of the resource packages
   already contained in the **msl.equipment.resources** package for guidance.
2. Create a new class within the package that you created in step 1. The class must be a subclass one of the a
   classes found in the :mod:`msl.equipment.connection_msl` module.
3. Run ``python setup.py apidoc`` to auto-generate the **.rst** documentation files.
4. Copy the newly-created **.rst** files from the **docs/_autosummary** folder to the **docs/_api** folder. Note that
   running ``python setup.py apidoc`` will generate **.rst** files for **ALL** modules in **MSL-Equipment**. Within the
   **docs/_autosummary** folder just copy the **.rst** files that are associated with your new package/class. You can
   delete the **docs/_autosummary** folder before running ``python setup.py docs`` otherwise you'll get numerous
   warnings when building the documentation.
5. Add the package to the the toctree in **docs/_api/msl.equipment.resources.rst**. If you forget to then a warning will
   occur when building the documentation.
6. Document that the resource class now exists for everyone to use in **docs/resources.rst**

.. _Bentham Instruments Ltd: https://www.bentham.co.uk/
.. _Pico Technology: https://www.picotech.com/
.. _CMI: https://www.cmi.cz/?language=en
.. _Thorlabs: https://www.thorlabs.com/

.. _benhw32: http://support.bentham.co.uk/support/solutions/articles/5000615653-sdk-manual
.. _PicoScope: https://www.picotech.com/downloads
.. _Kinesis: https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
