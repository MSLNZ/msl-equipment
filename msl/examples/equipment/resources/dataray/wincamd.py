"""
Example showing how to communicate with a WinCamD beam profiling camera from DataRay.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import pprint

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = None

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='DataRay',
        model='WinCamD',
        connection=ConnectionRecord(
            address='SDK::DATARAYOCX',
            backend=Backend.MSL,
        ),
    )

    # connect to the camera
    # NOTE: a GUI will be displayed (the GUI must remain open
    #       to have full access to the DataRay OCX library).
    camera = record.connect()

    # wait until we finish configuring the camera
    # (e.g, setting the ROI, the number of averages, ...)
    camera.wait_to_configure()

    # capture an image (could be an average of N images)
    info = camera.capture()

    # print and plot (if matplotlib is available) the information about the image
    pprint.pprint(info)
    if plt is not None:
        ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2)
        ax2 = plt.subplot2grid((2, 2), (0, 1))
        ax3 = plt.subplot2grid((2, 2), (1, 1))

        ax1.imshow(info['image'])
        ax2.plot(info['profile_x'])
        ax2.set_title('Profile X')
        ax3.plot(info['profile_y'])
        ax3.set_title('Profile Y')

        plt.tight_layout()
        plt.show()

    # disconnect from the camera (also closes the GUI)
    camera.disconnect()
