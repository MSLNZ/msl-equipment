# Resources

Resources are custom classes for interfacing with specific equipment. In previous releases of `msl-equipment` (versions < 1.0), the resources were automatically bundled with `msl-equipment`. As of v1.0, the resources are maintained in another package, `msl-equipment-resources`, that must be installed separately.

Some of the resources might not work in your application because the resource might depend on an external dependency, e.g., the Software Development Kit (SDK) provided by a manufacturer, and this external dependency might not be available for your operating system.

!!! examples
    There are examples on how to use the resources in the [repository](https://github.com/MSLNZ/msl-equipment/tree/main/packages/resources/examples){:target="_blank"}.

!!! danger "Attention"
    Companies that sell equipment that are used for scientific research are identified in this guide in order to illustrate how to adequately use `msl-equipment-resources` in your application. Such identification is not intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand, nor is it intended to imply that the companies identified are necessarily the best for the purpose.

## Install

`msl-equipment-resources` is currently only available for installation from source. It can be installed using a variety of package managers.

=== "pip"
    ```console
    pip install msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "uv"
    ```console
    uv add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "poetry"
    ```console
    poetry add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "pdm"
    ```console
    pdm add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

## Create a new resource

TODO...

## Multiple interfaces

If the equipment supports multiple interfaces for message-based protocols (e.g., [Socket][msl.equipment.interfaces.socket.Socket], [Serial][msl.equipment.interfaces.serial.Serial], [GPIB][msl.equipment.interfaces.gpib.GPIB], ...) you can create a resource that inherits from the [MultiMessageBased][msl.equipment_resources.multi_message_based.MultiMessageBased] class. Upon calling [super][] in the subclass, the connection is established with the appropriate protocol class.
