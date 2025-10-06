# API Overview

Although this package contains many classes and functions, the classes that you may typically create instances of are

* [Config][] &mdash; if you want to load equipment registers and communicate with equipment
* [Connection][] &mdash; if you are only interested in communicating with equipment
* [Register][] &mdash; if you only want to load an equipment register

and there are [enumeration][enumerations] classes.

[Interfaces][] are available to communicate with equipment, [Backends][] may be used to interface with equipment using external packages and possibly [Resources][] may be available.

!!! tip
    You do not need to create instances of these communication classes. Calling the [Equipment.connect()][msl.equipment.schema.Equipment.connect] or [Connection.connect()][msl.equipment.schema.Connection.connect] method will automatically use the correct object for communication.

    If you are using type annotations and/or an editor that supports code completion, you can annotate the type of the returned object to get support for these features, for example,

    ```python
    from msl.equipment import GPIB, Connection

    device: GPIB = Connection("GPIB::22").connect()
    ```

The [MSLConnectionError][msl.equipment.interfaces.message_based.MSLConnectionError] and [MSLTimeoutError][msl.equipment.interfaces.message_based.MSLTimeoutError] classes are raised if there are issues when communicating with equipment.
