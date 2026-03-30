# Modbus

## Prerequisites {: #modbus-prerequisites }

See [this][serial-prerequisites] section if you are communicating with a Modbus device on Linux or macOS via the [Serial][] interface. Otherwise, there are no prerequisites to follow on Windows or if using a network [Socket][] for the interface.

::: msl.equipment.interfaces.modbus.Modbus
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.modbus.ModbusIdentification
    options:
        show_root_full_path: false
        show_root_heading: true
        show_attribute_values: false

::: msl.equipment.interfaces.modbus.ModbusObject
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.modbus.ModbusResponse
    options:
        show_root_full_path: false
        show_root_heading: true
        show_attribute_values: false
