# Overview

!!! info
    The docs are being rewritten. See [here](https://msl-equipment.readthedocs.io/en/latest/index.html) for the old docs.

The purpose of `msl-equipment` is to manage information about equipment and to interface with equipment for computer control. The information that is managed is focused on testing and calibration laboratories that are accredited for the [ISO/IEC 17025](https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html){:target="_blank"} standard, but the information may also be selectively specified for laboratories that are not required to meet the standard. See the [Getting Started][] page to learn how information is managed and how equipment is controlled.

## Install

The `msl-equipment` [repository](https://github.com/MSLNZ/msl-equipment/){:target="_blank"} is organised as a [workspace project](https://docs.astral.sh/uv/concepts/projects/workspaces/){:target="_blank"} that is split across multiple packages: `msl-equipment`, [msl-equipment-resources][resources], [msl-equipment-validate][validate], and [msl-equipment-webapp][web-application].

The core package is `msl-equipment` and it is available through the [Python Package Index](https://pypi.org/project/msl-equipment/){:target="_blank"}. It can be installed using a variety of package managers

=== "pip"
    ```console
    pip install msl-equipment
    ```

=== "uv"
    ```console
    uv add msl-equipment
    ```

=== "poetry"
    ```console
    poetry add msl-equipment
    ```

=== "pdm"
    ```console
    pdm add msl-equipment
    ```

### Dependencies

The `msl-equipment` package depends on the following packages: [msl-loadlib](https://mslnz.github.io/msl-loadlib/latest/), [numpy](https://www.numpy.org/){:target="_blank"}, [pyserial](https://pyserial.readthedocs.io/en/latest/){:target="_blank"}, [pyzmq](https://pyzmq.readthedocs.io/en/stable/){:target="_blank"}

The following packages are optional dependencies that may be installed to interface with equipment: [msl-equipment-resources][resources], [NI-DAQmx](https://nidaqmx-python.readthedocs.io/en/stable/){:target="_blank"}, [PyVISA](https://pyvisa.readthedocs.io/en/stable/){:target="_blank"}, [PyVISA-py](https://pyvisa.readthedocs.io/projects/pyvisa-py/en/stable/){:target="_blank"}
