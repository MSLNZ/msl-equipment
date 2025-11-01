"""Example showing how to find all devices from Princeton Instruments."""

from msl.equipment.resources import PrincetonInstruments

# Load the SDK (update the path for your computer)
PrincetonInstruments.init(r"C:\Program Files (x86)\Princeton Instruments\ARC_Instrument_x64.dll")

major, minor, build = PrincetonInstruments.ver()
print(f"Using version {major}.{minor}.{build} of the SDK")

# Find all devices from Princeton Instruments
num_found = PrincetonInstruments.search_for_inst()
print(f"Found {num_found} device(s):")
for enum in range(num_found):
    model = PrincetonInstruments.get_enum_preopen_model(enum)
    serial = PrincetonInstruments.get_enum_preopen_serial(enum)
    port = PrincetonInstruments.get_enum_preopen_com(enum)
    print(f"  Model#: {model!r}, Serial#: {serial} -> at COM{port}")

# List all Monochromator's that are available
print("Monochromator's available:")
for enum in range(num_found):
    try:
        model = PrincetonInstruments.get_mono_preopen_model(enum)
    except RuntimeError:
        continue
    else:
        print(f"  {model!r} at COM{PrincetonInstruments.get_enum_preopen_com(enum)}")
