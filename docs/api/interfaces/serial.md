# Serial

## Prerequisites {: #serial-prerequisites }

If you are communicating with a Serial device on Windows, you already have permission (from the operating system) to access the serial port (or USB-to-Serial adaptor). If you receive an *Access is denied* error message when connecting to a serial port, that indicates the serial port is already open in another application.

If you are using Linux or macOS and receive a *Device or resource busy* error message when connecting to a serial port, that indicates the serial port is already open in another application. A *Permission denied* error can be solved by either running your application as the root user or by adding the current user to the same *group* that the serial port belongs to.

To determine the *group* that a serial port (e.g., `/dev/ttyUSB0`) belongs to, run the following.

```console
ls -l /dev/ttyUSB0
```

The output will be similar to

```console
crw-rw---- 1 root dialout 4, 64 Feb 20 17:23 /dev/ttyUSB0
```

where it is shown that this serial port belongs to the `dialout` *group*.

Add the current user to the appropriate *group* (e.g., `dialout` for the above case)

```console
sudo usermod -a -G dialout $USER
```

and then log out and in again (or restart the computer if you still encounter permission issues after re-logging in).

::: msl.equipment.interfaces.serial.Serial
    options:
        show_root_full_path: false
        show_root_heading: true
