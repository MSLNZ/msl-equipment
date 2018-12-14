"""
Example showing how to list all Pico Technology PT-104 Platinum Resistance Data Logger's that can be found.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import sys
    from msl.equipment.resources.picotech.pt104 import enumerate_units

    # ensure that the PicoTech DLLs are available on PATH
    sys.path.append(r'C:\Program Files\Pico Technology\SDK\lib')

    units = enumerate_units()
    print('Found the following PT-104\'s: {}'.format(units))
