"""
This example communicates with a Thorlabs Filter Flipper (MFF101).

Since the Thorlabs MotionControl API requires a serial number to communicate with a device, 
the serial number that is specified in the "equipment-connections-database.xlsx" database, 
i.e., 37871232, would need to be changed to the serial number of the device that is connected 
to the computer.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time

    from msl.equipment import Config
    from msl.examples.equipment import EXAMPLES_DIR

    # you will have to update the value of the serial number for the FilterFlipper
    # in the "equipment-connections-database.xlsx" database
    db = Config(os.path.join(EXAMPLES_DIR, 'equipment-configuration.xml')).database()
    flipper = db.equipment['filter_flipper'].connect()

    print(flipper)

    # make the LED flash on the Filter Flipper
    flipper.identify()
    time.sleep(3)

    hw_info = flipper.get_hardware_info()
    print('serialNumber................: {}'.format(hw_info.serialNumber))
    print('modelNumber.................: {}'.format(hw_info.modelNumber))
    print('type........................: {}'.format(hw_info.type))
    print('numChannels.................: {}'.format(hw_info.numChannels))
    print('notes.......................: {}'.format(hw_info.notes))
    print('firmwareVersion.............: {}'.format(flipper.to_version(hw_info.firmwareVersion)))
    print('hardwareVersion.............: {}'.format(hw_info.hardwareVersion))
    print('modificationState...........: {}'.format(hw_info.modificationState))

    io_settings = flipper.get_io_settings()
    print('transitTime.................: {}'.format(io_settings.transitTime))
    print('ADCspeedValue...............: {}'.format(io_settings.ADCspeedValue))
    print('digIO1OperMode..............: {}'.format(io_settings.digIO1OperMode))
    print('digIO1SignalMode............: {}'.format(io_settings.digIO1SignalMode))
    print('digIO1PulseWidth............: {}'.format(io_settings.digIO1PulseWidth))
    print('digIO2OperMode..............: {}'.format(io_settings.digIO2OperMode))
    print('digIO2SignalMode............: {}'.format(io_settings.digIO2SignalMode))
    print('digIO2PulseWidth............: {}'.format(io_settings.digIO2PulseWidth))

    print('get_firmware_version........: {}'.format(flipper.get_firmware_version()))
    print('get_software_version........: {}'.format(flipper.get_software_version()))
    print('get_number_positions........: {}'.format(flipper.get_number_positions()))
    print('get_transit_time............: {}'.format(flipper.get_transit_time()))
    print('request_settings............: {}'.format(flipper.request_settings()))

    flipper.home()

    print('time_since_last_msg_received: {}'.format(flipper.time_since_last_msg_received()))
    print('has_last_msg_timer_overrun..: {}'.format(flipper.has_last_msg_timer_overrun()))

    # start the device polling at 200-ms intervals
    flipper.start_polling(200)
    print('polling_duration............: {}'.format(flipper.polling_duration()))
    print('message_queue_size..........: {}'.format(flipper.message_queue_size()))
    print('get_next_message............: {}'.format(flipper.convert_message(*flipper.get_next_message())))

    position = flipper.get_position()
    print('get_position:...............: {}'.format(position))

    # use event messages to wait for the flipper to finish moving
    move_to = 1 if position == 2 else 2
    flipper.move_to_position(move_to, wait=True)
    print('get_position:...............: {}'.format(flipper.get_position()))

    flipper.stop_polling()
