# GPIB

## Prerequisites {: #gpib-prerequisites }

Before communicating with equipment that use the General Purpose Interface Bus (GPIB), you must have a GPIB-compatible driver installed and the directory to the appropriate library file (e.g., `ni4882`, `gpib-32`, `libgpib`) must be available on the `PATH` environment variable.

!!! tip
    You can create a `GPIB_LIBRARY` environment variable with the value being the full path to a GPIB library file to load. This variable can also be defined as a `<gpib_library>` element in a [Configuration file][configuration-files].

Consult the manufacturer's website for the appropriate software to install for the GPIB hardware you are using. Some options may include installing one of the following software packages for your operating system,

* [NI-488.2](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#575749){:target="_blank"}
* [Keysight IO Libraries Suite](https://www.keysight.com/vn/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html){:target="_blank"}

or you may even want to [build your own](https://github.com/xyphro/UsbGpib){:target="_blank"} GPIB adaptor.

### Debian/Ubuntu {: #gpib-prerequisites-linux }
If you are using Linux as your operating system, you may want to consider using the [linux-gpib](https://linux-gpib.sourceforge.io/){:target="_blank"} project to communicate with [supported GPIB hardware](https://linux-gpib.sourceforge.io/doc_html/supported-hardware.html){:target="_blank"}.

Save the following bash script as, for example, `install-linux-gpib.sh` and (optionally) update the value of the `VERSION` parameter to be the [latest linux-gpib](https://sourceforge.net/projects/linux-gpib/files/linux-gpib%20for%203.x.x%20and%202.6.x%20kernels/){:target="_blank"} release number.

??? example "install-linux-gpib.sh (click to expand)"
    ```shell
    #!/bin/bash

    # The linux-gpib version to install (optional: update to be the latest release version)
    VERSION="4.3.7"

    # Prerequisites to build linux-gpib
    sudo apt-get install --yes linux-headers-$(uname -r) wget automake libtool flex bison

    # Download and extract the specified linux-gpib version
    echo "Downloading linux-gpib-$VERSION.tar.gz source from https://sourceforge.net ..."
    wget -q -O linux-gpib-$VERSION.tar.gz https://sourceforge.net/projects/linux-gpib/files/linux-gpib%20for%203.x.x%20and%202.6.x%20kernels/$VERSION/linux-gpib-$VERSION.tar.gz/download
    tar -xf linux-gpib-$VERSION.tar.gz
    cd linux-gpib-$VERSION

    # Build and install the kernel files
    tar -xf linux-gpib-kernel-$VERSION.tar.gz
    cd linux-gpib-kernel-$VERSION
    make
    sudo make install
    cd ..

    # Build and install the user files
    tar -xf linux-gpib-user-$VERSION.tar.gz
    cd linux-gpib-user-$VERSION
    ./bootstrap
    ./configure --sysconfdir=/etc
    make
    sudo make install
    sudo ldconfig

    # Allow for access to the GPIB hardware without needing to be the root user
    sudo addgroup gpib
    sudo usermod -a -G gpib $(whoami)

    echo ""
    echo "Plug the GPIB-USB controller(s) into the appropriate USB port and run 'sudo gpib_config'"
    echo "to update the 'board_type' for the controller(s) that you are using."
    echo "If you get an error, for example,"
    echo "  failed to open device file '/dev/gpib0'"
    echo "unplug/re-plug the GPIB-USB controller (or restart the computer) and run 'sudo gpib_config' again."
    echo "You may also delete the linux-gpib-$VERSION directory and the linux-gpib-$VERSION.tar.gz file."
    ```

Make the script executable,

```command
chmod +x ./install-linux-gpib.sh
```

then run it to install the *linux-gpib* driver and to allow for access to the GPIB hardware without needing to be the root user.

```command
./install-linux-gpib.sh
```

::: msl.equipment.interfaces.gpib.GPIB
    options:
        show_root_full_path: false
        show_root_heading: true
