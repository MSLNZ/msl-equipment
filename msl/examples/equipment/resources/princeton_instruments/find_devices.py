"""
Example showing how to find all devices from Princeton Instruments.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    from msl.equipment.exceptions import PrincetonInstrumentsError
    from msl.equipment.resources import PrincetonInstruments as PI

    # Load the SDK (update the path for your computer)
    PI.init('D:/PI/ARC_Instrument_x64.dll')
    print('Using version {}.{}.{} of the SDK'.format(*PI.ver()))

    # Find all devices from Princeton Instruments
    num_found = PI.search_for_inst()
    print('Found {} device(s):'.format(num_found))
    for enum in range(num_found):
        model = PI.get_enum_preopen_model(enum)
        serial = PI.get_enum_preopen_serial(enum)
        port = PI.get_enum_preopen_com(enum)
        print('  Model#: {!r}, Serial#: {} -> at COM{}'.format(model, serial, port))

    # List all Monochromators that are available
    print('Monochromators available:')
    for enum in range(num_found):
        try:
            model = PI.get_mono_preopen_model(enum)
        except PrincetonInstrumentsError:
            pass
        else:
            print('  {!r} at COM{}'.format(model, PI.get_enum_preopen_com(enum)))
