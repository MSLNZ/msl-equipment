"""
Load the 32-bit ``DATARAYOCX`` library using :ref:`msl-loadlib-welcome`.
"""
from __future__ import annotations

import os
import threading
import time
import traceback

from msl.loadlib import Server32


class DataRayOCX32(Server32):

    def __init__(self, host, port, **kwargs):
        """Communicates with the 32-bit ``DATARAYOCX`` library.

        Tested with the WinCamD-LCM-8.0D36 software version.
        """

        # the DATARAYOCX library must be started in a separate thread in order
        # to keep the GUI responsive. Therefore, a dummy DLL is loaded on the
        # 32-bit server and all requests from Client64 are passed to the
        # ActiveX application instance
        dummy = os.path.join(Server32.examples_dir(), 'cpp_lib32')
        super(DataRayOCX32, self).__init__(dummy, 'cdll', host, port)

        # this parameter is used by datarayocx_64.py to verify
        # that no errors occurred while staring the camera
        self.error = None

        self.initialized = False

        # create the GUI for the ActiveX application in a separate thread
        self.thread = threading.Thread(
            target=self._create_app, kwargs=kwargs, daemon=True
        )
        self.thread.start()

        t0 = time.time()
        while not self.initialized and not self.error:
            time.sleep(0.1)
            if time.time() - t0 > 10:
                self.error = 'Could not initialize the DataRay camera after 10 seconds'

    def _create_app(self, **kwargs):
        try:
            self.app = DataRayApp(**kwargs)
            self.app.GetData.StopDevice()
            self.initialized = self.app.GetData.StartDriver()
            if self.initialized:
                Forms.Application.Run(self.app)
            else:
                self.error = 'Cannot start the DataRay camera driver'
        except:
            self.error = traceback.format_exc()

    def wait_to_configure(self):
        """Wait until the camera has been configured."""
        self.app.wait_to_configure()

    def capture(self, timeout):
        """Capture an image."""
        return self.app.capture(timeout)

    def start(self):
        """Start the camera."""
        return self.app.start_device()

    def stop(self):
        """Stop the camera."""
        return self.app.stop_device()

    def shutdown_handler(self):
        """Stop the camera and close the application."""
        self.app.GetData.StopDevice()

        # unregister the Close callback
        self.app.FormClosing -= self.app.on_form_closing

        self.app.Close()
        Forms.Application.Exit()
        self.thread.join()


# only create the ActiveX application if running on the 32-bit sever (see msl-loadlib)
if Server32.is_interpreter():
    from ctypes import (
        c_int32,
        byref,
    )

    # avoid comtypes importing 64-bit numpy from msl-equipment
    Server32.remove_site_packages_64bit()

    from msl.loadlib.activex import (
        Application,
        Forms,
        System,
        WS_CHILD,
        WS_VISIBLE,
    )

    class DataRayApp(Application):

        BUTTON_EFF_2W = 95
        BUTTON_XC = 171
        BUTTON_YC = 172
        BUTTON_XG = 173
        BUTTON_YG = 174
        BUTTON_XP = 175
        BUTTON_YP = 176
        BUTTON_XU = 233
        BUTTON_YU = 234
        BUTTON_ELLIPSE = 177
        BUTTON_POWER = 178
        BUTTON_ORIENTATION = 179
        BUTTON_MAJOR = 180
        BUTTON_MINOR = 181
        BUTTON_MEAN = 182
        BUTTON_ADC_PEAK = 183
        BUTTON_MAJ_ISO = 226
        BUTTON_MIN_ISO = 227
        BUTTON_ELP = 228
        BUTTON_INC_POWER_MAJOR = 261
        BUTTON_INC_POWER_MINOR = 262
        BUTTON_INC_POWER_MEAN = 263
        BUTTON_INC_POWER_AREA = 264
        BUTTON_INC_P = 265
        BUTTON_INC_IRR = 266
        BUTTON_MEAN_THETA = 267
        BUTTON_PLATEAU_UNIFORMITY = 291
        BUTTON_CLIP_A = 294
        BUTTON_CLIP_B = 295
        BUTTON_STATUS = 297
        BUTTON_CENTROID = 298
        BUTTON_IMAGE_ZOOM = 301
        BUTTON_CROSSHAIR = 302
        BUTTON_EXPOSURE_1 = 409
        BUTTON_GAIN_1 = 421
        BUTTON_RC = 425
        BUTTON_PK_TO_AVG = 429

        PROFILE_X = 22
        PROFILE_Y = 23

        def __init__(self, **kwargs):
            super(DataRayApp, self).__init__()

            self.camera_index = int(kwargs.get('camera_index', 0))
            if self.camera_index < 0 or self.camera_index > 7:
                raise ValueError(
                    'The camera index must be between 0 and 7 (got {})'.format(self.camera_index)
                )

            self.default_major_minor_method = int(kwargs.get('major_minor_method', 0))
            if self.default_major_minor_method not in [0, 1, 2]:
                raise ValueError(
                    'The major/minor method must be 0, 1 or 2 (got {})'.format(self.default_major_minor_method)
                )

            self.default_centroid_method = int(kwargs.get('centroid_method', 0))
            if self.default_centroid_method not in [0, 1, 2]:
                raise ValueError(
                    'The centroid method must be 0, 1 or 2 (got {})'.format(self.default_centroid_method)
                )

            # the manual claims it can be between 0 and 10.1
            self.default_full_scale_filter = float(kwargs.get('filter', 0.2))
            if self.default_full_scale_filter < 0 or self.default_full_scale_filter > 10.1:
                raise ValueError(
                    'The full-scale-filter index must be between '
                    '0 and 10.1 (got {})'.format(self.default_full_scale_filter)
                )

            self.default_area_filter = int(kwargs.get('area_filter', 1))
            if self.default_area_filter not in [1, 2, 3, 4, 5]:
                raise ValueError(
                    'The area-filter method must be between 1 and 5 (got {})'.format(self.default_area_filter)
                )

            # the total number of images acquired
            self.total_captures = 0

            # the number of images acquired since StartDevice() was called
            self.num_captures = 0

            # the number of images to average for each capture
            self.num_to_average = 0

            # the UI also has a Ready/Running button so we need to differentiate
            # between a capture() call and a button press
            self.capture_requested = False

            # checking this parameter seem to be more reliable than
            # checking self.GetData.DeviceRunning() in the self.capture() method
            self.acquired = False

            # put all components in a Panel
            self.panel = self.create_panel()

            # for the ActiveX buttons that are used
            self.buttons = []

            prefix = kwargs['prog_id_prefix']
            style = WS_CHILD | WS_VISIBLE

            # =================================================================
            # Load the necessary OCX objects
            # =================================================================

            self.GetData = self.load(prefix+'.GetDataCtrl.1', parent=self)
            self.GetData.CameraSelect = self.camera_index

            # handle events emitted by the GetData object
            self.handle_events(self.GetData)

            w, h = 300, int(kwargs.get('ui_size', 25))  # width and height of a button
            profile_height = 200  # the height of the Profile plots
            buttons_to_add = [
                (DataRayApp.BUTTON_CLIP_A, DataRayApp.BUTTON_CLIP_B),
                DataRayApp.BUTTON_STATUS,
                DataRayApp.BUTTON_MAJOR,
                DataRayApp.BUTTON_MINOR,
                DataRayApp.BUTTON_MEAN,
                DataRayApp.BUTTON_EFF_2W,
                DataRayApp.BUTTON_MAJ_ISO,
                DataRayApp.BUTTON_MIN_ISO,
                DataRayApp.BUTTON_ELP,
                DataRayApp.BUTTON_ELLIPSE,
                DataRayApp.BUTTON_ORIENTATION,
                DataRayApp.BUTTON_CROSSHAIR,
                DataRayApp.BUTTON_INC_POWER_MAJOR,
                DataRayApp.BUTTON_INC_POWER_MINOR,
                DataRayApp.BUTTON_INC_POWER_MEAN,
                DataRayApp.BUTTON_INC_POWER_AREA,
                DataRayApp.BUTTON_INC_P,
                DataRayApp.BUTTON_INC_IRR,
                DataRayApp.BUTTON_MEAN_THETA,

                # automatically draws XG or XP or XU if it was selected from the DataRay software
                (DataRayApp.BUTTON_XC, DataRayApp.BUTTON_YC),

                (DataRayApp.BUTTON_CENTROID, DataRayApp.BUTTON_RC),
                (DataRayApp.BUTTON_ADC_PEAK, DataRayApp.BUTTON_IMAGE_ZOOM),
                DataRayApp.BUTTON_PLATEAU_UNIFORMITY,
                DataRayApp.BUTTON_PK_TO_AVG,
            ]
            for i, button_id in enumerate(buttons_to_add):
                if isinstance(button_id, tuple):
                    n = len(button_id)
                    for j, sub_button_id in enumerate(button_id):
                        button = self.load(
                            prefix+'.ButtonCtrl.1', x=j*w//n, y=i*h, width=w//n,
                            height=h, parent=self.panel, style=style
                        )
                        button.ButtonID = sub_button_id
                        self.buttons.append(button)
                else:
                    button = self.load(
                        prefix+'.ButtonCtrl.1', x=0, y=i*h, width=w,
                        height=h, parent=self.panel, style=style
                    )
                    button.ButtonID = button_id
                    self.buttons.append(button)

            a = len(buttons_to_add) * h
            b = a - profile_height
            self.CCDimage = self.load(
                prefix+'.CCDimageCtrl.1', x=w, y=0, width=b,
                height=b, parent=self.panel, style=style
            )
            self.ThreeDview = self.load(
                prefix+'.ThreeDviewCtrl.1', x=w+b, y=0, width=b-3*h,
                height=b-3*h, parent=self.panel, style=style
            )
            self.PaletteBar = self.load(
                prefix+'.PaletteBarCtrl.1', x=w+2*b-3*h, y=0, width=h,
                height=b-3*h, parent=self.panel, style=style
            )

            i = 3
            button_ids = [DataRayApp.BUTTON_POWER, DataRayApp.BUTTON_GAIN_1, DataRayApp.BUTTON_EXPOSURE_1]
            for button_id in button_ids:
                button = self.load(
                    prefix+'.ButtonCtrl.1', x=w+b, y=b-i*h, width=b-2*h,
                    height=h, parent=self.panel, style=style
                )
                button.ButtonID = button_id
                self.buttons.append(button)
                i -= 1

            w2 = w + 2*b - 2*h
            self.ProfilesX = self.load(
                prefix+'.ProfilesCtrl.1', x=w, y=b, width=(w2-w)//2,
                height=profile_height, parent=self.panel, style=style
            )
            self.ProfilesX.ProfileID = DataRayApp.PROFILE_X
            self.ProfilesY = self.load(
                prefix+'.ProfilesCtrl.1', x=w+(w2-w)//2, y=b, width=(w2-w)//2,
                height=profile_height, parent=self.panel, style=style
            )
            self.ProfilesY.ProfileID = DataRayApp.PROFILE_Y

            # self.TriggerControl = self.load(prefix+'.TriggerControlCtrl.1')
            # self.TwoD = self.load(prefix+'.TwoDCtrl.1')

            # =================================================================
            # Average Menu
            # =================================================================
            ave_menu_values = [
                ('No averaging', 0),
                ('-', None),
                ('Averaging 2', 2),
                ('Averaging 5', 5),
                ('Averaging 10', 10),
                ('Averaging 20', 20),
                ('-', None),
                ('Continuous [1000]', 1000),
            ]
            self.ave_menu = Forms.MenuItem()
            self.ave_menu.Text = 'Average'
            n_averages = self.GetData.GetAverageNumber()
            for i, (name, value) in enumerate(ave_menu_values):
                item = Forms.MenuItem()
                item.Text = name
                item.Index = i
                item.Name = str(value)
                item.RadioCheck = True
                item.Checked = n_averages == value
                if name != '-':
                    item.Click += self.on_average_changed
                self.ave_menu.MenuItems.Add(item)

            # =================================================================
            # Filter Menu
            # =================================================================
            filter_menu_values = [
                ('No filtering', 0.0),
                ('Filter = 0.1% Full Scale', 0.1),
                ('Filter = 0.2% Full Scale', 0.2),
                ('Filter = 0.5% Full Scale', 0.5),
                ('Filter = 1.0% Full Scale', 1.0),
                ('Filter = 2.0% Full Scale', 2.0),
                ('Filter = 5.0% Full Scale', 5.0),
                ('Filter = 10.0% Full Scale', 10.0),
                ('-', None),
                ('Area filter 1 pixel', 1),
                ('Area filter 3 pixels', 2),
                ('Area filter 5 pixels', 3),
                ('Area filter 7 pixels', 4),
                ('Area filter 9 pixels', 5),
            ]
            self.filter_menu = Forms.MenuItem()
            self.filter_menu.Text = 'Filter'
            self.GetData.FilterValue = self.default_full_scale_filter
            self.GetData.WinCamFilter = self.default_area_filter
            for i, (name, value) in enumerate(filter_menu_values):
                item = Forms.MenuItem()
                item.Text = name
                item.Index = i
                if name.startswith('Area'):
                    item.Checked = self.GetData.WinCamFilter == value
                else:
                    item.Checked = self.GetData.FilterValue == value
                if name != '-':
                    item.Name = str(value)
                    item.RadioCheck = True
                    item.Click += self.on_filter_changed
                self.filter_menu.MenuItems.Add(item)

            # =================================================================
            # Setup Menu
            # =================================================================
            self.setup_menu = Forms.MenuItem()
            self.setup_menu.Text = 'Setup'

            index = 0

            dialog_menu_values = [
                ('Capture setup dialog', 13),
                ('-', None),
                ('Enter Wavelength...', 12),
                ('-', None),
                ('Numeric Display Modes...', 8),
                ('Set centroid cliplevel', 16),
                ('Enter Effective Width cliplevel', 25),
                ('Set geo-centroid cliplevel', 22),
                ('Setup Trigger', 21),
                ('ISO Options', 32),
                ('-', None),
            ]
            for name, value in dialog_menu_values:
                item = Forms.MenuItem()
                item.Text = name
                item.Index = index
                item.Name = str(value)
                if name != '-':
                    item.Click += self.on_open_dialog
                self.setup_menu.MenuItems.Add(item)
                index += 1

            major_minor_names = [
                'Default Major / Minor method',
                'Use ISO 11146 compliant diameters and angle',
                'DXX mode',
                '-',
            ]
            self.GetData.MajorMinorMethod = self.default_major_minor_method
            for i, name in enumerate(major_minor_names):
                item = Forms.MenuItem()
                item.Text = name
                item.Index = index
                item.Name = 'MajorMinorItem %d' % i
                if name != '-':
                    item.RadioCheck = True
                    item.Checked = self.GetData.MajorMinorMethod == i
                    item.Click += self.on_major_minor_method_changed
                self.setup_menu.MenuItems.Add(item)
                index += 1

            self.GetData.CentroidType = self.default_centroid_method
            for i in range(3):
                item = Forms.MenuItem()
                item.Text = 'Centroid Method %d' % i
                item.Index = index
                item.RadioCheck = True
                item.Checked = self.GetData.CentroidType == i
                item.Click += self.on_centroid_method_changed
                self.setup_menu.MenuItems.Add(item)
                index += 1

            # =================================================================
            # Create the Main menu bar
            # =================================================================
            self.main_menu = Forms.MainMenu()
            self.main_menu.MenuItems.AddRange((self.ave_menu, self.filter_menu, self.setup_menu))

            # =================================================================
            # Set up the Form
            # =================================================================
            self.Text = 'DataRay {} || Camera {}'.format(self.GetData.GetSoftwareVersion(), self.camera_index)
            self.FormBorderStyle = Forms.FormBorderStyle.FixedSingle
            self.MaximizeBox = False
            self.Size = System.Drawing.Size(w2+10, a+50)
            self.panel.Size = self.Size
            self.StartPosition = Forms.FormStartPosition.CenterScreen
            self.Menu = self.main_menu
            self.Controls.Add(self.panel)
            self.FormClosing += self.on_form_closing  # register a callback if the Close button is clicked

        def SendMessage(self, message, long_value, double_value):
            """Handler for a GetData.SendMessage event.

            Event fired every time a message is sent.
            """
            pass

        def DataReady(self):
            """Handler for a GetData.DataReady event.

            Event fired every time new data becomes ready.
            """
            if self.capture_requested and self.num_captures == self.num_to_average:
                self.stop_device()
                self.acquired = True
                self.capture_requested = False
            self.num_captures += 1
            self.total_captures += 1

        def wait_to_configure(self):
            Forms.MessageBox.Show(
                'Click OK when you have finished configuring the camera.',
                self.Text,  # the text in the titlebar
                Forms.MessageBoxButtons.OK,  # buttons
                Forms.MessageBoxIcon.Information,  # icon
                Forms.MessageBoxDefaultButton.Button1,  # default button
                Forms.MessageBoxOptions.ServiceNotification,  # bring the popup window to the front
            )

        def capture(self, timeout):
            """Capture an image."""
            self.stop_device()
            self.acquired = False
            self.capture_requested = True
            self.num_captures = 0
            self.num_to_average = self.GetData.GetAverageNumber()
            self.start_device()
            t0 = time.time()
            while not self.acquired:
                time.sleep(0.01)
                if time.time() - t0 > timeout:
                    if self.num_to_average == 0:
                        text = '1 image'
                    else:
                        text = '{} images'.format(self.num_to_average)
                    self.stop_device()
                    raise TimeoutError(
                        'TimeoutError: Could not capture {} in {} seconds.'.format(text, timeout)
                    )

            error = self.GetData.GetLastError()
            if error:
                self.stop_device()
                raise RuntimeError(error)

            return {
                'adc_peak_%': self.GetData.GetParameter(DataRayApp.BUTTON_ADC_PEAK) * 100.0,
                'area_filter': self.GetData.WinCamFilter,
                'centroid': self.get_centroid(),
                'centroid_filter_size': self.GetData.EffectiveCentroidFilterInPixels,
                'centroid_type': self.GetData.CentroidType,
                'clip_level_centroid': self.GetData.CentroidClipLevel,
                'clip_level_geo': self.GetData.GeoClipLevel,
                'crosshair': self.GetData.GetParameter(DataRayApp.BUTTON_CROSSHAIR),
                'eff_2w': self.GetData.GetParameter(DataRayApp.BUTTON_EFF_2W),
                'effective_centroid': self.get_effective_centroid(),
                'effective_geo_centroid': self.get_effective_geo_centroid(),
                'ellip': self.GetData.GetParameter(DataRayApp.BUTTON_ELLIPSE),
                'elp': self.GetData.GetParameter(DataRayApp.BUTTON_ELP),
                'exposure_time': self.GetData.Exposure(self.camera_index),
                'filter_full_scale': self.GetData.FilterValue,
                'image': self.GetData.GetWinCamDataAsVariant(),
                'image_zoom': self.GetData.GetParameter(DataRayApp.BUTTON_IMAGE_ZOOM),
                'imager_gain': self.GetData.ImagerGain,
                'inc_p': self.GetData.GetParameter(DataRayApp.BUTTON_INC_P),
                'inc_power_area': self.GetData.GetParameter(DataRayApp.BUTTON_INC_POWER_AREA),
                'inc_power_major': self.GetData.GetParameter(DataRayApp.BUTTON_INC_POWER_MAJOR),
                'inc_power_mean': self.GetData.GetParameter(DataRayApp.BUTTON_INC_POWER_MEAN),
                'inc_power_minor': self.GetData.GetParameter(DataRayApp.BUTTON_INC_POWER_MINOR),
                'is_fast_update': bool(self.GetData.FastUpdate),
                'is_full_resolution': self.GetData.CaptureIsFullResolution(),
                'maj_iso': self.GetData.GetParameter(DataRayApp.BUTTON_MAJ_ISO),
                'major': self.GetData.GetParameter(DataRayApp.BUTTON_MAJOR),
                'major_minor_method': self.GetData.MajorMinorMethod,
                'mean': self.GetData.GetParameter(DataRayApp.BUTTON_MEAN),
                'mean_theta': self.GetData.GetParameter(DataRayApp.BUTTON_MEAN_THETA),
                'min_iso': self.GetData.GetParameter(DataRayApp.BUTTON_MIN_ISO),
                'minor': self.GetData.GetParameter(DataRayApp.BUTTON_MINOR),
                'num_averages': self.GetData.GetAverageNumber(),
                'num_captures': self.total_captures,
                'orient': self.GetData.GetParameter(DataRayApp.BUTTON_ORIENTATION),
                'peak': self.get_peak(),
                'pixel_height_um': self.GetData.GetWinCamDPixelSize(1),
                'pixel_width_um': self.GetData.GetWinCamDPixelSize(0),
                'pk_to_avg': self.GetData.GetParameter(DataRayApp.BUTTON_PK_TO_AVG),
                'plateau_uniformity': self.GetData.GetParameter(DataRayApp.BUTTON_PLATEAU_UNIFORMITY),
                'profile_x': self.ProfilesX.GetProfileDataAsVariant(),
                'profile_y': self.ProfilesY.GetProfileDataAsVariant(),
                'shape': (self.GetData.GetVerticalPixels(), self.GetData.GetHorizontalPixels()),
                'roi': self.get_roi(),
                'xc': self.GetData.GetParameter(DataRayApp.BUTTON_XC),
                'xg': self.GetData.GetParameter(DataRayApp.BUTTON_XG),
                'xp': self.GetData.GetParameter(DataRayApp.BUTTON_XP),
                'xu': self.GetData.GetParameter(DataRayApp.BUTTON_XU),
                'yc': self.GetData.GetParameter(DataRayApp.BUTTON_YC),
                'yg': self.GetData.GetParameter(DataRayApp.BUTTON_YG),
                'yp': self.GetData.GetParameter(DataRayApp.BUTTON_YP),
                'yu': self.GetData.GetParameter(DataRayApp.BUTTON_YU),
            }

        def get_roi(self):
            x, y, w, h = (c_int32(), c_int32(), c_int32(), c_int32())
            self.GetData.GetROI(byref(x), byref(y), byref(w), byref(h))
            return x.value, y.value, w.value, h.value

        def get_effective_centroid(self):
            try:
                return (
                    self.GetData.GetEffectiveCentroidX(self.camera_index),
                    self.GetData.GetEffectiveCentroidY(self.camera_index)
                )
            except AttributeError:
                # Version 8.0D36 does not define these attributes
                return None, None

        def get_effective_geo_centroid(self):
            try:
                return (
                    self.GetData.GetEffectiveGeoCenterX(self.camera_index),
                    self.GetData.GetEffectiveGeoCenterY(self.camera_index)
                )
            except AttributeError:
                # Version 8.0D36 does not define these attributes
                return None, None

        def get_centroid(self):
            return (
                self.GetData.GetCentroidXlocation(),
                self.GetData.GetCentroidYlocation()
            )

        def get_peak(self):
            return (
                self.GetData.GetPeakXlocation(),
                self.GetData.GetPeakYlocation()
            )

        def on_form_closing(self, sender, event):
            event.Cancel = True
            Forms.MessageBox.Show(
                'The DataRay window must remain open to capture images.\nYou can only minimize the window.',
                self.Text,
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Exclamation,
            )

        def on_open_dialog(self, sender, event):
            self.GetData.OpenDialog(int(sender.Name))

        def on_major_minor_method_changed(self, sender, event):
            if sender.Checked:
                return

            for item in self.setup_menu.MenuItems.GetEnumerator():
                if item.Name.startswith('MajorMinorItem'):
                    item.Checked = item == sender

            self.GetData.MajorMinorMethod = int(sender.Name[-1])

        def on_centroid_method_changed(self, sender, event):
            if sender.Checked:
                return

            for item in self.setup_menu.MenuItems.GetEnumerator():
                if not item.Text.startswith('Centroid'):
                    continue
                item.Checked = item == sender

            self.GetData.CentroidType = int(sender.Text[-1])

        def on_average_changed(self, sender, event):
            if sender.Checked:
                return

            for item in self.ave_menu.MenuItems.GetEnumerator():
                item.Checked = item == sender

            self.GetData.SetAverageNumber(int(sender.Name))

        def on_filter_changed(self, sender, event):
            if sender.Checked:
                return

            if sender.Text.startswith('Area'):
                for item in self.filter_menu.MenuItems.GetEnumerator():
                    if item.Text.startswith('Area'):
                        item.Checked = item == sender
                self.GetData.WinCamFilter = int(sender.Name)
            else:
                for item in self.filter_menu.MenuItems.GetEnumerator():
                    if not item.Text.startswith('Area'):
                        item.Checked = item == sender
                self.GetData.FilterValue = float(sender.Name)

        def start_device(self):
            self.GetData.StartDevice()

        def stop_device(self):
            self.GetData.StopDevice()
