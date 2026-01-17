# FTDI

## Prerequisites {: #ftdi-prerequisites }

Before communicating with equipment that use a Future Technology Devices International (FTDI) chip for the interface, either a [libusb](https://libusb.info/){:target="_blank"}-compatible driver or the [d2xx](https://ftdichip.com/drivers/d2xx-drivers/){:target="_blank"} driver must be installed and the directory to the appropriate library file (`libusb` or `ftd2xx`) must be available on the `PATH` environment variable.

The following instructions are intended to be a starting point if you are having issues communicating with an FTDI chip.

### Windows {: #ftdi-prerequisites-windows }
The choice of using a `libusb` or `d2xx` driver depends on whether the manufacturer of the equipment provides software that you also want to use to control the equipment and what driver their software uses. On Windows, this is typically the `d2xx` driver. If you don't want to use the manufacturer's software (or they don't provide software) then the choice of which driver to use does not matter.

If you want to use a `libusb` driver, follow [these][usb-prerequisites-windows] instructions.

If you want to use the [d2xx](https://ftdichip.com/drivers/d2xx-drivers/){:target="_blank"} driver, follow the [installation guide](https://ftdichip.com/wp-content/uploads/2023/11/AN_396_FTDI_Drivers_Installation_Guide_for_Windows_10_11.pdf){:target="_blank"} (skip this step if the Windows Device Manager shows that the driver for the equipment has already been successfully installed), [download](https://ftdichip.com/wp-content/uploads/2025/03/CDM-v2.12.36.20-WHQL-Certified.zip) the zip file that contains the `ftd2xx` library file then extract the zip file and copy the appropriate library file (i.e., `amd64\ftd2xx64.dll` if using 64-bit Python, `i386\ftd2xx.dll` if using 32-bit Python) to a directory that is on your `PATH` environment variable.

### Debian/Ubuntu {: #ftdi-prerequisites-linux }
If you want to use the `libusb` driver (recommended), follow [these][usb-prerequisites-linux] instructions.

If you want to use the [d2xx](https://ftdichip.com/drivers/d2xx-drivers/){:target="_blank"} driver, follow the [installation guide](https://ftdichip.com/wp-content/uploads/2020/08/AN_220_FTDI_Drivers_Installation_Guide_for_Linux-1.pdf){:target="_blank"}, [download](https://ftdichip.com/wp-content/uploads/2025/11/libftd2xx-linux-x86_64-1.4.34.tgz) the compressed-archive file that contains the `libftd2xx.so` library file then extract the archive and copy the library file (i.e., `linux-x86_64\libftd2xx.so`) to a directory that is on your `PATH` environment variable, and, finally create a *udev* rule to be able to access the equipment as a non-root user (follow the *udev* instructions from [here][usb-prerequisites-linux]).

### macOS {: #ftdi-prerequisites-macos }
If you want to use the `libusb` driver (recommended), follow [these][usb-prerequisites-macos] instructions.

If you want to use the [d2xx](https://ftdichip.com/drivers/d2xx-drivers/){:target="_blank"} driver, follow the [installation guide](https://ftdichip.com/wp-content/uploads/2020/08/AN_134_FTDI_Drivers_Installation_Guide_for_MAC_OSX-1.pdf){:target="_blank"}, [download](https://ftdichip.com/wp-content/uploads/2024/04/D2XX1.4.30.dmg) the virtual-disk file that contains the `libftd2xx.dylib` library file then extract the file and copy the library file (i.e., `release\build\libftd2xx.1.4.30.dylib`) to a directory that is on your `PATH` environment variable, and, finally rename the library file to be `libftd2xx.dylib` (i.e., remove the version information).


::: msl.equipment.interfaces.ftdi.FTDI
    options:
        show_root_full_path: false
        show_root_heading: true
