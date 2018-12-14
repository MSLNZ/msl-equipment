"""
This example prints a list of all the PicoScopes that are connected to the computer. 
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import sys

    from msl.equipment.resources.picotech.picoscope import enumerate_units

    # ensure that the PicoTech DLLs are available on PATH
    sys.path.append(r'C:\Program Files\Pico Technology\SDK\lib')

    units = enumerate_units()
    print('The following serial numbers were found: {}'.format(units))
