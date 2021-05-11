.. _equipment-install:

=====================
Install MSL-Equipment
=====================

To install **MSL-Equipment** run

.. code-block:: console

   pip install https://github.com/MSLNZ/msl-equipment/archive/main.zip

Alternatively, using the `MSL Package Manager`_ run

.. code-block:: console

   msl install equipment

.. _equipment-dependencies:

Dependencies
------------
* Python 2.7, 3.5+
* msl-loadlib_
* msl-io_
* numpy_
* pyserial_
* python-dateutil_

Optional Dependencies
---------------------
* PyVISA_
* PyVISA-py_
* NI-DAQmx_

Some of the :ref:`equipment-resources` might not work in your application
because the resource might depend on an external dependency (e.g., the SDK
provided by a manufacturer) and this external dependency might not be
available for your operating system.

.. _MSL Package Manager: https://msl-package-manager.readthedocs.io/en/latest/
.. _PyVISA: https://pyvisa.readthedocs.io/en/latest/
.. _PyVISA-py: https://pyvisa-py.readthedocs.io/en/latest/
.. _NI-DAQmx: https://nidaqmx-python.readthedocs.io/en/latest/
.. _numpy: https://www.numpy.org/
.. _msl-loadlib: https://msl-loadlib.readthedocs.io/en/latest/
.. _msl-io: https://msl-io.readthedocs.io/en/latest/
.. _pyserial: https://pythonhosted.org/pyserial/
.. _python-dateutil: https://dateutil.readthedocs.io/en/latest/
