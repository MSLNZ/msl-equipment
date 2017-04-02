"""
The functions in this module are only helper functions that were initially used 
for wrapping the PicoScope SDK in Python. There are no user-facing functions 
here, only those used by a developer.

These functions are used to: 

Print the following to stdout 
- the #define constants
- the function signatures for the PicoScope subclasses

Create the following files:
- picoscope_enums.py
- picoscope_structs.py
- picoscope_callbacks.py
- picoscope_function_pointers.py
"""
import os
import re

CTYPES_MAP = {
    'void':        'c_void_p',
    'float':       'c_float',
    'double':      'c_double',
    'PICO_INFO':   'PICO_INFO',
    'PICO_STATUS': 'PICO_STATUS',
}


def parse_pico_scope_api_header(path):
    """
    Parse a PicoScope header file.

    Args:
        path (str): The path to a PicoScope header file  

    Returns:
        :py:class:`dict`: {'enums': {}, 'defines': {}, 'functions': {}, 'structs': {}, 'functypes': {}}
    """
    fname = os.path.basename(path)[:-2]
    header_dict = {'enums': {}, 'defines': {}, 'functions': {}, 'structs': {}, 'functypes': {}}
    with open(path, 'r') as fp:
        for line in fp:

            # the function definitions and the function-prototype definitions
            if line.startswith('PREF0') or line.startswith('typedef void') or line.startswith('typedef int16_t'):
                if line.startswith('PREF0'):
                    key = 'functions'
                    function_name = re.findall('\((.*?)\)', line)[0].strip()
                    restype = re.findall('PREF1(.*?)PREF2', line)[0].strip()
                else:
                    key = 'functypes'
                    function_name = line.split('*')[1][:-2]
                    restype = 'void' if line.startswith('typedef void') else 'int16_t'
                args = []
                for line2 in fp:
                    if '(' in line2:
                        continue
                    elif ');' in line2:
                        alias = function_name.replace(fname.replace('Api', ''), '')
                        if '_' in function_name:  # convert to camel case
                            alias = ''.join(x.capitalize() for x in alias.split('_')[1:])
                        header_dict[key][function_name] = alias, restype, args
                        #print('{0:<11} {1:<45} {2:<45} {3:<12} {4}'.format(fname, function_name, alias, restype, args))
                        break
                    split_line = line2.split()
                    dtype = split_line[0]
                    if '**' in line2:
                        dtype += '**'
                    elif '*' in line2:
                        dtype += '*'
                    if len(split_line) > 1:
                        args.extend([dtype, re.search('[a-zA-Z_]+', split_line[-1]).group(0)])
                    else:
                        if dtype == 'GetOverviewBuffersMaxMin':
                            args.extend([dtype, 'lpGetOverviewBuffersMaxMin'])
                        elif dtype == 'void':
                            # the following function do not take inputs
                            # ps2000_open_unit, ps2000_open_unit_async
                            # ps3000_open_unit, ps3000_open_unit_async
                            pass
                            #args.extend([dtype, None])
                        else:
                            raise NotImplementedError

            # the #define statements
            if line.startswith('#define'):
                line_split = line.split()
                if len(line_split) > 2:
                    header_dict['defines'][line_split[1]] = ''.join(line_split[2:]).split('//')[0]

            # the enum definitions
            if line.startswith('typedef enum'):
                enum_name = line.split('typedef enum')[1].strip()
                args = []
                for line2 in fp:
                    if '{' in line2:
                        continue
                    elif '}' in line2:
                        alias = line2.replace('}', '').replace(';', '').strip()
                        if '=' in alias:
                            # fix: PS5000A_NONE = PS5000A_RISING} PS5000A_THRESHOLD_DIRECTION;
                            s = alias.split()
                            alias = s[3]
                            args.append(s[0] + ' = ' + s[2])
                        header_dict['enums'][enum_name] = alias, args
                        break
                    text = line2.split('//')[0].replace(',', '').strip()
                    if text:
                        args.append(text)

            # the struct definitions
            if line.startswith('typedef struct'):
                struct_name = line.split('typedef struct')[1].strip()
                args = []
                for line2 in fp:
                    if '{' in line2:
                        continue
                    elif '}' in line2:
                        alias = line2.replace('}', '').replace(';', '').strip()
                        prefix = fname.replace('Api', '').upper()
                        if not alias.startswith(prefix):
                            alias = prefix + '_' + alias
                        header_dict['structs'][struct_name] = alias, args
                        break
                    dtype, text = line2.split()
                    args.append([dtype, text.replace(';', '')])

    return header_dict


def print_define_statements(header_dict):
    """
    Print the #define constants in the PicoScope header files to stdout
    
    The output is copied and pasted to the appropriate PicoScope subclass.
     
    For example, the stdout text below 
    
        ps5000aApi
    
    is copied to 
    
        class PicoScope5000A(PicoScope):    
    """
    for hkey in header_dict:
        print(hkey)
        for key, value in header_dict[hkey]['defines'].items():
            if value.endswith('L') or value.endswith('f'):
                value = value[:-1]
            print('\t{} = {}'.format(key, value))


def create_picoscope_enums_file(header_dict, picostatus_h_path):
    """Creates the _picoscope_enums.py file"""
    fp = open('_picoscope_enums.py', 'w')
    fp.write('from enum import IntEnum\n\n')

    aliases = []
    for hkey in header_dict:
        fp.write('\n# ' + '*'*25 + ' typedef enum for ' + hkey + ' ' + '*'*25 + '\n')
        HKEY = hkey.replace('Api', '').upper()
        for key in header_dict[hkey]['enums']:
            class_name = key[2:]
            if not class_name.startswith('PS'):
                class_name = HKEY + class_name
            fp.write('\n\nclass {}(IntEnum):\n'.format(class_name))

            alias = header_dict[hkey]['enums'][key][0]
            if alias not in aliases:
                aliases.append(alias)

            param_names = []
            n = -1  # find max string length for the parameter NAME
            for value in header_dict[hkey]['enums'][key][1]:
                val = value.replace(HKEY + '_', '')
                if val[0].isdigit():
                    val = 'x'+val
                n = max(n, len(val.split('=')[0].strip()))
                param_names.append(val)

            index = -1
            is_hex = False
            for item in param_names:
                if '=' in item:
                    a, b = item.split('=')
                    fp.write('    {} = {}\n'.format(a.strip().ljust(n), b.strip()))
                    is_hex = '0x' in b
                    if is_hex:
                        index = int(b, 16)
                    else:
                        try:
                            index = int(b)
                        except ValueError:
                            # a reference to another parameter NAME
                            pass
                else:
                    index += 1
                    text = item.strip().ljust(n)
                    text_index = str(hex(index)) if is_hex else str(index)
                    fp.write('    {} = {}\n'.format(text, text_index))

        # for some reason the "typedef enum enPicoStringValue" enum definition is found in PicoStatus.h
        # this enum is only used by the ps4000aGetString function
        if 'ps4000a' in hkey:
            fp.write('# This enum definition was found in PicoStatus.h\n')
            fp.write('# It is used by the ps4000aGetString function\n')
            ps4000a_enum = []
            with open(picostatus_h_path, 'r') as ps:
                allow_writing = False
                index = 0
                n = 0
                for line in ps:
                    if line.startswith('typedef enum enPicoStringValue'):
                        fp.write('\n\nclass PicoStringValue(IntEnum):\n')
                        allow_writing = True
                        continue
                    if '}' in line:
                        aliases.append('PICO_STRING_VALUE')
                        allow_writing = False
                        continue
                    if allow_writing and '{' not in line:
                        t = line.replace(',', '').strip()
                        if t:
                            n = max(n, len(t))
                            ps4000a_enum.append((t, index))
                            index += 1
            for g in ps4000a_enum:
                fp.write('    {} = {}\n'.format(g[0].ljust(n), g[1]))

        fp.write('\n')

    fp.write('\nENUM_DATA_TYPE_NAMES = [\n')
    for a in sorted(aliases):
        fp.write('    \'{}\',\n'.format(a))
    fp.write(']\n')

    fp.close()


def create_picoscope_structs_file(header_dict):
    """Creates the _picoscope_structs.py file"""
    from picoscope_enums import ENUM_DATA_TYPE_NAMES

    fp = open('_picoscope_structs.py', 'w')
    fp.write('from ctypes import Structure, c_int16, c_uint16, c_uint32, c_int64, c_uint64\n\n')
    fp.write('from msl.equipment.resources.pico_technology.pico_status import c_enum, PICO_STATUS\n\n')

    aliases = {}
    for hkey in header_dict:
        fp.write('\n# ' + '*'*24 + ' typedef struct for ' + hkey + ' ' + '*'*24 + '\n')
        HKEY = hkey.replace('Api', '').upper()
        for key in header_dict[hkey]['structs']:
            class_name = key[1:]
            if not class_name.startswith('PS'):
                class_name = HKEY + class_name
            fp.write('\n\nclass {}(Structure):\n'.format(class_name))
            fp.write('    _fields_ = [\n')

            alias = header_dict[hkey]['structs'][key][0]
            if alias in aliases:
                raise KeyError('The STRUCT_DATA_TYPE_ALIASES keys are not unique: ' + alias)
            aliases[alias] = '{}'.format(class_name)

            args = []
            for value in header_dict[hkey]['structs'][key][1]:
                arg_name = value[1]
                c_type = value[0]
                if c_type in ENUM_DATA_TYPE_NAMES:
                    c_type = 'c_enum'
                elif c_type.endswith('_t'):
                    c_type = 'c_' + c_type[:-2]
                elif 'PICO_STATUS' in c_type:
                    pass
                else:
                    raise ValueError('{} {} {}'.format(hkey, value, c_type))
                args.append((arg_name, c_type))

            n = -1  # find max string length for the argument NAME
            for a in args:
                n = max(n, len(a[0]))

            for a in args:
                fp.write("        ('{}'{}, {}),\n".format(a[0], ' '*(n-len(a[0])), a[1]))  #.ljust(n)
            fp.write('    ]\n')

        fp.write('\n')

    fp.write('\nSTRUCT_DATA_TYPE_ALIASES = {\n')
    for a in sorted(aliases):
        fp.write('    \'{}\': {},\n'.format(a, aliases[a]))
    fp.write('}\n')

    fp.close()


def check_enum_struct_names():
    """Ensure that none of the items in ENUM_DATA_TYPE_NAMES are in STRUCT_DATA_TYPE_ALIASES"""
    from picoscope_enums import ENUM_DATA_TYPE_NAMES
    from picoscope_structs import STRUCT_DATA_TYPE_ALIASES

    for item in ENUM_DATA_TYPE_NAMES:
        if item in STRUCT_DATA_TYPE_ALIASES:
            raise ValueError('{}'.format(item))
    print('The enum and struct names are unique')


def create_callbacks_file(header_dict):
    """Create the _picoscope_callbacks.py file"""

    fp = open('_picoscope_callbacks.py', 'w')
    fp.write('import sys\n')
    fp.write('from ctypes import WINFUNCTYPE, CFUNCTYPE, POINTER, c_int16, c_uint32, c_void_p, c_int32\n\n')
    fp.write('from msl.equipment.resources.pico_technology.pico_status import PICO_STATUS\n\n')
    fp.write("if sys.platform in ('win32', 'cygwin'):\n")
    fp.write('    FUNCTYPE = WINFUNCTYPE\n')
    fp.write('else:\n')
    fp.write('    FUNCTYPE = CFUNCTYPE\n\n')

    keys = []

    ignore_GetOverviewBuffersMaxMin = False
    for hkey in header_dict:
        for key in header_dict[hkey]['functypes']:
            if key not in keys:
                keys.append(key)
            assert header_dict[hkey]['functypes'][key][1] in ('void', 'int16_t')
            args = 'None'
            for idx, value in enumerate(header_dict[hkey]['functypes'][key][2]):
                if idx % 2 == 0:
                    args += ', '
                    if value.endswith('_t'):
                        args += 'c_' + value[:-2]
                    elif value == 'void*':
                        args += 'c_void_p'
                    elif value == 'int16_t*':
                        args += 'POINTER(c_int16)'
                    elif value == 'int16_t**':
                        args += 'POINTER(POINTER(c_int16))'
                    else:
                        args += value

            # the GetOverviewBuffersMaxMin callback occurs twice, in ps2000.h and ps3000.h
            if 'GetOverviewBuffersMaxMin' in key:
                if ignore_GetOverviewBuffersMaxMin:
                    continue
                ignore_GetOverviewBuffersMaxMin = True

            fp.write('{} = FUNCTYPE({})\n'.format(key, args))

    fp.write('\n\nCALLBACK_NAMES = [\n')
    for k in keys:
        fp.write("    '{}',\n".format(k))
    fp.write(']\n')

    fp.close()


def ctypes_map(dtype, hkey):
    from picoscope_enums import ENUM_DATA_TYPE_NAMES
    from picoscope_structs import STRUCT_DATA_TYPE_ALIASES
    from picoscope_callbacks import CALLBACK_NAMES

    if not dtype:
        return ''

    assert '**' not in dtype  # we have not dealt with a Pointer to Pointer

    is_pointer = '*' in dtype
    if is_pointer:
        dtype = dtype[:-1]

    c_type = None
    try:
        c_type = CTYPES_MAP[dtype]
    except KeyError:
        if dtype.endswith('_t'):
            c_type = 'c_' + dtype[:-2]
        elif dtype in ENUM_DATA_TYPE_NAMES:
            c_type = 'c_enum'
        elif dtype in STRUCT_DATA_TYPE_ALIASES:
            c_type = '{}'.format(STRUCT_DATA_TYPE_ALIASES[dtype].__name__)
        elif dtype in CALLBACK_NAMES:
            c_type = dtype

        # some structs in the header files do not start with PS####, try again
        if c_type is None:
            test = hkey.replace('Api', '').upper() + '_' + dtype
            if test in STRUCT_DATA_TYPE_ALIASES:
                c_type = '{}'.format(STRUCT_DATA_TYPE_ALIASES[test].__name__)

    if c_type is None:
        raise ValueError('Unhandled C argument data type "{}"'.format(dtype))

    if is_pointer:
        return 'POINTER({})'.format(c_type)
    else:
        return c_type


def create_picoscope_functions_file(header_dict):
    """
    Create the _picoscope_functions.py file. 
    The lists in this file are used for creating ctypes._FuncPtr objects
    """
    from picoscope_callbacks import CALLBACK_NAMES
    from picoscope_structs import STRUCT_DATA_TYPE_ALIASES

    fp = open('_picoscope_functions.py', 'w')

    fp.write('from ctypes import (c_int8, c_uint8, c_int16, c_uint16, c_int32, \n')
    fp.write('                    c_uint32, c_int64, c_uint64, c_float, c_double, c_void_p, POINTER)\n\n')
    fp.write('from .pico_status import c_enum, PICO_STATUS, PICO_INFO\n\n')

    # import all the callbacks
    callbacks_import = 'from .picoscope_callbacks import ({},\n'.format(CALLBACK_NAMES[0])
    for idx in range(1, len(CALLBACK_NAMES)):
        if CALLBACK_NAMES[idx].endswith('DataReady'):
            continue
        callbacks_import += '                                  {},\n'.format(CALLBACK_NAMES[idx])
    fp.write(callbacks_import[:-2] + ')\n\n')

    # import all the structs
    structs_import = 'from .picoscope_structs import ('
    for idx, struct in enumerate(STRUCT_DATA_TYPE_ALIASES):
        s = STRUCT_DATA_TYPE_ALIASES[struct].__name__
        if idx == 0:
            structs_import += '{},\n'.format(s)
        else:
            structs_import += '                                {},\n'.format(s)
    fp.write(structs_import[:-2] + ')\n\n\n')

    # write a description of what follows
    fp.write('# The structure for each item in a *_funcptrs list is:\n')
    fp.write('#\n')
    fp.write('# (SDK_function_name, an_alias_for_the_function_name, return_data_type, error_check_returned_value?,\n')
    fp.write('#    (ctype, SDK_type, SDK_argument_name),\n\n\n')

    for hkey in header_dict:
        fp.write('# ' + '*' * 24 + ' SDK functions for ' + hkey + ' ' + '*' * 24 + '\n\n\n')
        fp.write('{}_funcptrs = [\n'.format(hkey))
        fcns = []
        for key in header_dict[hkey]['functions']:
            alias = header_dict[hkey]['functions'][key][0]
            ret = header_dict[hkey]['functions'][key][1]
            argtypes = header_dict[hkey]['functions'][key][2]
            s = '' if len(argtypes) > 0 else '     []\n'
            for i in range(0, len(argtypes), 2):
                if i == 0:
                    s = "     [({}, '{}', '{}'),\n".format(ctypes_map(argtypes[i], hkey), argtypes[i], argtypes[i+1])
                    continue
                try:
                    s += "      ({}, '{}', '{}'),\n".format(ctypes_map(argtypes[i], hkey), argtypes[i], argtypes[i+1])
                except ValueError:
                    # some structs in the header files do not start with PS####, try again
                    t = hkey.replace('Api', '').upper() + '_' + argtypes[i]
                    s += "      ({}, '{}', '{}'),\n".format(ctypes_map(t, hkey), argtypes[i], argtypes[i+1])

            # for ps2000 and ps3000 the returned value can represent many different scenarios, do not do error checking
            errcheck = hkey not in ('ps2000', 'ps3000')
            fcns.append("('{}', '{}', {}, {},\n{}]\n     ),\n".format(key, alias, ctypes_map(ret, hkey),
                                                                      errcheck, s[:-2]))

        for val in sorted(fcns):
            fp.write('    ' + val)

        fp.write(']\n\n\n')

    fp.close()


def print_class_def_signatures(header_dict):
    def convert(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    for hkey in header_dict:
        print(hkey)
        lowercase_underscore_keys = {convert(key): key for key in header_dict[hkey]['functions']}
        for item in sorted(lowercase_underscore_keys):
            key = lowercase_underscore_keys[item]
            alias = header_dict[hkey]['functions'][key][0]
            text = '    def ' + convert(alias) + '(self, '
            args = header_dict[hkey]['functions'][key][2]
            internal = ''
            sdk_args = ''
            ret_text = ''
            for i in range(0, len(args), 2):
                if '*' in args[i]:
                    internal += '        {} = {}()\n'.format(convert(args[i+1]), ctypes_map(args[i][:-1], hkey))
                    sdk_args += 'byref({}), '.format(convert(args[i+1]))
                    ret_text += '{}.value, '.format(convert(args[i+1]))
                    continue
                else:
                    sdk_args += '{}, '.format(convert(args[i + 1]))
                if ('handle' in args[i+1]) or (len(args[i+1]) == 0):
                    continue
                text += convert(args[i+1]) + ', '
            print(text[:-2] + '):')  # prints the def signature
            if internal:
                print(internal[:-1])
            if hkey in ('ps2000', 'ps3000'):
                print('        ret = self.sdk.{}({})'.format(key, sdk_args[:-2].replace('handle', 'self._handle')))
                if ret_text:
                    print('        return ret, (' + ret_text[:-2] + ')')
                else:
                    print('        return ret')
            else:
                print('        self.sdk.{}({})'.format(key, sdk_args[:-2].replace('handle', 'self._handle')))
                if ret_text:
                    print('        return {}'.format(ret_text[:-2]))
            print()

    print('This helps you out, but you still need to verify each function')
    print('For example, if passing a pointer to a Structure then you need to return the Structure values')


def print_common_functions(header_dict, ps_name):

    match = []
    do_not_match = []
    for psvalue in header_dict[ps_name]['functions'].values():
        for hkey in header_dict:
            if hkey == ps_name:
                continue
            for key, value in header_dict[hkey]['functions'].items():
                if psvalue[0] == value[0]:  # alias match
                    if psvalue[2] == value[2]:  # arguments match
                        match.append((key, value))
                    else:
                        do_not_match.append((key, value))

    print('match')
    for m in match:
        print('\t', m)

    print('\ndo not match')
    for m in do_not_match:
        print('\t', m)


if __name__ == '__main__':
    root = 'C:/Program Files/Pico Technology/SDK/inc/'
    filenames = ('ps2000'   , 'ps2000aApi',
                 'ps3000'   , 'ps3000aApi',
                 'ps4000Api', 'ps4000aApi',
                 'ps5000Api', 'ps5000aApi',
                 'ps6000Api')

    header_dict = {}
    for name in filenames:
        header_dict[name] = parse_pico_scope_api_header(os.path.join(root, name + '.h'))

    if 0:  # print header_dict
        for hkey in header_dict:
            print(hkey)
            for key in header_dict[hkey]:
                print('{} {}'.format(key, header_dict[hkey][key]))
            print()

    #print_define_statements(header_dict)

    #create_picoscope_enums_file(header_dict, os.path.join(root, 'PicoStatus.h'))

    #create_picoscope_structs_file(header_dict)

    #check_enum_struct_names()

    #create_callbacks_file(header_dict)

    #create_picoscope_functions_file(header_dict)

    #print_class_def_signatures(header_dict)

    #print_common_functions(header_dict, 'ps2000aApi')
