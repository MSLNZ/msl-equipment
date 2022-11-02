"""
Establishes a connection to the ``DATARAYOCX`` library developed by DataRay Inc.
"""
import os

import numpy as np
from msl.loadlib import (
    Client64,
    Server32Error,
    ConnectionTimeoutError,
)

from msl.equipment.connection import Connection
from msl.equipment.resources import register
from msl.equipment.exceptions import DataRayError


@register(manufacturer=r'Data\s*Ray', model=r'.')
class DataRayOCX64(Connection):

    def __init__(self, record):
        """A wrapper around the :class:`~.datarayocx_32.DataRayOCX32` class.

        This class can be used with either a 32- or 64-bit Python interpreter
        to call the 32-bit functions in the ``DATARAYOCX`` library. A GUI is
        created to configure and visualize the images taken by the camera.

        Tested with the WinCamD-LCM-8.0D36 software version.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a DataRay connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'area_filter': int, area filter: 1=1pixel, 2=3pixels, 3=5pixels, 4=7pixels, 5=9pixels [default: 1]
            'camera_index': int, the camera to use (between 0 and 7; 0=first camera found) [default: 0]
            'centroid_method': int, the centroid method to use (0, 1 or 2) [default: 0]
            'filter': float, percent full scale filter (0, 0.1, 0.2, 0.5, 1, 2, 5 or 10) [default: 0.2]
            'major_minor_method': int, the major/minor method to use (0, 1 or 2) [default: 0]
            'ui_size': int, the size of the User Interface (value=height of a button in pixels) [default: 25]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(DataRayOCX64, self).__init__(record)
        self.set_exception_class(DataRayError)

        self._client = None
        error = None
        try:
            self._client = Client64(
                os.path.join(os.path.dirname(__file__), 'datarayocx_32.py'),
                prog_id_prefix=record.connection.address[5:],
                **record.connection.properties
            )
        except ConnectionTimeoutError as err:
            error = err.reason

        # check for errors instantiating the DataRayOCX32 class
        if error:
            self.raise_exception(
                'Cannot connect to the DataRay Beam Profiler.\n{}'.format(error)
            )

        # check for errors starting the camera
        error = self._client.request32('error')
        if error:
            self.disconnect()
            self.raise_exception('Error initializing the DataRay OCX library\n{}'.format(error))

        self.log_debug('Connected to %s', record.connection)

    def wait_to_configure(self):
        """Wait until the camera has been configured.

        This is a blocking call and waits until you close the popup Window.
        """
        self.log_debug('DataRayOCX64.wait_to_configure()')
        self._client.request32('wait_to_configure')

    def capture(self, timeout=10, restart=False):
        """Capture an image.

        Parameters
        ----------
        timeout : :class:`float`, optional
            The maximum number of seconds to wait to capture an image.
        restart : :class:`bool`, optional
            Whether to keep the camera running after the image is captured.

        Returns
        -------
        :class:`dict`
            The information about the captured image. The key-value pairs are:

            * ``adc_peak_%``: :class:`float`, the maximum ADC value (as a percentage)
            * ``area_filter``: :class:`int`, area filtering applies a convolution to the pixels (1=1pixel, 2=3pixels, 3=5pixels, 4=7pixels, 5=9pixels)
            * ``centroid``: :class:`tuple`, the (x, y) centroid value
            * ``centroid_filter_size``: :class:`int`, centroid filter size (in pixels)
            * ``centroid_type``: :class:`int`, the centroid type (0, 1 or 2)
            * ``clip_level_centroid``: :class:`float`, the centroid clip level (between 0 and 1)
            * ``clip_level_geo``: :class:`float`, the geometric clip level (between 0 and 1)
            * ``crosshair``: :class:`float`, the angle between the horizontal x-axis and the solid crosshair line (in degrees)
            * ``eff_2w``: :class:`float`, the effective beam size (in um)
            * ``effective_centroid``: :class:`tuple`, the effective (x, y) centroid value
            * ``effective_geo_centroid``: :class:`tuple`, the effective (x, y) geometric centroid value
            * ``ellip``: :class:`float`, the ratio between the minor/major axis
            * ``elp``: :class:`float`, the beam azimutal angle for ISO 11146 (in degrees)
            * ``exposure_time``: :class:`float`, the exposure time (in ms)
            * ``filter_full_scale``: :class:`float`, used in the triangular weighting smoothing function
            * ``image``: :class:`numpy.ndarray`, the camera image
            * ``image_zoom``: :class:`float`, the zoom factor of the image
            * ``imager_gain``: :class:`float`, the gain used by the imager
            * ``inc_p``: :class:`float`, Dxx power (in Watts)
            * ``inc_power_area``: :class:`float`, Dxx beam area (in mm^2)
            * ``inc_power_major``: :class:`float`, Dxx beam diameter along the major axis (in mm)
            * ``inc_power_mean``: :class:`float`, Dxx mean beam diameter (in mm)
            * ``inc_power_minor``: :class:`float`, Dxx beam diameter along the minor axis (in mm)
            * ``is_fast_update``: :class:`bool`, whether the camera is in fast update or normal mode
            * ``is_full_resolution``: :class:`bool`, whether the camera is set to full resolution
            * ``maj_iso``: :class:`float`, the ISO 11146 beam size along the major axis (in um)
            * ``major``: :class:`float`, the beam size along the major axis (in um)
            * ``major_minor_method``: :class:`int`, the major/minor method used (0, 1 or 2)
            * ``mean``: :class:`float`, the mean beam size (in um)
            * ``mean_theta``: :class:`float`, Dxx mean angle (in mrad)
            * ``min_iso``: :class:`float`, the ISO 11146 beam size along the minor axis (in um)
            * ``minor``: :class:`float`, the beam size along the minor axis (in um)
            * ``num_averages``: :class:`int`, the number of averages per capture
            * ``num_captures``: :class:`int`, the number of images that have been captured
            * ``orient``: :class:`float`, the angle between the horizontal x-axis and the major or minor axis closest to the horizontal x-axis (in degrees)
            * ``peak``: :class:`tuple`, the peak location in (x, y), usually zero
            * ``pixel_width_um``: :class:`float`, the width of a pixel (in um)
            * ``pixel_height_um``: :class:`float`, the height of a pixel (in um)
            * ``pk_to_avg``: :class:`float`, the peak to average value
            * ``plateau_uniformity``: :class:`float`, the flatness of the plateau (between 0 and 1)
            * ``profile_x``: :class:`numpy.ndarray`, the profile in the X direction
            * ``profile_y``: :class:`numpy.ndarray`, the profile in the Y direction
            * ``roi``: :class:`tuple`, the selected region of interest (x, y, width, height)
            * ``xc``: :class:`float`, the centroid position along the x axis (in um)
            * ``xg``: :class:`float`, the geometric centroid position along the x axis (in um)
            * ``xp``: :class:`float`, the peak-intensity centroid position along the x axis (in um)
            * ``xu``: :class:`float`, the user-selected centroid position along the x axis (in um)
            * ``yc``: :class:`float`, the centroid position along the y axis (in um)
            * ``yg``: :class:`float`, the geometric centroid position along the y axis (in um)
            * ``yp``: :class:`float`, the peak-intensity centroid position along the y axis (in um)
            * ``yu``: :class:`float`, the user-selected centroid position along the y axis (in um)

        Raises
        ------
        ~msl.equipment.exceptions.DataRayError
            If not successful.
        """
        self.log_debug('DataRayOCX64.capture(timeout=%s)', timeout)

        info = {}
        error = None
        try:
            info = self._client.request32('capture', timeout)
        except Server32Error as err:
            error = err  # TODO avoid raising nested exceptions in Python 2.7

        if error:
            self.raise_exception(error)

        shape = info.pop('shape')
        if not info['is_full_resolution']:
            shape = (shape[0]//2, shape[1]//2)

        info['image'] = np.asarray(info['image']).reshape(shape)
        info['profile_x'] = np.asarray(info['profile_x'])[:shape[1]]
        info['profile_y'] = np.asarray(info['profile_y'])[:shape[0]]
        if restart:
            self.start()
        return info

    def disconnect(self):
        """Disconnect from the camera."""
        if not self._client:
            return

        try:
            stdout, stderr = self._client.shutdown_server32()
            stdout.close()
            stderr.close()
        except:
            pass

        self._client = None
        self.log_debug('Disconnected from %s', self.equipment_record.connection)

    def start(self):
        """Start the camera."""
        self.log_debug('DataRayOCX64.start()')
        try:
            return self._client.request32('start')
        except Server32Error as err:
            error = err  # TODO avoid raising nested exceptions in Python 2.7
        self.raise_exception(error)

    def stop(self):
        """Stop the camera."""
        self.log_debug('DataRayOCX64.stop()')
        try:
            return self._client.request32('stop')
        except Server32Error as err:
            error = err  # TODO avoid raising nested exceptions in Python 2.7
        self.raise_exception(error)
