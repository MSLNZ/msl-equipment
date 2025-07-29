.. _equipment-install:

=====================
Install MSL-Equipment
=====================

To install MSL-Equipment run

.. code-block:: console

   pip install https://github.com/MSLNZ/msl-equipment/releases/download/v0.2.0/msl_equipment-0.2.0-py3-none-any.whl

Alternatively, using the `MSL Package Manager`_ run

.. code-block:: console

   msl install equipment

.. _equipment-dependencies:

Dependencies
------------
* Python 3.8+
* msl-loadlib_
* msl-io_
* numpy_
* pyserial_
* pyzmq_

Optional Dependencies
---------------------
* PyVISA_
* PyVISA-py_
* NI-DAQmx_

Some of the :ref:`equipment-resources` might not work in your application
because the resource might depend on an external dependency (e.g., the SDK
provided by a manufacturer) and this external dependency might not be
available for your operating system.

.. _MSL Package Manager: https://msl-package-manager.readthedocs.io/en/stable/
.. _PyVISA: https://pyvisa.readthedocs.io/en/stable/
.. _PyVISA-py: https://pyvisa-py.readthedocs.io/en/stable/
.. _NI-DAQmx: https://nidaqmx-python.readthedocs.io/en/stable/
.. _numpy: https://www.numpy.org/
.. _msl-loadlib: https://msl-loadlib.readthedocs.io/en/stable/
.. _msl-io: https://msl-io.readthedocs.io/en/latest/
.. _pyserial: https://pythonhosted.org/pyserial/
.. _pyzmq: https://pyzmq.readthedocs.io/en/stable/
