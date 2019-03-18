"""
Load the 32-bit ``DATARAYOCX`` library using :ref:`msl-loadlib-welcome`.
"""
import os
import sys
import time

from msl.loadlib import Server32, SERVER_FILENAME

app = None
camera_ready = False
error_message = None
options = None


class DataRayOCX32(Server32):

    def __init__(self, host, port, quiet, **kwargs):
        """Communicates with the 32-bit ``DATARAYOCX`` library."""

        # The DataRay OCX library must be executed from within a GUI.
        # Calling LoadLibrary('DATARAYOCX.GetDataCtrl.1', 'com') works but
        # an exception will be raised when you try to call an OCX object.
        # Therefore we load a dummy DLL that does not get used ...
        mock_dll = os.path.join(os.path.dirname(sys.executable), '..', 'examples', 'loadlib', 'cpp_lib32')
        super(DataRayOCX32, self).__init__(mock_dll, 'cdll', host, port, quiet)

        # ... and create a .NET application to contain the ActiveX objects
        _create_app(**kwargs)
        if error_message:
            raise RuntimeError(error_message)
        app.Show()

    def wait_to_configure(self):
        """Wait until the camera has been configured."""
        app.wait_to_configure()

    def capture(self, timeout):
        """Capture an image."""
        return app.capture(timeout)


def _start_app():
    global app, camera_ready, error_message

    try:
        app = DataRayForm()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        error_message = 'Cannot load the DATARAYOCX library'
        return

    app.GetData.StopDevice()

    if not app.GetData.StartDriver():
        error_message = 'Cannot start the DataRay driver'
        return

    camera_ready = True
    WinForms.Application.Run(app)


def _create_app(**kwargs):
    global app, options
    options = kwargs
    thread = Thread(ThreadStart(_start_app))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()
    t0 = time.time()
    while not camera_ready:
        time.sleep(0.1)
        if time.time() - t0 > 10:
            return


# only create the .NET Form if running on the 32-bit Sever (see MSL-LoadLib)
if sys.executable.endswith(SERVER_FILENAME):
    import clr
    clr.AddReference('System.Windows.Forms')
    import System.Windows.Forms as WinForms
    from System.Drawing import Size
    from System.Threading import ApartmentState, Thread, ThreadStart

    # create the sys.coinit_flags attribute before importing comtypes
    # fixes -> OSError: [WinError -2147417850] Cannot change thread mode after it is set
    sys.coinit_flags = 0

    import ctypes
    import comtypes.client

    class DataRayForm(WinForms.Form):

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

        def __init__(self):
            self.camera_index = int(options.get('camera_index', 0))
            if self.camera_index < 0 or self.camera_index > 7:
                raise ValueError('DataRayError: the camera index must be between '
                                 '0 and 7, got %d' % self.camera_index)

            self.default_major_minor_method = int(options.get('major_minor_method', 0))
            if self.default_major_minor_method not in [0, 1, 2]:
                raise ValueError('DataRayError: the major/minor method must be '
                                 '0, 1 or 2 (got %d)' % self.default_major_minor_method)

            self.default_centroid_method = int(options.get('centroid_method', 0))
            if self.default_centroid_method not in [0, 1, 2]:
                raise ValueError('DataRayError: the centroid method must be '
                                 '0, 1 or 2 (got %d)' % self.default_centroid_method)

            # manual claims it can be between 0 and 10.1
            self.default_full_scale_filter = float(options.get('filter', 0.2))
            if self.default_full_scale_filter < 0 or self.default_full_scale_filter > 10.1:
                raise ValueError('DataRayError: the full scale filter index must be between '
                                 '0 and 10.1, got %f' % self.default_full_scale_filter)

            self.default_area_filter = int(options.get('area_filter', 1))
            if self.default_area_filter not in [1, 2, 3, 4, 5]:
                raise ValueError('DataRayError: the area filter method must be '
                                 'between 1 and 5 (got %d)' % self.default_area_filter)

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
            self.panel = WinForms.Panel()

            # =================================================================
            # Load the necessary OCX objects
            # =================================================================
            self.GetData = self.load('DATARAYOCX.GetDataCtrl.1')
            self.GetData.CameraSelect = self.camera_index

            w, h = 300, int(options.get('ui_size', 25))  # width and height of a button
            profile_height = 200  # the height of the Profile plots
            buttons_to_add = [
                (DataRayForm.BUTTON_CLIP_A, DataRayForm.BUTTON_CLIP_B),
                DataRayForm.BUTTON_STATUS,
                DataRayForm.BUTTON_MAJOR,
                DataRayForm.BUTTON_MINOR,
                DataRayForm.BUTTON_MEAN,
                DataRayForm.BUTTON_EFF_2W,
                DataRayForm.BUTTON_MAJ_ISO,
                DataRayForm.BUTTON_MIN_ISO,
                DataRayForm.BUTTON_ELP,
                DataRayForm.BUTTON_ELLIPSE,
                DataRayForm.BUTTON_ORIENTATION,
                DataRayForm.BUTTON_CROSSHAIR,
                DataRayForm.BUTTON_INC_POWER_MAJOR,
                DataRayForm.BUTTON_INC_POWER_MINOR,
                DataRayForm.BUTTON_INC_POWER_MEAN,
                DataRayForm.BUTTON_INC_POWER_AREA,
                DataRayForm.BUTTON_INC_P,
                DataRayForm.BUTTON_INC_IRR,
                DataRayForm.BUTTON_MEAN_THETA,

                # automatically draws XG or XP or XU if it was selected from the 'official' DataRay software
                (DataRayForm.BUTTON_XC, DataRayForm.BUTTON_YC),

                (DataRayForm.BUTTON_CENTROID, DataRayForm.BUTTON_RC),
                (DataRayForm.BUTTON_ADC_PEAK, DataRayForm.BUTTON_IMAGE_ZOOM),
                DataRayForm.BUTTON_PLATEAU_UNIFORMITY,
                DataRayForm.BUTTON_PK_TO_AVG,
            ]
            self.buttons = []
            for i, button_id in enumerate(buttons_to_add):
                if isinstance(button_id, tuple):
                    n = len(button_id)
                    for j, sub_button_id in enumerate(button_id):
                        self.buttons.append(self.load('DATARAYOCX.ButtonCtrl.1', x=j*w//n, y=i*h, w=w//n, h=h))
                        self.buttons[-1].ButtonID = sub_button_id
                else:
                    self.buttons.append(self.load('DATARAYOCX.ButtonCtrl.1', x=0, y=i*h, w=w, h=h))
                    self.buttons[-1].ButtonID = button_id

            a = len(buttons_to_add) * h
            b = a - profile_height
            self.CCDimage = self.load('DATARAYOCX.CCDimageCtrl.1', x=w, y=0, w=b, h=b)
            self.ThreeDview = self.load('DATARAYOCX.ThreeDviewCtrl.1', x=w+b, y=0, w=b-3*h, h=b-3*h)
            self.PaletteBar = self.load('DATARAYOCX.PaletteBarCtrl.1', x=w+2*b-3*h, y=0, w=h, h=b-3*h)

            i = 3
            button_ids = [DataRayForm.BUTTON_POWER, DataRayForm.BUTTON_GAIN_1, DataRayForm.BUTTON_EXPOSURE_1]
            for button_id in button_ids:
                self.buttons.append(self.load('DATARAYOCX.ButtonCtrl.1', x=w+b, y=b-i*h, w=b-2*h, h=h))
                self.buttons[-1].ButtonID = button_id
                i -= 1

            w2 = w + 2*b - 2*h
            self.ProfilesX = self.load('DATARAYOCX.ProfilesCtrl.1', x=w, y=b, w=(w2-w)//2, h=profile_height)
            self.ProfilesX.ProfileID = DataRayForm.PROFILE_X
            self.ProfilesY = self.load('DATARAYOCX.ProfilesCtrl.1', x=w+(w2-w)//2, y=b, w=(w2-w)//2, h=profile_height)
            self.ProfilesY.ProfileID = DataRayForm.PROFILE_Y

            # self.TriggerControl = self.load('DATARAYOCX.TriggerControlCtrl.1')
            # self.TwoD = self.load('DATARAYOCX.TwoDCtrl.1')

            # set the event-handler method to be self.DataReady
            self.event_sink = comtypes.client.GetEvents(self.GetData, self)

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
            self.ave_menu = WinForms.MenuItem()
            self.ave_menu.Text = 'Average'
            n_averages = self.GetData.GetAverageNumber()
            for i, (name, value) in enumerate(ave_menu_values):
                item = WinForms.MenuItem()
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
            self.filter_menu = WinForms.MenuItem()
            self.filter_menu.Text = 'Filter'
            self.GetData.FilterValue = self.default_full_scale_filter
            self.GetData.WinCamFilter = self.default_area_filter
            for i, (name, value) in enumerate(filter_menu_values):
                item = WinForms.MenuItem()
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
            self.setup_menu = WinForms.MenuItem()
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
                item = WinForms.MenuItem()
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
                item = WinForms.MenuItem()
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
                item = WinForms.MenuItem()
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
            self.main_menu = WinForms.MainMenu()
            self.main_menu.MenuItems.AddRange((self.ave_menu, self.filter_menu, self.setup_menu))

            # =================================================================
            # Set up the Form
            # =================================================================
            self.Text = 'DataRay Beam Profiler || Camera %d' % self.camera_index
            self.FormBorderStyle = WinForms.FormBorderStyle.FixedSingle
            self.MaximizeBox = False
            self.Size = Size(w2+10, a+50)
            self.panel.Size = self.Size
            self.StartPosition = WinForms.FormStartPosition.CenterScreen
            self.Menu = self.main_menu
            self.Controls.Add(self.panel)
            self.FormClosing += self.on_form_closing  # register a callback if the Close button is clicked

        def load(self, prog_id, x=0, y=0, w=1, h=1):
            # the following mimics what is done in wxPython
            # See -> wx.lib.activex.ActiveXCtrl

            # don't show the GetDataCtrl in the UI
            parent = self if prog_id.endswith('GetDataCtrl.1') else self.panel

            ctypes.windll.atl.AtlAxWinInit()
            h_instance = ctypes.windll.kernel32.GetModuleHandleA(None)
            hwnd = ctypes.windll.user32.CreateWindowExA(
                0, b'AtlAxWin', prog_id.encode(), 1442840576,
                x, y, w, h, parent.Handle.ToInt32(), None, h_instance, 0
            )

            if hwnd == 0:
                sys.stderr.write('DataRayError: Cannot create handle in user32.CreateWindowExA\n')
                raise RuntimeError

            # get the Interface for the ActiveX control
            unknown = ctypes.POINTER(comtypes.IUnknown)()
            res = ctypes.windll.atl.AtlAxGetControl(hwnd, ctypes.byref(unknown))
            if res != 0:
                sys.stderr.write('DataRayError: Cannot create ActiveX control in atl.AtlAxGetControl\n')
                raise RuntimeError

            return comtypes.client.GetBestInterface(unknown)

        def DataReady(self):
            """Automatically called every time new data becomes available."""
            if self.capture_requested and self.num_captures == self.num_to_average:
                self.GetData.StopDevice()
                self.acquired = True
                self.capture_requested = False
            self.num_captures += 1
            self.total_captures += 1

        def wait_to_configure(self):
            WinForms.MessageBox.Show(
                'Click OK when you have finished configuring the camera.',
                self.Text,  # the text in the titlebar
                WinForms.MessageBoxButtons.OK,  # buttons
                WinForms.MessageBoxIcon.Information,  # icon
                WinForms.MessageBoxButtons.OK,  # default button
                WinForms.MessageBoxOptions.ServiceNotification,  # bring the popup window to the front
            )

        def capture(self, timeout):
            """Capture an image."""
            self.GetData.StopDevice()  # in case it was running from a Button click
            self.acquired = False
            self.capture_requested = True
            t0 = time.time()
            self.num_captures = 0
            self.num_to_average = self.GetData.GetAverageNumber()
            self.GetData.StartDevice()
            while not self.acquired:
                time.sleep(0.01)
                if time.time() - t0 > timeout:
                    if self.num_to_average == 0:
                        text = '1 image'
                    else:
                        text = '{} images'.format(self.num_to_average)
                    raise TimeoutError('Timeout. Could not capture {} in {} seconds.'
                                       .format(text, timeout))

            error = self.GetData.GetLastError()
            if error:
                raise RuntimeError(error)

            return {
                'adc_peak_%': self.GetData.GetParameter(DataRayForm.BUTTON_ADC_PEAK) * 100.0,
                'area_filter': self.GetData.WinCamFilter,
                'centroid': self.get_centroid(),
                'centroid_filter_size': self.GetData.EffectiveCentroidFilterInPixels,
                'centroid_type': self.GetData.CentroidType,
                'clip_level_centroid': self.GetData.CentroidClipLevel,
                'clip_level_geo': self.GetData.GeoClipLevel,
                'crosshair': self.GetData.GetParameter(DataRayForm.BUTTON_CROSSHAIR),
                'eff_2w': self.GetData.GetParameter(DataRayForm.BUTTON_EFF_2W),
                'effective_centroid': self.get_effective_centroid(),
                'effective_geo_centroid': self.get_effective_geo_centroid(),
                'ellip': self.GetData.GetParameter(DataRayForm.BUTTON_ELLIPSE),
                'elp': self.GetData.GetParameter(DataRayForm.BUTTON_ELP),
                'exposure_time': self.GetData.Exposure(self.camera_index),
                'filter_full_scale': self.GetData.FilterValue,
                'image': self.GetData.GetWinCamDataAsVariant(),
                'image_zoom': self.GetData.GetParameter(DataRayForm.BUTTON_IMAGE_ZOOM),
                'imager_gain': self.GetData.ImagerGain,
                'inc_p': self.GetData.GetParameter(DataRayForm.BUTTON_INC_P),
                'inc_power_area': self.GetData.GetParameter(DataRayForm.BUTTON_INC_POWER_AREA),
                'inc_power_major': self.GetData.GetParameter(DataRayForm.BUTTON_INC_POWER_MAJOR),
                'inc_power_mean': self.GetData.GetParameter(DataRayForm.BUTTON_INC_POWER_MEAN),
                'inc_power_minor': self.GetData.GetParameter(DataRayForm.BUTTON_INC_POWER_MINOR),
                'is_fast_update': bool(self.GetData.FastUpdate),
                'is_full_resolution': self.GetData.CaptureIsFullResolution(),
                'maj_iso': self.GetData.GetParameter(DataRayForm.BUTTON_MAJ_ISO),
                'major': self.GetData.GetParameter(DataRayForm.BUTTON_MAJOR),
                'major_minor_method': self.GetData.MajorMinorMethod,
                'mean': self.GetData.GetParameter(DataRayForm.BUTTON_MEAN),
                'mean_theta': self.GetData.GetParameter(DataRayForm.BUTTON_MEAN_THETA),
                'min_iso': self.GetData.GetParameter(DataRayForm.BUTTON_MIN_ISO),
                'minor': self.GetData.GetParameter(DataRayForm.BUTTON_MINOR),
                'num_averages': self.GetData.GetAverageNumber(),
                'num_captures': self.total_captures,
                'orient': self.GetData.GetParameter(DataRayForm.BUTTON_ORIENTATION),
                'peak': self.get_peak(),
                'pixel_height_um': self.GetData.GetWinCamDPixelSize(1),
                'pixel_width_um': self.GetData.GetWinCamDPixelSize(0),
                'pk_to_avg': self.GetData.GetParameter(DataRayForm.BUTTON_PK_TO_AVG),
                'plateau_uniformity': self.GetData.GetParameter(DataRayForm.BUTTON_PLATEAU_UNIFORMITY),
                'profile_x': self.ProfilesX.GetProfileDataAsVariant(),
                'profile_y': self.ProfilesY.GetProfileDataAsVariant(),
                'shape': (self.GetData.GetVerticalPixels(), self.GetData.GetHorizontalPixels()),
                'roi': self.get_roi(),
                'xc': self.GetData.GetParameter(DataRayForm.BUTTON_XC),
                'xg': self.GetData.GetParameter(DataRayForm.BUTTON_XG),
                'xp': self.GetData.GetParameter(DataRayForm.BUTTON_XP),
                'xu': self.GetData.GetParameter(DataRayForm.BUTTON_XU),
                'yc': self.GetData.GetParameter(DataRayForm.BUTTON_YC),
                'yg': self.GetData.GetParameter(DataRayForm.BUTTON_YG),
                'yp': self.GetData.GetParameter(DataRayForm.BUTTON_YP),
                'yu': self.GetData.GetParameter(DataRayForm.BUTTON_YU),
            }

        def get_roi(self):
            x, y, w, h = (ctypes.c_int32(), ctypes.c_int32(), ctypes.c_int32(), ctypes.c_int32())
            self.GetData.GetROI(ctypes.byref(x), ctypes.byref(y), ctypes.byref(w), ctypes.byref(h))
            return x.value, y.value, w.value, h.value

        def get_effective_centroid(self):
            return (self.GetData.GetEffectiveCentroidX(self.camera_index),
                    self.GetData.GetEffectiveCentroidY(self.camera_index))

        def get_effective_geo_centroid(self):
            return (self.GetData.GetEffectiveGeoCenterX(self.camera_index),
                    self.GetData.GetEffectiveGeoCentery(self.camera_index))

        def get_centroid(self):
            return (self.GetData.GetCentroidXlocation(),
                    self.GetData.GetCentroidYlocation())

        def get_peak(self):
            return (self.GetData.GetPeakXlocation(),
                    self.GetData.GetPeakYlocation())

        def on_form_closing(self, sender, event):
            event.Cancel = True
            WinForms.MessageBox.Show(
                'The DataRay window must remain open to capture images.\nYou can minimize the window.',
                self.Text,
                WinForms.MessageBoxButtons.OK,
                WinForms.MessageBoxIcon.Exclamation,
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
