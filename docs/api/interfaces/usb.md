# USB

Before communicating with a USB device, a [libusb](https://libusb.info/){:target="_blank"}-compatible
driver must be installed and the directory to the `libusb` library must be available on the `PATH` environment variable.

The following instructions are intended to be a starting point if you are having issues communicating with a USB device.

## Windows Setup
Download the latest `libusb` library from the [repository](https://github.com/libusb/libusb/releases){:target="_blank"}.

!!! tip
    Here, version 1.0.29 is downloaded. Update this value in the following command if there is a new release.

```shell
Invoke-WebRequest -Uri https://github.com/libusb/libusb/releases/download/v1.0.29/libusb-1.0.29.7z -OutFile libusb.7z
```

Use [7zip](https://7-zip.org/){:target="_blank"} to extract the zip file. First, install 7zip if it's not already.

```shell
winget install 7zip.7zip
```

Then extract the library file and copy the appropriate (i.e., x86 or x64, VS or MinGW) `libusb-1.0.dll` file to a directory that is on your `PATH` environment variable. The following command extracts the 64-bit library file that was built with Visual Studio 2022 to the *C:\Windows\System32* directory, but you may choose to extract a different DLL file to a different directory.

```shell
& 'C:\Program Files\7-Zip\7z' e libusb.7z -oC:/Windows/System32 VS2022/MS64/dll/libusb-1.0.dll
```

Finally, install the [Zadig](https://zadig.akeo.ie/){:target="_blank"} application

```shell
winget install akeo.ie.Zadig
```

then run Zadig (you must open a new administrative terminal)

```shell
zadig
```

to install a driver for the USB device &mdash; follow the [Zadig User Guide](https://github.com/pbatard/libwdi/wiki/Zadig){:target="_blank"}.

See [How to use libusb on Windows](https://github.com/libusb/libusb/wiki/Windows#user-content-How_to_use_libusb_on_Windows){:target="_blank"} for additional information.

## Debian/Ubuntu Setup
Install the `libusb-1.0-0` package.

```shell
sudo apt install libusb-1.0-0
```

To access a USB device without root privilege you should create a [udev](https://wiki.debian.org/udev){:target="_blank"} configuration file. There are many ways to configure *udev*, here is a typical setup.

```python
# /etc/udev/rules.d/10-custom.rules

SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", ATTR{idProduct}=="2107", GROUP="plugdev", MODE="0664"
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6001", GROUP="plugdev", MODE="0664"
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="faf0", GROUP="plugdev", MODE="0664"
```

You need to *unplug* / *plug back* the USB device once this file has been created so that *udev* loads the rules for the matching device, or alternatively, inform the `udev` daemon about the changes.

```shell
sudo udevadm control --reload-rules
sudo udevadm trigger
```

With this setup, be sure to add users that want to access the USB device(s) to the *plugdev* group.

```shell
sudo adduser $USER plugdev
```

Remember that you need to *log out* / *log in* to get the above command effective, or start a subshell.

```shell
newgrp plugdev
```

## macOS Setup
Install the `libusb` package.

```shell
brew install libusb
```

::: msl.equipment.interfaces.usb.Endpoint
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.usb.USB
    options:
        show_root_full_path: false
        show_root_heading: true
