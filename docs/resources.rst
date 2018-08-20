.. _msl-resources:

=============
MSL Resources
=============
MSL Resources are specific classes that are used to communicate with the equipment.

* `Bentham Instruments Ltd`_

  * :class:`~msl.equipment.resources.bentham.benhw64.Bentham` - The benhw32_ library

* CMI_ (Czech Metrology Institute)

  * :class:`~msl.equipment.resources.cmi.sia3.SIA3` - Switched Integrator Amplifier

* OMEGA_

  * :class:`~msl.equipment.resources.omega.ithx.iTHX` - iTHX-W3, iTHX-D3, iTHX-SD, iTHX-M, iTHX-W, iTHX-2

* OptoSigma_

  * :class:`~msl.equipment.resources.optosigma.shot702.SHOT702` - Two-axis Stage Controller

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
    * :class:`~msl.equipment.resources.thorlabs.kinesis.integrated_stepper_motors.IntegratedStepperMotors` - LTS150, LTS300, MLJ050, MLJ150, K10CR1
    * :class:`~msl.equipment.resources.thorlabs.kinesis.kcube_solenoid.KCubeSolenoid` - KSC101
    * :class:`~msl.equipment.resources.thorlabs.kinesis.kcube_stepper_motor.KCubeStepperMotor` - KST101
    * :class:`~msl.equipment.resources.thorlabs.kinesis.kcube_dc_servo.KCubeDCServo` - KDC101
    * :class:`~msl.equipment.resources.thorlabs.kinesis.benchtop_stepper_motor.BenchtopStepperMotor` - BSC101, BSC102, BSC103, BSC201, BSC202, BSC203

  * :class:`~msl.equipment.resources.thorlabs.fwxx2c.FilterWheelXX2C` - FW102C, FW212C

.. _new_resource:

Creating a new MSL Resource
---------------------------
When adding a new MSL Resource class to the repository_ the following steps should be performed.
Please follow the `style guide`_.

.. note::
   If you do not want to upload the new MSL Resource class to the repository_ then you
   only need to write the code found in Step 5 to use your class in your own programs.

1. Create a fork_ of the repository_.
2. If you are adding a new MSL Resource for equipment from a manufacturer that does not already exist in the
   `msl/equipment/resources`_ directory then create a new Python package in `msl/equipment/resources`_ using the name
   of the *manufacturer* as the package name.
3. Create a new Python module, in the package from Step 2, using the *model number* of the equipment as the name
   of the module.
4. If a :mod:`msl.equipment.exceptions` class has not been created for this manufacture then create a new
   exception handler class using the name of the *manufacturer* in the class name.
5. Create a new connection class within the module that you created in Step 3. The class must be a subclass of one of
   the :ref:`connection_classes`.

   .. code-block:: python

        # msl/equipment/resources/<manufacturer>/<model_number>.py
        #
        from msl.equipment.resources import register
        from msl.equipment.exceptions import TheErrorClassFromStep4  # this is optional
        from msl.equipment.connection_xxx import ConnectionXxx  # replace xxx with the Connection subclass

        # Register your class so that MSL-Equipment knows that it exists
        @register(manufacturer='a regex pattern', model='a regex pattern')  # can include a `flags` kwarg
        class ModelNumber(ConnectionXxx):  # change ModelNumber and ConnectionXxx

            def __init__(self, record):
                """Edit the docstring...

                Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
                method to connect to the equipment.

                Parameters
                ----------
                record : :class:`~.EquipmentRecord`
                    A record from an :ref:`equipment_database`.
                """
                super(ModelNumber, self).__init__(record)  # change ModelNumber

                # the following is optional, the default exception handler is MSLConnectionError
                self.set_exception_class(TheErrorClassFromStep4)  # change TheErrorClassFromStep4

6. Add at least one example for how to use the new MSL Resource in `msl/examples/equipment/resources`_.
   Follow the template of the other examples in this package for naming conventions and for showing how to use the
   new MSL Resource.
7. Create tests for the new MSL Resource. The tests cannot be dependent on whether the equipment is physically
   connected to the computer running the test (ideally the examples that you write in Step 6 will demonstrate that
   communicating with the equipment works). The very minimal test to create is to add a test case to the
   `def test_find_resource_class()`_ function for ensuring that your class is returned for various values of
   *manufacturer* and *model*. Run the tests using ``python setup.py test`` (ideally you would run the tests
   for all :ref:`currently-supported versions <equip-dependencies>` of Python, see also `test_envs.py`_).
8. Add ``*.rst`` documentation files for the new MSL Resource to the `docs/_api`_ folder. You can either run
   ``python setup.py apidoc`` to automatically generate the ``*.rst`` documentation files or you can create the
   necessary ``*.rst`` files manually. Running ``python setup.py apidoc`` will generate ``*.rst`` files for *all*
   modules in **MSL-Equipment** in the ``docs/_autosummary`` folder. Only copy the ``*.rst`` files that are associated
   with your new MSL Resource to the `docs/_api`_ folder. After copying the files you can delete the
   ``docs/_autosummary`` folder before running ``python setup.py docs`` to build the documentation, otherwise you will
   get numerous warnings. If you want to manually create the ``*.rst`` files then look in the `docs/_api`_ folder for
   examples from other MSL Resources.
9. If you created a new package in Step 2 then you need to add the new package to the ``toctree`` of the
   ``Subpackages`` section in `docs/_api/msl.equipment.resources.rst`_. Insert the name of the new MSL Resource
   package in the file alphabetically. If you forget to do this step then a warning will appear when building
   the documentation to help remind you to do it.
10. Add the new MSL Resource class, alphabetically, to the list of MSL Resources in `docs/resources.rst`_. Follow the
    template that is used for the other MSL Resources listed in this file.
11. Add yourself to ``AUTHORS.rst`` and add a note in ``CHANGES.rst`` that you created this new Resource. These files
    are located in the root directory of the **MSL-Equipment** package.
12. If running the tests pass and building the docs show no errors/warnings then create a `pull request`_.

.. _style guide: http://msl-package-manager.readthedocs.io/en/latest/developers_guide.html#edit-the-source-code-using-the-style-guide
.. _fork: https://help.github.com/articles/fork-a-repo/
.. _repository: https://github.com/MSLNZ/msl-equipment
.. _msl/equipment/resources: https://github.com/MSLNZ/msl-equipment/tree/master/msl/equipment/resources
.. _msl/examples/equipment/resources: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/resources
.. _def test_find_resource_class(): https://github.com/MSLNZ/msl-equipment/blob/master/tests/resources/test_init.py
.. _test_envs.py: https://msl-package-manager.readthedocs.io/en/latest/new_package_readme.html#test-envs-py-commands
.. _docs/_api: https://github.com/MSLNZ/msl-equipment/tree/master/docs/_api
.. _docs/_api/msl.equipment.resources.rst: https://github.com/MSLNZ/msl-equipment/blob/master/docs/_api/msl.equipment.resources.rst
.. _docs/resources.rst: https://github.com/MSLNZ/msl-equipment/blob/master/docs/resources.rst
.. _pull request: https://help.github.com/articles/creating-a-pull-request-from-a-fork/

.. _Bentham Instruments Ltd: https://www.bentham.co.uk/
.. _benhw32: http://support.bentham.co.uk/support/solutions/articles/5000615653-sdk-manual
.. _CMI: https://www.cmi.cz/?language=en
.. _Pico Technology: https://www.picotech.com/
.. _Thorlabs: https://www.thorlabs.com/
.. _Kinesis: https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
.. _Pico Technology SDK: https://www.picotech.com/downloads
.. _PicoScope: https://www.picotech.com/products/oscilloscope
.. _OMEGA: https://www.omega.com/
.. _OptoSigma: https://www.global-optosigma.com/en_jp/
