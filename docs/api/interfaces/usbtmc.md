# USBTMC

## Prerequisites {: #usbtmc-prerequisites }

Before communicating with equipment that use the [USB Test & Measurement Class](https://www.usb.org/document-library/test-measurement-class-specification){:target="_blank"} protocol, a [libusb](https://libusb.info/){:target="_blank"}-compatible driver must be installed and the directory to the `libusb` library must be available on the `PATH` environment variable. See [here][usb] for more details.

::: msl.equipment.interfaces.usbtmc.USBTMC
    options:
        show_root_full_path: false
        show_root_heading: true
