"""
Error code definition file for Bentham Instruments Spectroradiometer Control DLL
"""

BI_OK = 0
BI_error = -1
BI_invalid_token = -2
BI_invalid_component = -3
BI_invalid_attribute = -4
BI_no_setup_window = -5

# BI_no_error = 0  ... just use BI_OK

BI_PMC_timeout = 1
BI_MSC_timeout = 2
BI_MSD_timeout = 3
BI_MAC_timeout = 4
BI_MAC_invalid_cmd = 5

BI_225_dead = 10
BI_265_dead = 11
BI_267_dead = 12
BI_277_dead = 13

BI_262_dead = 14

BI_ADC_read_error = 20
BI_ADC_invalid_reading = 21
BI_ADC_Overload = 22

BI_AMP_invalid_channel = 30
BI_AMP_invalid_wavelength = 31
BI_SAM_invalid_wavelength = 32
BI_turret_invalid_wavelength = 33
BI_turret_incorrect_pos = 34
BI_MVSS_invalid_width = 35

BI_undefined_error = 100

ERROR_CODES = {
    BI_OK: (
        'BI_OK',
        'Function call succeeded.'
    ),
    BI_error: (
        'BI_error',
        'Function call failed.'
    ),
    BI_invalid_token: (
        'BI_invalid_token',
        'The function was passed an invalid attribute token.'
    ),
    BI_invalid_component: (
        'BI_invalid_component',
        'The function was passed a component identifier that does not exist.'
    ),
    BI_invalid_attribute: (
        'BI_invalid_attribute',
        'The function was passed an attribute token referring to an attribute that does not exist or is inaccessible.'
    ),
    BI_no_setup_window: (
        'BI_no_setup_window',
        'No setup window.'
    ),
    BI_PMC_timeout: (
        'BI_PMC_timeout',
        'PMC not responding.'
    ),
    BI_MSC_timeout: (
        'BI_MSC_timeout',
        'MSC1 not responding.'
    ),
    BI_MSD_timeout: (
        'BI_MSD_timeout',
        'MSC1 not responding.'
    ),
    BI_MAC_timeout: (
        'BI_MAC_timeout',
        'MAC not responding.'
    ),
    BI_MAC_invalid_cmd: (
        'BI_MAC_invalid_cmd',
        'Error in communication with MAC.'
    ),
    BI_225_dead: (
        'BI_225_dead',
        '225 not responding.'
    ),
    BI_265_dead: (
        'BI_265_dead',
        '265 not responding.'
    ),
    BI_267_dead: (
        'BI_267_dead',
        '267 not responding.'
    ),
    BI_277_dead: (
        'BI_277_dead',
        '277 not responding.'
    ),
    BI_262_dead: (
        'BI_262_dead',
        '262 not responding.'
    ),
    BI_ADC_read_error: (
        'BI_ADC_read_error',
        'ADC not responding.'
    ),
    BI_ADC_invalid_reading: (
        'BI_ADC_invalid_reading',
        'Could not obtain valid ADC reading.'
    ),
    BI_ADC_Overload: (
        'BI_ADC_Overload',
        'ADC overload.'
    ),
    BI_AMP_invalid_channel: (
        'BI_AMP_invalid_channel',
        'Invalid amplifier channel.'
    ),
    BI_AMP_invalid_wavelength: (
        'BI_AMP_invalid_wavelength',
        'Invalid amplifier wavelength.'
    ),
    BI_SAM_invalid_wavelength: (
        'BI_SAM_invalid_wavelength',
        'Invalid SAM wavelength.'
    ),
    BI_turret_invalid_wavelength: (
        'BI_turret_invalid_wavelength',
        'Attempt to send monochromator beyond wavelength range.'
    ),
    BI_turret_incorrect_pos: (
        'BI_turret_incorrect_pos',
        'Error in communication with MAC.'
    ),
    BI_MVSS_invalid_width: (
        'BI_MVSS_invalid_width',
        'Invalid MVSS wavelength.'
    ),
    BI_undefined_error: (
        'BI_undefined_error',
        'Undefined error.'
    ),
}
