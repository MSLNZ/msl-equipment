"""
Example showing how to list all Pico Technology PT-104 Platinum Resistance Data Logger's that can be found.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    from msl.equipment.resources.picotech.pt104 import enumerate_units

    # ensure that the PicoTech DLLs are available on PATH
    os.environ['PATH'] += os.pathsep + r'C:\Program Files\Pico Technology\SDK\lib'

    units = enumerate_units()
    print('The following PT-104\'s were found: {}'.format(units))
