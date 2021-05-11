"""
Example showing how to communicate with a WinCamD beam
profiling camera from DataRay.
"""
import pprint

# if matplotlib is available then plot the data
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='DataRay',
    model='WinCamD',
    connection=ConnectionRecord(
        address='SDK::DATARAYOCX',
        backend=Backend.MSL,
    ),
)

# connect to the camera (a GUI will be displayed)
# NOTE: The GUI must remain open to have access to the DataRay OCX library
camera = record.connect()

# wait until we finish configuring the camera
# (e.g, setting the ROI, the number of averages, ...)
camera.wait_to_configure()

# capture images
for i in range(5):
    info = camera.capture()

    # print and plot (if matplotlib is available) the information about the image
    print('Capture {}:'.format(i+1))
    pprint.pprint(info)
    if plt is not None:
        ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2)
        ax2 = plt.subplot2grid((2, 2), (0, 1))
        ax3 = plt.subplot2grid((2, 2), (1, 1))

        ax1.imshow(info['image'])
        ax1.set_title('Capture {}'.format(i+1))
        ax2.plot(info['profile_x'])
        ax2.set_title('Profile X')
        ax3.plot(info['profile_y'])
        ax3.set_title('Profile Y')

        plt.tight_layout()
        plt.show()

# disconnect from the camera (also closes the GUI)
camera.disconnect()
