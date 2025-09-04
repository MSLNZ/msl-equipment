# Resources

Resources are custom classes for interfacing with specific equipment. In previous releases of `msl-equipment` (versions < 1.0), the resources were automatically bundled with `msl-equipment`. As of v1.0, the resources are maintained in another package, `msl-equipment-resources`, that must be installed separately.

Some of the resources might not work in your application because the resource might depend on an external dependency, e.g., the Software Development Kit (SDK) provided by a manufacturer, and this external dependency might not be available for your operating system.

!!! danger "Attention"
    Companies that sell equipment that are used for scientific research are identified in this guide in order to illustrate how to adequately use `msl-equipment-resources` in your application. Such identification is not intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand, nor is it intended to imply that the companies identified are necessarily the best for the purpose.

## Install

Installing `msl-equipment-resources` will also install `msl-equipment`

```console
pip install msl-equipment-resources
```

## Create a new resource
