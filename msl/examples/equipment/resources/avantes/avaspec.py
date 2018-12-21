"""
Example showing how to communicate with an AvaSpec-2048L using the Avantes SDK.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
    from msl.equipment.resources.avantes import MeasureCallback

    record = EquipmentRecord(
        manufacturer='Avantes',
        model='AvaSpec-2048L',
        serial='1807344U1',  # update the serial number for your device
        connection=ConnectionRecord(
            address='SDK::D:/AvaSpecX64-DLL_9.7/avaspecx64.dll',  # update the path to the DLL file
            backend=Backend.MSL,
        )
    )

    # this function will be called every time a measurement scan is available
    @MeasureCallback
    def callback_fcn(handle, info):
        print('The DLL handle is:', handle.contents.value)
        if info.contents.value == 0:  # equals 0 if everything is okay (see manual)
            print('  callback data:', ava.get_data())

    # initializes the Avantes SDK
    ava = record.connect()

    # get the information about all connected devices
    print('Devices found:')
    for i, device in enumerate(ava.get_list()):
        print('  Device %d' % i)
        print('    SerialNumber: %s' % device.SerialNumber)
        print('    UserFriendlyName: %s' % device.UserFriendlyName)
        print('    Status: %s' % device.Status)

    # print (some of) the device information about the spectrometer
    print('DeviceConfigType parameters:')
    params = ava.get_parameter()
    print('  m_Len: %d' % params.m_Len)
    print('  m_ConfigVersion: %d' % params.m_ConfigVersion)
    print('  m_aUserFriendlyId: %r' % params.m_aUserFriendlyId)
    print('  m_Detector.m_DefectivePixels: %r' % [val for val in params.m_Detector.m_DefectivePixels])
    print('  m_Detector.m_ExtOffset: %f' % params.m_Detector.m_ExtOffset)
    print('  m_Detector.m_Gain: %r' % [val for val in params.m_Detector.m_Gain])
    print('  m_Detector.m_NLEnable: %r' % params.m_Detector.m_NLEnable)
    print('  m_Detector.m_NrPixels: %d' % params.m_Detector.m_NrPixels)
    print('  m_Detector.m_Offset: %r' % [val for val in params.m_Detector.m_Offset])
    print('  m_Detector.m_SensorType: %d' % params.m_Detector.m_SensorType)
    print('  m_Detector.m_aFit: %r' % [val for val in params.m_Detector.m_aFit])
    print('  m_Detector.m_aHighNLCounts: %f' % params.m_Detector.m_aHighNLCounts)
    print('  m_Detector.m_aLowNLCounts: %f' % params.m_Detector.m_aLowNLCounts)
    print('  m_Detector.m_aNLCorrect: %r' % [val for val in params.m_Detector.m_aNLCorrect])
    print('  m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothPix: %d' % params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothPix)
    print('  m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothModel: %d' % params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothModel)
    print('  m_Irradiance.m_IntensityCalib.m_CalInttime: %d' % params.m_Irradiance.m_IntensityCalib.m_CalInttime)
    # ... continue printing parameters ...

    # get the number of pixels that the spectrometer has
    num_pixels = ava.get_num_pixels()
    print('The spectrometer has %d pixels' % num_pixels)

    # get the wavelength value of each pixel
    wavelengths = ava.get_lambda()

    # enable the 16-bit AD converter
    ava.use_high_res_adc(True)

    # prepare the measurement type of the spectrometer
    # (the values of just a few parameters are updated here, see the manual for more details)
    cfg = ava.MeasConfigType()
    cfg.m_StopPixel = num_pixels - 1
    cfg.m_IntegrationTime = 5  # in milliseconds
    cfg.m_NrAverages = 1  # number of averages
    ava.prepare_measure(cfg)

    # start continuous measurements
    # (use a callback function to be notified when a measurement is ready)
    ava.measure_callback(-1, callback_fcn)

    # get as many scans as possible for 2 seconds
    time.sleep(2)

    # stop continuous measurements
    ava.stop_measure()

    # start 1 measurement, wait until the measurement is finished, then get the data
    ava.measure(1)
    while not ava.poll_scan():
        time.sleep(0.01)
    tick_count, data = ava.get_data()

    # if matplotlib is available then plot the results
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print('measurement data:', data)
    else:
        plt.title('Time label (tick counts): %d' % tick_count)
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('ADC')
        plt.plot(wavelengths, data, 'bo')
        plt.show()

    # safely shutdown the Avantes resources that are in use
    ava.disconnect()
