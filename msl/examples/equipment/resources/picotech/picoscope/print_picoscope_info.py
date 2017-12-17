"""
This example prints the information available about a PicoScope. 
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    from msl.examples.equipment.resources.picotech.picoscope import record

    scope = record.connect()
    print('Summary for {}'.format(record))

    # print all information that is available about the PicoScope
    print(scope.get_unit_info())

    print('')

    # use the enum value to get the calibration date, do not print the member-name prefix
    print('The PicoScope was calibrated on {}'.format(scope.get_unit_info(5, False)))

    # use the enum member name to get the calibration date
    print(scope.get_unit_info('cal_date'))

    print('The current power source is ' + scope.current_power_source())
    if scope.IS_PS5000A:
        print('The device resolution is {!r}'.format(scope.get_device_resolution()))  # only valid for ps5000a scopes
    print('The maximum ADU value is {}'.format(scope.maximum_value()))
    print('The minimum ADU value is {}'.format(scope.minimum_value()))
    print('The voltage-offset range for a +/-1V voltage range is {}'.format(scope.get_analogue_offset('1V', 'dc')))
    print('The voltage ranges available for channel A are: {}'.format(scope.get_channel_information('A')))
    print('The maximum down-sampling ratio that can be used for a given number of samples in a given down-sampling '
          'mode is {}'.format(scope.get_max_down_sample_ratio(1000, mode='aggregate')))
    print('The maximum number of segments allowed is {}'.format(scope.get_max_segments()))
    print('AWG range of allowed sample values and waveform buffer sizes {}'.format(scope.sig_gen_arbitrary_min_max_values()))
