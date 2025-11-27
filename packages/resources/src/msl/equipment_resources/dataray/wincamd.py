"""Connect to a WinCamD beam-profiling camera from [DataRay](https://www.dataray.com/){:target="_blank"}.

Tested with the WinCamD-LCM-8.0E45 (x64) software version.
"""

# cSpell: ignore NOCLOSE ICONINFORMATION Dview cliplevel Xlocation Ylocation bitness
from __future__ import annotations

import time
from ctypes import byref, c_long
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

from msl.equipment.interfaces import SDK, MSLConnectionError
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from typing import Any

    from msl.loadlib.activex import Application, MenuItem
    from numpy.typing import NDArray

    from msl.equipment.schema import Equipment


class WinCamD(SDK, manufacturer=r"Data\s*Ray", model=r"WinCamD"):
    """Connect to a WinCamD beam-profiling camera from [DataRay](https://www.dataray.com/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        """Connect to a WinCamD beam-profiling camera from DataRay.

        The bitness (32 or 64 bit) of the DataRay Beam Profiling Software that
        is installed must match the bitness of the Python interpreter that is used
        to load the `DATARAYOCX` library.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the `WinCamD` class.

        Attributes: Connection Properties:
            area_filter (int | None): Area filter:

                * `1`: 1 pixel
                * `2`: 3 pixels
                * `3`: 5 pixels
                * `4`: 7 pixels
                * `5`: 9 pixels

                If `None`, use the value saved in the device firmware. _Default: `None`_
            camera_index (int): The camera to use (between 0 and 7). _Default: `0`_
            centroid_method (int | None): The centroid method to use (0, 1 or 2).
                If `None`, use the value saved in the device firmware. _Default: `None`_
            full_scale_filter (float | None): Percent full scale filter (0, 0.1, 0.2, 0.5, 1, 2, 5 or 10).
                If `None`, use the value saved in the device firmware. _Default: `None`_
            major_minor_method (int | None): The major/minor method to use (0, 1 or 2).
                If `None`, use the value saved in the device firmware. _Default: `None`_
            plateau_uniformity (bool | None): Whether to enable or disable plateau uniformity.
                If `None`, use the value saved in the device firmware. _Default: `None`_
            wavelength (float | None): The wavelength, in nm, of the incident light.
                If `None`, use the value saved in the device firmware. _Default: `None`_
            ui_size (int): The height, in pixels, of a button for the user interface. _Default: `25`_
        """
        from msl.loadlib.activex import WindowClassStyle  # noqa: PLC0415

        assert equipment.connection is not None  # noqa: S101
        prefix = equipment.connection.address[len("SDK::") :]
        super().__init__(
            equipment, libtype="activex", path=f"{prefix}.GetDataCtrl.1", class_style=WindowClassStyle.NOCLOSE
        )

        assert self.application is not None  # noqa: S101
        p = equipment.connection.properties

        self._ocx: _WinCam = _WinCam(
            app=self.application,
            sdk=self.sdk,
            prefix=prefix,
            camera_index=p.get("camera_index", 0),
            major_minor_method=p.get("major_minor_method"),
            centroid_method=p.get("centroid_method"),
            area_filter=p.get("area_filter"),
            full_scale_filter=p.get("full_scale_filter"),
            ui_size=p.get("ui_size", 25),
            plateau_uniformity=p.get("plateau_uniformity"),
        )

        wavelength = p.get("wavelength")
        if wavelength:
            self.wavelength = wavelength

        if not self.sdk.StartDriver():
            msg = "Cannot start the DataRay driver"
            raise RuntimeError(msg)

    @property
    def adc_peak_percent(self) -> float:
        """Returns the peak value as a percentage of the maximum possible ADC level."""
        return self._ocx.get_parameter(_Button.ADC_PEAK) * 100.0

    def capture(self, timeout: float | None = None) -> None:
        """Capture image.

        Args:
            timeout: The maximum number of seconds to wait to capture the image.
        """
        try:
            self._ocx.capture(timeout)
        except (RuntimeError, TimeoutError) as e:
            raise MSLConnectionError(self, message=str(e)) from None

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the `DATARAYOCX` library."""
        if hasattr(self, "_ocx") and self.application is not None:
            self._ocx.stop_device()
            self.application.close()
            super().disconnect()

    @property
    def centroid(self) -> tuple[float, float]:
        """Returns the `(x, y)` coordinate of the centroid."""
        x: float = self.sdk.GetCentroidXlocation()
        y: float = self.sdk.GetCentroidYlocation()
        return x, y

    @property
    def crosshair(self) -> float:
        """Returns the angle between the horizontal x-axis and the solid crosshair line, in degrees."""
        return self._ocx.get_parameter(_Button.CROSSHAIR)

    @property
    def effective_2w(self) -> float:
        """Returns the effective beam size, in um."""
        return self._ocx.get_parameter(_Button.EFF_2W)

    @property
    def ellipticity(self) -> float:
        """Returns the ratio between the minor/major axis."""
        return self._ocx.get_parameter(_Button.ELLIPSE)

    @property
    def exposure_time(self) -> float:
        """Returns the exposure time, in ms."""
        return self.sdk.Exposure(self._ocx.camera_index)

    @property
    def homogeneity(self) -> float:
        """Returns the 2D homogeneity of the beam (between 0 and 1)."""
        return self._ocx.get_parameter(_Button.HOMOGENEITY)

    @property
    def image(self) -> NDArray[np.int64]:
        """Returns the image data."""
        shape = self._ocx.get_shape()
        data = self.sdk.GetWinCamDataAsVariant()
        if not data:
            msg = "No valid images have been captured"
            raise MSLConnectionError(self, msg)
        return np.asarray(data).reshape(shape)

    @property
    def major(self) -> float:
        """Returns the beam size along the major axis, in um."""
        return self._ocx.get_parameter(_Button.MAJOR)

    @property
    def major_iso(self) -> float:
        """Returns the ISO 11146 beam size along the major axis, in um.

        The camera must be configured for ISO 11146 mode.
        """
        return self._ocx.get_parameter(_Button.MAJ_ISO)

    @property
    def mean(self) -> float:
        """Returns the mean beam size, in um."""
        return self._ocx.get_parameter(_Button.MEAN)

    @property
    def mean_theta(self) -> float:
        """Returns the DXX mean angle, in radians.

        The camera must be configured for DXX mode.
        """
        return self._ocx.get_parameter(_Button.MEAN_THETA)

    @property
    def minor(self) -> float:
        """Returns the beam size along the minor axis, in um."""
        return self._ocx.get_parameter(_Button.MINOR)

    @property
    def minor_iso(self) -> float:
        """Returns the ISO 11146 beam size along the minor axis, in um.

        The camera must be configured for ISO 11146 mode.
        """
        return self._ocx.get_parameter(_Button.MIN_ISO)

    @property
    def orientation(self) -> float:
        """Returns the angle between the x-axis and the major or minor axis closest to the x-axis, in degrees."""
        return self._ocx.get_parameter(_Button.ORIENTATION)

    @property
    def pk_to_avg(self) -> float:
        """Returns the peak to average value."""
        return self._ocx.get_parameter(_Button.PK_TO_AVG)

    @property
    def plateau_uniformity(self) -> float:
        """Returns the flatness of the plateau.

        A value between 0 and 1 denoting how closely the beam resembles a theoretically perfect flat-top beam.
        """
        return self._ocx.get_parameter(_Button.PLATEAU_UNIFORMITY)

    @property
    def pixel_size(self) -> tuple[float, float]:
        """Returns the `(width, height)` size, in um, of a pixel."""
        w: float = self.sdk.GetWinCamDPixelSize(0)
        h: float = self.sdk.GetWinCamDPixelSize(1)
        return w, h

    @property
    def profile_x(self) -> NDArray[np.int64]:
        """Returns the profile data along X."""
        return self._ocx.get_profile_x()

    @property
    def profile_y(self) -> NDArray[np.int64]:
        """Returns the profile data along Y."""
        return self._ocx.get_profile_y()

    @property
    def rc(self) -> float:
        """Returns the radial distance from the center of the sensor to the center of the crosshair position."""
        return self._ocx.get_parameter(_Button.RC)

    @property
    def roi(self) -> tuple[int, int, int, int]:
        """Returns the region of interest `(x, y, width, height)`."""
        x, y, w, h = (c_long(), c_long(), c_long(), c_long())
        self.sdk.GetROI(byref(x), byref(y), byref(w), byref(h))
        return x.value, y.value, w.value, h.value

    def wait_to_configure(self) -> None:
        """Wait until the camera has been configured.

        This is a blocking call and waits until the popup window is closed.
        """
        self._ocx.wait_to_configure()

    @property
    def wavelength(self) -> float:
        """Get/Set the wavelength, in nm, of the incident light."""
        return self.sdk.Wavelength * 1e3

    @wavelength.setter
    def wavelength(self, value: float) -> None:
        self.sdk.Wavelength = value / 1e3
        logger.debug("DataRay.Wavelength=%f", value)

    @property
    def xc(self) -> float:
        """Returns the centroid position along X, in um."""
        return self._ocx.get_parameter(_Button.XC)

    @property
    def xg(self) -> float:
        """Returns the geometric centroid position along X, in um."""
        return self._ocx.get_parameter(_Button.XG)

    @property
    def xp(self) -> float:
        """Returns the peak-intensity centroid position along X, in um."""
        return self._ocx.get_parameter(_Button.XP)

    @property
    def yc(self) -> float:
        """Returns the centroid position along Y, in um."""
        return self._ocx.get_parameter(_Button.YC)

    @property
    def yg(self) -> float:
        """Returns the geometric centroid position along Y, in um."""
        return self._ocx.get_parameter(_Button.YG)

    @property
    def yp(self) -> float:
        """Returns the peak-intensity centroid position along Y, in um."""
        return self._ocx.get_parameter(_Button.YP)

    @property
    def zoom_factor(self) -> float:
        """Returns the zoom factor of the image."""
        return self._ocx.get_parameter(_Button.IMAGE_ZOOM)


class _Button(IntEnum):
    """Button ID's."""

    EFF_2W = 95
    XC = 171
    YC = 172
    XG = 173
    YG = 174
    XP = 175
    YP = 176
    XU = 233
    YU = 234
    ELLIPSE = 177
    POWER = 178
    ORIENTATION = 179
    MAJOR = 180
    MINOR = 181
    MEAN = 182
    ADC_PEAK = 183
    MAJ_ISO = 226
    MIN_ISO = 227
    ELP = 228
    INC_POWER_MAJOR = 261
    INC_POWER_MINOR = 262
    INC_POWER_MEAN = 263
    INC_POWER_AREA = 264
    INC_P = 265
    INC_IRR = 266
    MEAN_THETA = 267
    PLATEAU_UNIFORMITY = 291
    HOMOGENEITY = 292
    CLIP_A = 294
    CLIP_B = 295
    STATUS = 297
    CENTROID = 298
    IMAGE_ZOOM = 301
    CROSSHAIR = 302
    EXPOSURE_1 = 409
    GAIN_1 = 421
    RC = 425
    PK_TO_AVG = 429


class _Profile(IntEnum):
    """Profile ID's."""

    X = 22
    Y = 23


class _WinCam:
    def __init__(  # noqa: C901, PLR0912, PLR0913, PLR0915
        self,
        *,
        app: Application,
        sdk: Any,  # noqa: ANN401
        prefix: str,
        camera_index: int,
        major_minor_method: int | None,
        centroid_method: int | None,
        area_filter: int | None,
        full_scale_filter: float | None,
        ui_size: int,
        plateau_uniformity: bool | None,
    ) -> None:
        """Configure the WinCamD Application."""
        from msl.loadlib.activex import MenuGroup, MessageBoxOption  # noqa: PLC0415

        self._msg_box_options: MessageBoxOption = (
            MessageBoxOption.OK | MessageBoxOption.ICONINFORMATION | MessageBoxOption.TOPMOST
        )

        self.camera_index: int = camera_index
        if camera_index < 0 or camera_index > 7:  # noqa: PLR2004
            msg = f"The camera index must be between 0 and 7 (got {camera_index})"
            raise ValueError(msg)

        if major_minor_method is not None and major_minor_method not in [0, 1, 2]:
            msg = f"The major/minor method must be 0, 1 or 2 (got {major_minor_method})"
            raise ValueError(msg)

        if centroid_method is not None and centroid_method not in [0, 1, 2]:
            msg = f"The centroid method must be 0, 1 or 2 (got {centroid_method})"
            raise ValueError(msg)

        if area_filter is not None and area_filter not in [1, 2, 3, 4, 5]:
            msg = f"The area-filter method must be between 1 and 5 (got {area_filter})"
            raise ValueError(msg)

        # the manual claims it can be between 0 and 10.1
        if full_scale_filter is not None and (full_scale_filter < 0 or full_scale_filter > 10.1):  # noqa: PLR2004
            msg = f"The full-scale-filter index must be between 0 and 10.1 (got {full_scale_filter})"
            raise ValueError(msg)

        # the number of images acquired since StartDevice() was called
        self.num_captures: int = 0

        # the number of images to average for each capture
        self.num_to_average: int = 1

        # the UI also has a Ready/Running button so we need to differentiate
        # between a capture() call and a button press
        self.capture_requested: bool = False

        # checking this parameter seem to be more reliable than
        # checking self.GetData.DeviceRunning() in the self.capture() method
        self.acquired: bool = False

        # for the ActiveX buttons that are used
        self.buttons: list[Any] = []

        # =================================================================
        # Load the necessary OCX objects
        # =================================================================

        self.app: Application = app
        self.GetData: Any = sdk
        self.GetData.CameraSelect = self.camera_index

        # handle events emitted by the GetData object
        self.app.handle_events(self.GetData, self)

        w, h = 300, ui_size  # width and height of a button
        profile_height = 200  # the height of the Profile plots
        buttons_to_add = [
            (_Button.CLIP_A, _Button.CLIP_B),
            _Button.STATUS,
            _Button.MAJOR,
            _Button.MINOR,
            _Button.MEAN,
            _Button.EFF_2W,
            _Button.MAJ_ISO,
            _Button.MIN_ISO,
            _Button.ELLIPSE,
            _Button.ORIENTATION,
            _Button.CROSSHAIR,
            _Button.MEAN_THETA,
            # automatically draws XG or XP or XU if it was selected from the DataRay software
            (_Button.XC, _Button.YC),
            (_Button.CENTROID, _Button.RC),
            (_Button.ADC_PEAK, _Button.IMAGE_ZOOM),
            _Button.PLATEAU_UNIFORMITY,
            _Button.HOMOGENEITY,
            _Button.PK_TO_AVG,
        ]
        for i, button_id in enumerate(buttons_to_add):
            if isinstance(button_id, tuple):
                n = len(button_id)
                for j, sub_button_id in enumerate(button_id):
                    button = self.app.load(f"{prefix}.ButtonCtrl.1", x=j * w // n, y=i * h, width=w // n, height=h)
                    button.ButtonID = sub_button_id
                    self.buttons.append(button)
            else:
                button = self.app.load(f"{prefix}.ButtonCtrl.1", x=0, y=i * h, width=w, height=h)
                button.ButtonID = button_id
                self.buttons.append(button)

        a = len(buttons_to_add) * h
        b = a - profile_height
        self.CCDimage: Any = self.app.load(f"{prefix}.CCDimageCtrl.1", x=w, y=0, width=b, height=b)
        self.ThreeDView: Any = self.app.load(
            f"{prefix}.ThreeDviewCtrl.1",
            x=w + b,
            y=0,
            width=b - 3 * h,
            height=b - 3 * h,
        )
        self.PaletteBar: Any = self.app.load(
            f"{prefix}.PaletteBarCtrl.1",
            x=w + 2 * b - 3 * h,
            y=0,
            width=h,
            height=b - 3 * h,
        )

        i = 3
        button_ids = [_Button.POWER, _Button.GAIN_1, _Button.EXPOSURE_1]
        for button_id in button_ids:
            button = self.app.load(
                f"{prefix}.ButtonCtrl.1",
                x=w + b,
                y=b - i * h,
                width=b - 2 * h,
                height=h,
            )
            button.ButtonID = button_id
            self.buttons.append(button)
            i -= 1

        w2 = w + 2 * b - 2 * h
        self.ProfilesX: Any = self.app.load(
            f"{prefix}.ProfilesCtrl.1",
            x=w,
            y=b,
            width=(w2 - w) // 2,
            height=profile_height,
        )
        self.ProfilesX.ProfileID = _Profile.X

        self.ProfilesY: Any = self.app.load(
            f"{prefix}.ProfilesCtrl.1",
            x=w + (w2 - w) // 2,
            y=b,
            width=(w2 - w) // 2,
            height=profile_height,
        )
        self.ProfilesY.ProfileID = _Profile.Y

        # =================================================================
        # Average Menu
        # =================================================================
        average = self.app.menu.create("Average")
        self.ave_group: MenuGroup = MenuGroup("average")
        self.app.menu.append_group(average, self.ave_group)

        ave_items = [
            ("No averaging", 0),
            ("-", -1),
            ("Average 2", 2),
            ("Average 5", 5),
            ("Average 10", 10),
            ("Average 20", 20),
            ("-", -1),
            ("Continuous [1000]", 1000),
            ("-", -1),
            ("Hold Max", 1),
        ]
        n_averages = self.GetData.GetAverageNumber()
        for text, ave in ave_items:
            if text == "-":
                self.ave_group.append_separator()
                continue

            item = self.ave_group.append(text=text, data=ave, callback=self.on_average_changed)
            if n_averages == ave:
                self.ave_group.checked = item

        # =================================================================
        # Filter Menu
        # =================================================================
        filtered = self.app.menu.create("Filter")

        if full_scale_filter is not None:
            self.GetData.FilterValue = full_scale_filter
        filter_value = float(self.GetData.FilterValue)

        self.full_scale_group: MenuGroup = MenuGroup("full-scale")
        self.app.menu.append_group(filtered, self.full_scale_group)

        full_scale_items = [
            ("No filtering", 0.0),
            ("Filter = 0.1% Full Scale", 0.1),
            ("Filter = 0.2% Full Scale", 0.2),
            ("Filter = 0.5% Full Scale", 0.5),
            ("Filter = 1.0% Full Scale", 1.0),
            ("Filter = 2.0% Full Scale", 2.0),
            ("Filter = 5.0% Full Scale", 5.0),
            ("Filter = 10.0% Full Scale", 10.0),
        ]
        for text, fs in full_scale_items:
            item = self.full_scale_group.append(text=text, data=fs, callback=self.on_filter_changed)
            if filter_value == fs:
                self.full_scale_group.checked = item

        self.app.menu.append_separator(filtered)

        if area_filter is not None:
            self.GetData.WinCamFilter = area_filter
        win_cam_filter = int(self.GetData.WinCamFilter)

        self.area_group: MenuGroup = MenuGroup("area")
        self.app.menu.append_group(filtered, self.area_group)

        area_items = [
            ("Area filter 1 pixel", 1),
            ("Area filter 3 pixels", 2),
            ("Area filter 5 pixels", 3),
            ("Area filter 7 pixels", 4),
            ("Area filter 9 pixels", 5),
        ]
        for text, area in area_items:
            item = self.area_group.append(text=text, data=area, callback=self.on_filter_changed)
            if win_cam_filter == area:
                self.area_group.checked = item

        self.app.menu.append_separator(filtered)
        self.outlier_filter: MenuItem = self.app.menu.append(
            filtered, text="Outlier filter", callback=self.on_filter_changed
        )
        self.outlier_filter.checked = bool(self.GetData.GetOutlierFilter())

        # =================================================================
        # Setup Menu
        # =================================================================
        setup = self.app.menu.create("Setup")
        dialog_menu_values = [
            ("Capture setup dialog", 13),
            ("-", -1),
            ("Enter Wavelength...", 12),
            ("-", -1),
            ("Numeric Display Modes...", 8),
            ("Set centroid cliplevel", 16),
            ("Enter Effective Width cliplevel", 25),
            ("Set geo-centroid cliplevel", 22),
            ("Setup Trigger", 21),
            ("ISO Options", 32),
            ("Show Beam Wanderer", 15),
            ("-", -1),
        ]
        for text, dialog in dialog_menu_values:
            if text == "-":
                self.app.menu.append_separator(setup)
            else:
                _ = self.app.menu.append(setup, text=text, data=dialog, callback=self.on_open_dialog)

        self.major_minor_group: MenuGroup = MenuGroup("major-minor")
        self.app.menu.append_group(setup, self.major_minor_group)

        plateau = self.app.menu.append(setup, "Enable Plateau Uniformity", callback=self.on_plateau)
        if plateau_uniformity is not None:
            self.GetData.UsePlateauUniformity = int(plateau_uniformity)
            plateau.checked = plateau_uniformity

        self.app.menu.append_separator(setup)

        if major_minor_method is not None:
            self.GetData.MajorMinorMethod = major_minor_method
        major_minor_method = int(self.GetData.MajorMinorMethod)

        major_minor_names = [
            "Default Major / Minor method",
            "Use ISO 11146 compliant diameters and angle",
            "DXX mode",
        ]
        for i, name in enumerate(major_minor_names):
            item = self.major_minor_group.append(name, data=i, callback=self.on_major_minor_method_changed)
            if major_minor_method == i:
                self.major_minor_group.checked = item

        self.app.menu.append_separator(setup)

        self.centroid_group: MenuGroup = MenuGroup("centroid")
        self.app.menu.append_group(setup, self.centroid_group)

        if centroid_method is not None:
            self.GetData.CentroidType = centroid_method
        centroid_method = int(self.GetData.CentroidType)
        for i in range(3):
            item = self.centroid_group.append(f"Centroid Method {i}", data=i, callback=self.on_centroid_method_changed)
            if centroid_method == i:
                self.centroid_group.checked = item

        # =================================================================
        # Set up the Window
        # =================================================================
        self._title: str = f"DataRay {self.GetData.GetSoftwareVersion()} || Camera {self.camera_index}"
        self.app.set_window_title(self._title)
        self.app.set_window_size(width=w2 + 10, height=a + 60)
        self.app.show()

    def SendMessage(self, *_: float) -> None:  # noqa: N802
        """Handler for a GetData.SendMessage event.

        Event fired every time a message is sent.
        """

    def DataReady(self) -> None:  # noqa: N802
        """Handler for a GetData.DataReady event.

        Event fired every time new data becomes ready.
        """
        self.num_captures += 1
        if self.capture_requested and self.num_captures == self.num_to_average:
            self.stop_device()
            self.acquired = True
            self.capture_requested = False

    def wait_to_configure(self) -> None:
        """Wait until the camera has been configured."""
        _ = self.app.message_box(
            title=self._title,
            text="Click OK when you have finished configuring the camera.",
            options=self._msg_box_options,
        )

    def capture(self, timeout: float | None) -> None:
        """Capture an image."""
        self.stop_device()
        self.acquired = False
        self.capture_requested = True
        self.num_captures = 0
        self.num_to_average = max(1, self.GetData.GetAverageNumber())
        self.start_device()

        t0 = time.time()
        while not self.acquired:
            self.app.wait_for_events(0.1)
            if timeout is not None and time.time() - t0 > timeout:
                self.stop_device()
                s = "" if self.num_to_average == 1 else "s"
                msg = f"TimeoutError: Could not capture {self.num_to_average} image{s} in {timeout} seconds."
                raise TimeoutError(msg)

        self.stop_device()
        error = str(self.GetData.GetLastError())
        if error:
            raise RuntimeError(error)

    def get_parameter(self, button_id: int) -> float:
        value: float = self.GetData.GetParameter(button_id)
        return value

    def get_profile_x(self) -> NDArray[np.int64]:
        """Get the profile data along X."""
        _, x = self.get_shape()
        return np.asarray(self.ProfilesX.GetProfileDataAsVariant())[:x]

    def get_profile_y(self) -> NDArray[np.int64]:
        """Get the profile data along Y."""
        y, _ = self.get_shape()
        return np.asarray(self.ProfilesY.GetProfileDataAsVariant())[:y]

    def get_shape(self) -> tuple[int, int]:
        """Get the image shape."""
        resolution: int = self.GetData.CaptureIsFullResolution()
        shape: tuple[int, int] = (self.GetData.GetVerticalPixels(), self.GetData.GetHorizontalPixels())
        if resolution == 1:
            return shape
        if resolution == 0:
            return shape[0] // 2, shape[1] // 2
        return shape[0] // 4, shape[1] // 4

    def on_average_changed(self, item: MenuItem) -> None:
        """Handle a value change in the Average menu."""
        if not item.checked:
            self.GetData.SetAverageNumber(item.data)
            self.ave_group.checked = item
            logger.debug("DataRayOCX.SetAverageNumber=%d", self.GetData.GetAverageNumber())

    def on_centroid_method_changed(self, item: MenuItem) -> None:
        """Handle a major/minor method value change in the Setup menu."""
        if not item.checked:
            self.GetData.CentroidType = item.data
            self.centroid_group.checked = item
            logger.debug("DataRayOCX.CentroidType=%d", self.GetData.CentroidType)

    def on_filter_changed(self, item: MenuItem) -> None:
        """Handle a value change in the Filter menu."""
        if item.text.startswith("Outlier"):
            self.GetData.ToggleOutlierFilter()
            self.outlier_filter.checked = self.GetData.GetOutlierFilter()
            self.area_group.checked = self.area_group[0]
            self.GetData.WinCamFilter = 1
            logger.debug("DataRayOCX.OutlierFilter toggled")
            logger.debug("DataRayOCX.WinCamFilter=%d", self.GetData.WinCamFilter)
        elif item.text.startswith("Area"):
            self.GetData.WinCamFilter = item.data
            self.area_group.checked = item
            logger.debug("DataRayOCX.WinCamFilter=%d", self.GetData.WinCamFilter)
            if item.data != 1:
                self.outlier_filter.checked = False
                if self.GetData.GetOutlierFilter():
                    self.GetData.ToggleOutlierFilter()
                    logger.debug("DataRayOCX.OutlierFilter toggled")
        else:
            self.GetData.FilterValue = item.data
            self.full_scale_group.checked = item
            logger.debug("DataRayOCX.FilterValue=%.1f", self.GetData.FilterValue)

    def on_major_minor_method_changed(self, item: MenuItem) -> None:
        """Handle a major/minor method value change in the Setup menu."""
        if not item.checked:
            self.GetData.MajorMinorMethod = item.data
            self.major_minor_group.checked = item
            logger.debug("DataRayOCX.MajorMinorMethod=%d", self.GetData.MajorMinorMethod)

    def on_open_dialog(self, item: MenuItem) -> None:
        """Handle an open-dialog request in the Setup menu."""
        self.GetData.OpenDialog(item.data)

    def on_plateau(self, item: MenuItem) -> None:
        """Handle enable/disable platform uniformity."""
        item.checked = not item.checked
        self.GetData.UsePlateauUniformity = int(item.checked)
        logger.debug("DataRayOCX.UsePlateauUniformity=%d", self.GetData.UsePlateauUniformity)

    def start_device(self) -> None:
        """Start the camera."""
        self.GetData.StartDevice()

    def stop_device(self) -> None:
        """Stop the camera."""
        self.GetData.StopDevice()
