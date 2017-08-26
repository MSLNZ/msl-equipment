.. _resources:

=============
MSL Resources
=============
MSL Resources are specific classes that are used to communicate with the equipment.

The following classes are available to use as the **PythonClassName** when defining the :ref:`address_syntax`
in a :ref:`connection_database`. For example, to specify the :class:`~msl.equipment.resources.bentham.benhw64.Bentham`
resource class, which is a wrapper around the ``benhw32_cdecl.dll`` SDK that is provided by the manufacturer, the
**Address** field should be ``SDK::Bentham::benhw32_cdecl.dll``.

.. tip::

   The **PythonClassName** can sometimes be omitted from the **Address** field in the :ref:`connection_database`
   if the MSL Resource class name and the module and package names that the class is located in have a very specific
   name format. When the :meth:`~msl.equipment.record_types.EquipmentRecord.connect` method is called the
   :func:`~msl.equipment.resources.check_manufacture_model_resource_name` function will attempt to automatically
   find the appropriate MSL Resource class to use for the :class:`~msl.equipment.record_types.EquipmentRecord`
   connection. If a MSL Resource class cannot be found then either a generic
   :class:`~msl.equipment.connection.Connection` subclass will be used to communicate with the equipment or an
   exception will be raised. It is recommended to include the **PythonClassName** in the **Address** field if you
   know that a MSL Resource class exists for the :class:`~msl.equipment.record_types.EquipmentRecord`, but it is
   not mandatory.

* `Bentham Instruments Ltd`_

  * :class:`~msl.equipment.resources.bentham.benhw64.Bentham` - The benhw32_ library

* CMI_ (Czech Metrology Institute)

  * :class:`~msl.equipment.resources.cmi.sia3.SIA3` - Switched Integrator Amplifier

* `Pico Technology`_

  * PicoScope_ - Requires the `Pico Technology SDK`_

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

  * :class:`~msl.equipment.resources.thorlabs.fwxx2c.FilterWheelXX2C` - FW102C, FW212C

.. _new_resource:

Creating a new MSL Resource
---------------------------
When adding a new MSL Resource class the following steps should be performed. Please follow the `style guide`_.

1. Create a fork_ of the repository_.
2. If you are adding a new MSL Resource for equipment from a manufacturer that does not already exist in the
   **msl.equipment.resources** package then create a new Python package in **msl.equipment.resources** using the name
   of the manufacturer as the package name (use lower-case letters and, if necessary, replace whitespace with an
   underscore). If the name of the manufacturer already exists as a package then skip this step.
3. Create a new Python module in the package from step 2. If it is possible, use the model number of the equipment as
   the module name (use lower case). Using this module-naming convention might not be possible if the model number
   contains characters that cannot be used to name Python modules. Either remove these characters when naming the module
   or use your own judgement for what to name the module.
4. Create a new class within the module that you created in step 3. The class must be a subclass of one of the MSL
   :ref:`connection_classes`. If possible, the name of the class should also be the model number of the equipment
   (as it would be written in a :ref:`equipment_database` and a :ref:`connection_database`). Again, use your own
   judgement for what to name the class if the model number contains invalid characters for naming a Python class.
   Write the properties and methods for the class to be able to communicate with the equipment.
5. Add at least one example for how to use the new MSL Resource in **msl.examples.equipment**. Follow the template of
   the other examples in the **msl.examples.equipment** package for naming conventions and for showing how to use the
   new MSL Resource.
6. Create tests for the new MSL Resource. The tests cannot be dependent on whether the equipment is physically
   connected to the computer running the test (ideally the examples that you write in step 5 will demonstrate that
   communicating with the equipment works). See the **tests/resources** folder to see what tests other MSL
   Resource classes are performing. You can run the tests using ``python setup.py test``.
7. Add **.rst** documentation files for the new MSL Resource to the **docs/_api** folder. You can either run
   ``python setup.py apidoc`` to auto-generate the **.rst** documentation files or you can create the necessary
   **.rst** files manually. Running ``apidoc`` will generate **.rst** files for *ALL* modules in **MSL-Equipment**.
   Within the **docs/_autosummary** folder, that gets automatically created when running the ``apidoc`` command, only
   copy the **.rst** files that are associated with your new MSL Resource to the **docs/_api** folder. After copying
   the files you can delete the **docs/_autosummary** folder before running ``python setup.py docs`` to build the
   documentation, otherwise you will get numerous warnings. If you want to manually create the **.rst** files then
   look in the **docs/_api** folder for examples from other MSL Resources.
8. Add the new package to the **toctree** of the **Subpackages** section in **docs/_api/msl.equipment.resources.rst**,
   only if you needed to create a new package in step 2. Insert the name of the new MSL Resource package in the file
   alphabetically based on the package name. If you forget to do this step then a warning will appear when building
   the documentation to help remind you to do it.
9. Specify that the new MSL Resource class now exists for everyone to use in **docs/resources.rst**. Follow the
   template that is used for the other MSL Resources listed in this file.
10. Create a `pull request`_.

.. _style guide: http://msl-package-manager.readthedocs.io/en/latest/developers_guide.html#edit-the-source-code-using-the-style-guide
.. _fork: https://help.github.com/articles/fork-a-repo/
.. _repository: https://github.com/MSLNZ/msl-equipment
.. _pull request: https://help.github.com/articles/creating-a-pull-request-from-a-fork/

.. _Bentham Instruments Ltd: https://www.bentham.co.uk/
.. _CMI: https://www.cmi.cz/?language=en
.. _Pico Technology: https://www.picotech.com/
.. _Thorlabs: https://www.thorlabs.com/

.. _benhw32: http://support.bentham.co.uk/support/solutions/articles/5000615653-sdk-manual
.. _Kinesis: https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
.. _Pico Technology SDK: https://www.picotech.com/downloads
.. _PicoScope: https://www.picotech.com/products/oscilloscope
