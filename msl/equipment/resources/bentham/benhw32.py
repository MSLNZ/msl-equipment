"""
A wrapper around the 32-bit Bentham ``benhw32_cdecl`` SDK.
"""
from __future__ import annotations

from ctypes import POINTER
from ctypes import c_char_p
from ctypes import c_double
from ctypes import c_int
from ctypes import c_long
from ctypes import c_short
from ctypes import create_string_buffer

from msl.loadlib import Server32

from msl.equipment.resources.utils import HINSTANCE


class Bentham32(Server32):

    def __init__(self, host, port, quiet, **kwargs):
        """A wrapper around the 32-bit Bentham ``benhw32_cdecl`` SDK.

        Do not instantiate this class directly.
        
        The SDK is provided for 32-bit Windows only. This module is run on
        a 32-bit :class:`Server <msl.loadlib.server32.Server32>` so that the
        the :class:`~.benhw64.Bentham` class can be run on a 64-bit Python
        interpreter in order to access the functions in the SDK from a 64-bit
        process.
        """
        super(Bentham32, self).__init__(kwargs['lib_path'], 'cdll', host, port, quiet)

        self.lib.BI_automeasure.restype = c_int
        self.lib.BI_automeasure.argtypes = [POINTER(c_double)]
        self.lib.BI_autorange.restype = c_int
        self.lib.BI_autorange.argtypes = []
        self.lib.BI_build_group.restype = c_int
        self.lib.BI_build_group.argtypes = []
        self.lib.BI_build_system_model.restype = c_int
        self.lib.BI_build_system_model.argtypes = [c_char_p, c_char_p]
        self.lib.BI_close.restype = c_int
        self.lib.BI_close.argtypes = []
        self.lib.BI_close_shutter.restype = c_int
        self.lib.BI_close_shutter.argtypes = []
        self.lib.BI_component_select_wl.restype = c_int
        self.lib.BI_component_select_wl.argtypes = [c_char_p, c_double, POINTER(c_long)]
        self.lib.BI_get.restype = c_int
        self.lib.BI_get.argtypes = [c_char_p, c_int, c_int, POINTER(c_double)]
        self.lib.BI_get_c_group.restype = c_int
        self.lib.BI_get_c_group.argtypes = [POINTER(c_int)]
        self.lib.BI_get_component_list.restype = c_int
        self.lib.BI_get_component_list.argtypes = [c_char_p]
        self.lib.BI_get_group.restype = c_int
        self.lib.BI_get_group.argtypes = [c_int, c_char_p]
        self.lib.BI_get_hardware_type.restype = c_int
        self.lib.BI_get_hardware_type.argtypes = [c_char_p, POINTER(c_int)]
        self.lib.BI_get_mono_items.restype = c_int
        self.lib.BI_get_mono_items.argtypes = [c_char_p, c_char_p]
        self.lib.BI_get_no_of_dark_currents.restype = c_int
        self.lib.BI_get_no_of_dark_currents.argtypes = [POINTER(c_int)]
        self.lib.BI_get_zero_calibration_info.restype = c_int
        self.lib.BI_get_zero_calibration_info.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double)]
        self.lib.BI_group_add.restype = c_int
        self.lib.BI_group_add.argtypes = [c_char_p, c_int]
        self.lib.BI_group_remove.restype = c_int
        self.lib.BI_group_remove.argtypes = [c_char_p, c_int]
        self.lib.BI_initialise.restype = c_int
        self.lib.BI_initialise.argtypes = []
        self.lib.BI_load_setup.restype = c_int
        self.lib.BI_load_setup.argtypes = [c_char_p]
        self.lib.BI_measurement.restype = c_int
        self.lib.BI_measurement.argtypes = [POINTER(c_double)]
        self.lib.BI_multi_autorange.restype = c_int
        self.lib.BI_multi_autorange.argtypes = []
        self.lib.BI_multi_get_no_of_dark_currents.restype = c_int
        self.lib.BI_multi_get_no_of_dark_currents.argtypes = [c_int, POINTER(c_int)]
        self.lib.BI_multi_get_zero_calibration_info.restype = c_int
        self.lib.BI_multi_get_zero_calibration_info.argtypes = [c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double)]
        self.lib.BI_multi_initialise.restype = c_int
        self.lib.BI_multi_initialise.argtypes = []
        self.lib.BI_multi_measurement.restype = c_int
        self.lib.BI_multi_measurement.argtypes = [POINTER(c_double)]
        self.lib.BI_multi_select_wavelength.restype = c_int
        self.lib.BI_multi_select_wavelength.argtypes = [c_double, POINTER(c_long)]
        self.lib.BI_multi_zero_calibration.restype = c_int
        self.lib.BI_multi_zero_calibration.argtypes = [c_double, c_double]
        self.lib.BI_park.restype = c_int
        self.lib.BI_park.argtypes = []
        self.lib.BI_read.restype = c_int
        self.lib.BI_read.argtypes = [c_char_p, c_short, POINTER(c_short), c_char_p]
        self.lib.BI_report_error.restype = c_int
        self.lib.BI_report_error.argtypes = []
        self.lib.BI_save_setup.restype = c_int
        self.lib.BI_save_setup.argtypes = [c_char_p]
        self.lib.BI_select_wavelength.restype = c_int
        self.lib.BI_select_wavelength.argtypes = [c_double, POINTER(c_long)]
        self.lib.BI_send.restype = c_int
        self.lib.BI_send.argtypes = [c_char_p, c_char_p]
        self.lib.BI_set.restype = c_int
        self.lib.BI_set.argtypes = [c_char_p, c_int, c_int, c_double]
        self.lib.BI_trace.restype = c_int
        self.lib.BI_trace.argtypes = [c_int]
        self.lib.BI_use_group.restype = c_int
        self.lib.BI_use_group.argtypes = [c_int]
        self.lib.BI_version.restype = None
        self.lib.BI_version.argtypes = [c_char_p]
        self.lib.BI_zero_calibration.restype = c_int
        self.lib.BI_zero_calibration.argtypes = [c_double, c_double]
        self.lib.BI_camera_get_zero_calibration_info.restype = c_int
        self.lib.BI_camera_get_zero_calibration_info.argtypes = [c_char_p, POINTER(c_double), POINTER(c_double), POINTER(c_double)]
        self.lib.BI_camera_measurement.restype = c_int
        self.lib.BI_camera_measurement.argtypes = [c_char_p, c_int, POINTER(c_double)]
        self.lib.BI_camera_zero_calibration.restype = c_int
        self.lib.BI_camera_zero_calibration.argtypes = [c_char_p, c_double, c_double]
        self.lib.BI_delete_group.restype = c_int
        self.lib.BI_delete_group.argtypes = [c_int]
        self.lib.BI_display_advanced_window.restype = c_int
        self.lib.BI_display_advanced_window.argtypes = [c_char_p, HINSTANCE]
        self.lib.BI_display_setup_window.restype = c_int
        self.lib.BI_display_setup_window.argtypes = [c_char_p, HINSTANCE]
        self.lib.BI_get_log.restype = c_int
        self.lib.BI_get_log.argtypes = [c_char_p]
        self.lib.BI_get_log_size.restype = c_int
        self.lib.BI_get_log_size.argtypes = [POINTER(c_int)]
        self.lib.BI_get_max_bw.restype = c_int
        self.lib.BI_get_max_bw.argtypes = [c_int, c_double, c_double, POINTER(c_double)]
        self.lib.BI_get_min_step.restype = c_int
        self.lib.BI_get_min_step.argtypes = [c_int, c_double, c_double, POINTER(c_double)]
        self.lib.BI_get_n_groups.restype = c_int
        self.lib.BI_get_n_groups.argtypes = [POINTER(c_int)]
        self.lib.BI_get_str.restype = c_int
        self.lib.BI_get_str.argtypes = [c_char_p, c_int, c_int, c_char_p]
        self.lib.BI_Mapped_Logging.restype = None
        self.lib.BI_Mapped_Logging.argtypes = [c_int]
        self.lib.BI_multi_automeasure.restype = c_int
        self.lib.BI_multi_automeasure.argtypes = [POINTER(c_double)]
        self.lib.BI_multi_park.restype = c_int
        self.lib.BI_multi_park.argtypes = []
        self.lib.BI_start_log.restype = c_int
        self.lib.BI_start_log.argtypes = [c_char_p]
        self.lib.BI_stop_log.restype = c_int
        self.lib.BI_stop_log.argtypes = [c_char_p]

    def auto_measure(self):
        reading = c_double()
        ret = self.lib.BI_automeasure(reading)
        return ret, reading.value

    def auto_range(self):
        return self.lib.BI_autorange()

    def build_group(self):
        return self.lib.BI_build_group()

    def build_system_model(self, path):
        p_file_name = create_string_buffer(path.encode())
        p_description = create_string_buffer(256)
        ret = self.lib.BI_build_system_model(p_file_name, p_description)
        return ret, p_description.raw.decode()

    def close(self):
        return self.lib.BI_close()

    def close_shutter(self):
        return self.lib.BI_close_shutter()

    def component_select_wl(self, p_id, wavelength):
        p_delay = c_long()
        ret = self.lib.BI_component_select_wl(p_id, wavelength, p_delay)
        return ret, p_delay.value

    def get(self, hw_id, token, index):
        p_id = create_string_buffer(hw_id.encode())
        p_value = c_double()
        ret = self.lib.BI_get(p_id, token, index, p_value)
        return ret, p_value.value

    def get_c_group(self, n):
        _n = c_int(n)
        return self.lib.BI_get_c_group(_n)

    def get_component_list(self):
        comp_list = create_string_buffer(256)
        ret = self.lib.BI_get_component_list(comp_list)
        return ret, comp_list.raw.decode().split(',')

    def get_group(self, group):
        p_description = create_string_buffer(256)
        ret = self.lib.BI_get_group(group, p_description)
        return ret, p_description.raw.decode()

    def get_hardware_type(self, hw_id):
        p_hw_id = create_string_buffer(hw_id.encode())
        hardware_type = c_int()
        ret = self.lib.BI_get_hardware_type(p_hw_id, hardware_type)
        return ret, hardware_type.value

    def get_mono_items(self, hw_id):
        p_mono_id = create_string_buffer(hw_id.encode())
        p_items = create_string_buffer(256)
        ret = self.lib.BI_get_mono_items(p_mono_id, p_items)
        return ret, p_items.raw.decode().split(',')

    def get_no_of_dark_currents(self):
        return self.lib.BI_get_no_of_dark_currents()

    def get_zero_calibration_info(self):
        return self.lib.BI_get_zero_calibration_info()

    def group_add(self, p_id, group):
        return self.lib.BI_group_add(p_id, group)

    def group_remove(self, p_id, group):
        return self.lib.BI_group_remove(p_id, group)

    def initialise(self):
        return self.lib.BI_initialise()

    def load_setup(self, path):
        p_file_name = create_string_buffer(path.encode())
        return self.lib.BI_load_setup(p_file_name)

    def measurement(self):
        return self.lib.BI_measurement()

    def multi_auto_range(self):
        return self.lib.BI_multi_autorange()

    def multi_get_no_of_dark_currents(self, group):
        no_of_values = c_int()
        ret = self.lib.BI_multi_get_no_of_dark_currents(group, no_of_values)
        return ret, no_of_values.value

    def multi_get_zero_calibration_info(self, group):
        wavelength = c_double()
        dark_current = c_double()
        adc_offset = c_double()
        ret = self.lib.BI_multi_get_zero_calibration_info(group, wavelength, dark_current, adc_offset)
        return ret, wavelength.value, dark_current.value, adc_offset.value

    def multi_initialise(self):
        return self.lib.BI_multi_initialise()

    def multi_measurement(self):
        return self.lib.BI_multi_measurement()

    def multi_select_wavelength(self, wavelength):
        p_delay = c_long()
        ret = self.lib.BI_multi_select_wavelength(wavelength, p_delay)
        return ret, p_delay.value

    def multi_zero_calibration(self, start_wavelength, stop_wavelength):
        return self.lib.BI_multi_zero_calibration(start_wavelength, stop_wavelength)

    def park(self):
        return self.lib.BI_park()

    def read(self, p_message, buffer_size, p_id):
        chars_read = c_short()
        ret = self.lib.BI_read(p_message, buffer_size, chars_read, p_id)
        return ret, chars_read.value

    def report_error(self):
        return self.lib.BI_report_error()

    def save_setup(self, p_file_name):
        return self.lib.BI_save_setup(p_file_name)

    def select_wavelength(self, wavelength):
        p_delay = c_long()
        ret = self.lib.BI_select_wavelength(wavelength, p_delay)
        return ret, p_delay.value

    def send(self, p_message, p_id):
        return self.lib.BI_send(p_message, p_id)

    def set(self, hw_id, token, index, value):
        p_id = create_string_buffer(hw_id.encode())
        return self.lib.BI_set(p_id, token, index, value)

    def trace(self, on):
        return self.lib.BI_trace(on)

    def use_group(self, group):
        return self.lib.BI_use_group(group)

    def get_version(self):
        version = create_string_buffer(80)
        self.lib.BI_version(version)
        return version.raw.decode()

    def zero_calibration(self, start_wavelength, stop_wavelength):
        return self.lib.BI_zero_calibration(start_wavelength, stop_wavelength)

    def camera_get_zero_calibration_info(self, p_id):
        wavelength = c_double()
        dark_current = c_double()
        adc_offset = c_double()
        ret = self.lib.BI_camera_get_zero_calibration_info(p_id, wavelength, dark_current, adc_offset)
        return ret, wavelength.value, dark_current.value, adc_offset.value

    def camera_measurement(self, p_id, num):
        readings = c_double()
        ret = self.lib.BI_camera_measurement(p_id, num, readings)
        return ret, readings.value

    def camera_zero_calibration(self, p_id, start_wavelength, stop_wavelength):
        return self.lib.BI_camera_zero_calibration(p_id, start_wavelength, stop_wavelength)

    def delete_group(self, n):
        return self.lib.BI_delete_group(n)

    def display_advanced_window(self, p_id, hinstance):
        return self.lib.BI_display_advanced_window(p_id, hinstance)

    def display_setup_window(self, p_id, hinstance):
        return self.lib.BI_display_setup_window(p_id, hinstance)

    def get_log(self, log):
        return self.lib.BI_get_log(log)

    def get_log_size(self):
        return self.lib.BI_get_log_size()

    def get_max_bw(self, group, start_wavelength, stop_wavelength):
        bandwidth = c_double()
        ret = self.lib.BI_get_max_bw(group, start_wavelength, stop_wavelength, bandwidth)
        return ret, bandwidth.value

    def get_min_step(self, group, start_wavelength, stop_wavelength):
        min_step = c_double()
        ret = self.lib.BI_get_min_step(group, start_wavelength, stop_wavelength, min_step)
        return ret, min_step.value

    def get_n_groups(self):
        return self.lib.BI_get_n_groups()

    def get_str(self, hw_id, token, index, s):
        return self.lib.BI_get_str(hw_id, token, index, s)

    def mapped_logging(self, i):
        return self.lib.BI_Mapped_Logging(i)

    def multi_auto_measure(self):
        return self.lib.BI_multi_automeasure()

    def multi_park(self):
        return self.lib.BI_multi_park()

    def start_log(self, c_list):
        return self.lib.BI_start_log(c_list)

    def stop_log(self, c_list):
        return self.lib.BI_stop_log(c_list)


if __name__ == '__main__':
    from msl.equipment.resources.utils import CHeader, camelcase_to_underscore

    header = r'H:\Bentham\SDK\lang\c\bendll.h'

    header = CHeader(header)
    fcns = header.functions(r'typedef\s+(\w+)\s*\(WINAPI\*pf(\w+)\)')
    for key, value in fcns.items():
        print('        self.lib.{name}.restype = {res}'.format(name=key, res=value[0]))
        print('        self.lib.{name}.argtypes = [{args}]'.format(name=key, args=', '.join([item[0] for item in value[1] if item[0] is not None])))

    print()

    for key, value in fcns.items():
        args_p = [camelcase_to_underscore(item[1]) for item in value[1] if item[0] is not None and not item[0].startswith('POINTER')]
        args_c = [camelcase_to_underscore(item[1]) for item in value[1] if item[0] is not None]
        ptrs = [[camelcase_to_underscore(item[1]), item[0]] for item in value[1] if item[0] is not None and item[0].startswith('POINTER')]
        if args_p:
            print('    def {}(self, {}):'.format(camelcase_to_underscore(key[3:]), ', '.join(args_p)))
            for p in ptrs:
                print('        {} = {}()'.format(p[0], p[1][8:-1]))
            if not ptrs:
                print('        return self.lib.{}({})'.format(key, ', '.join(args_c)))
            else:
                print('        ret = self.lib.{}({})'.format(key, ', '.join(args_c)))
                print('        return ret, {}.value'.format('.value, '.join(p[0]for p in ptrs)))
        else:
            print('    def {}(self):'.format(camelcase_to_underscore(key[3:]), ', '.join(args_p)))
            print('        return self.lib.{}()'.format(key))
        print()
