"""
Utility functions/classes to help create modules in the **resources** package.
"""
import re
import ctypes

BYTE = ctypes.c_byte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong

CTYPES_MAP = {
    'void': None,
    'void*': 'c_void_p',
    'BYTE': 'BYTE',
    'WORD': 'WORD',
    'DWORD': 'DWORD',
    'byte': 'c_byte',
    '_Bool': 'c_bool',
    'bool': 'c_bool',
    'char': 'c_char',
    'char*': 'c_char_p',
    'char const*': 'c_char_p',
    'const char*': 'c_char_p',
    'wchar_t': 'c_wchar',
    'wchar_t*': 'c_wchar_p',
    'short': 'c_short',
    'int': 'c_int',
    'long': 'c_long',
    'long long': 'c_longlong',
    'unsigned long long': 'c_ulonglong',
    'float': 'c_float',
    'double': 'c_double',
    'long double': 'c_longdouble',
    'size_t': 'c_size_t',
    'ssize_t': 'c_ssize_t',
    '__int8': 'c_int8',
    '__int16': 'c_int16',
    '__int': 'c_int',
    '__int32': 'c_int32',
    '__int64': 'c_int64',
    'unsigned char': 'c_ubyte',
    'unsigned short': 'c_ushort',
    'unsigned int': 'c_uint',
    'unsigned __int8': 'c_uint8',
    'unsigned __int16': 'c_uint16',
    'unsigned __int': 'c_uint',
    'unsigned __int32': 'c_uint32',
    'unsigned __int64': 'c_uint64',
    'int8_t': 'c_int8',
    'uint8_t': 'c_uint8',
    'int16_t': 'c_int16',
    'uint16_t': 'c_uint16',
    'int32_t': 'c_int32',
    'uint32_t': 'c_uint32',
    'int64_t': 'c_int64',
    'uint64_t': 'c_uint64',
}


def camelcase_to_underscore(text):
    """Converts **CamelCaseText** to **camel_case_text**.
    
    Parameters
    ----------
    text : :obj:`str`
        The camel-case text to be converted.

    Returns
    -------
    :obj:`str`
        The `text` converted to lowercase and separated by underscores.        
    """
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_lines(header_path, remove_comments=True):
    """Returns the lines in a C/C++ header file that are not empty.
     
    Also strips the whitespace from each line and can optionally remove 
    the all comments from the header file.

    Parameters
    ----------
    header_path : :obj:`str`
        The path to a C/C++ header file.
    remove_comments : :obj:`bool`
        Whether to remove the comments from each line.

    Returns
    -------
    :obj:`list` of :obj:`str`
        The list of lines in the header file.
    """
    lines = []
    with open(header_path, 'r') as fp:
        for line in fp.readlines():
            line_strip = line.strip()
            if len(line_strip) == 0:
                continue
            if remove_comments:
                if line_strip.startswith('/') or line_strip.startswith('*'):
                    continue
                line_strip = line_strip.split('/')[0].strip()
            lines.append(line_strip)
    return lines


class CHeader(object):

    _defines_regex = re.compile(r'^#define\s+(\w+)\s+([^/]+)')
    _enum_regex = re.compile(r'^(typedef\s+)?enum\s+(\w+)(\s*:\s*\w+\s*\w+)?')
    _enum_alias_regex = re.compile(r'}\s*(\w+)\s*;')
    _struct_regex = re.compile(r'^(typedef\s+)?struct\s+(\w+)')
    _callback_regex = re.compile(r'typedef\s+void\s*\(\s*(\w+)?\s*\*(\w+)\s*\)')

    def __init__(self, header_path, remove_comments=True):
        """Parses a C/C++ header file to determine the constants, enums, structs, callbacks
        and the function signatures.
        
        Parameters
        ----------
        header_path : :obj:`str`
            The path to the header file. 
        remove_comments : :obj:`bool`
            Whether to remove the comments from the header file. 
        """
        self._struct_imports = []  # the structs that must be imported for the C functions

        self._lines = get_lines(header_path, remove_comments)
        self._get_enums()
        self._get_structs()
        self._get_callbacks()

    def constants(self, ignore_ifdef=True):
        """Finds the **#define** statements that in a C/C++ header file.

        Parameters
        ----------
        ignore_ifdef : :obj:`bool`, optional
            Whether to ignore the ``#define`` statements in between the ``#ifdef`` 
            and ``#endif`` statements.
        
        Returns
        -------
        :obj:`dict` of :obj:`str`
            A dictionary of all the ``#define`` constants (as strings).
        """
        _constants = {}
        count = 0
        for line in self._lines:
            if ignore_ifdef and line.startswith('#ifdef'):
                count += 1
            elif ignore_ifdef and line.startswith('#endif'):
                count -= 1
            if count > 0:
                continue
            m = self._defines_regex.search(line)
            if m is not None:
                name = m.group(1).strip()
                value = m.group(2).strip()
                if value.endswith('f'):
                    value = value[:-1]
                elif value.endswith('L'):
                    value = value[:-1]
                _constants[name] = value
        return _constants

    def enums(self):
        """
        Returns
        -------
        :obj:`dict`
            The ``enums`` that are defined in the C/C++ header file. 
            The value for each dictionary key is a tuple of 
            *(the naming convention, the enum data type that is defined, 
            a dict of name-value pairs)*.
        """
        return self._enums

    def structs(self):
        """
        Returns
        -------
        :obj:`dict`
            The ``structs`` that are defined in the C/C++ header file.
        """
        return self._structs

    def callbacks(self):
        """
        Returns
        -------
        :obj:`dict`
            The ``callbacks`` that are defined in the C/C++ header file.
        """
        return self._callbacks

    def functions(self, regex):
        """Returns the function signatures.

        Parameters
        ----------
        regex : :obj:`str`
            The regex must create 2 groups, *(return type, function name)*, and it must
            match the function declaration up until, but excluding, the '(' which begins the
            argument declarations.
            
            For example,
            
            If the function declarations are similar to            
            ``FILTERFLIPPERDLL_API unsigned int __cdecl FF_GetTransitTime(const char * serialNo);``            
            then the value of `regex` could be 
            ``r'_API\s+([\w\s]+?)__cdecl\s+(\w+)'``
                
            If the function declarations are similar to
            ``PREF0 PREF1 PICO_STATUS PREF2 PREF3 (ps6000OpenUnit)(int16_t *handle, int8_t *serial);``
            then the value of `regex` could be
            ``r'PREF0\s+PREF1\s+(\w+)\s+PREF2\s+PREF3\s+\((\w+)\)'``

        Returns
        -------
        :obj:`dict`
            The function signature. The key is the function name and the value is a list of 
            [return type, [(argument data type, argument name), ... ] ].        
        """
        _fcn_regex = re.compile(regex)
        lines = list(self._lines)  # create a copy, since it will bne modified
        self._struct_imports = []
        fcns = {}
        i, n = 0, len(lines)
        while i < n:
            m = _fcn_regex.search(lines[i])
            if m is None:
                i += 1
                continue

            # in case the function name is contained within brackets, e.g. (ps6000OpenUnit)
            lines[i] = _fcn_regex.split(lines[i])[-1]

            text, i = CHeader.get_text_between_brackets(lines, i, '(', ')')
            fcns[m.group(2)] = [self._convert_ctype(m.group(1)), self._split_datatype_name(text, ',')]

            i += 1
        return fcns

    def get_lines(self):
        """
        Returns
        -------
        :obj:`list` of :obj:`str`
            The lines in the C/C++ header file.
        """
        return self._lines

    def get_struct_imports(self):
        """
        Returns
        -------
        :obj:`list` of :obj:`str`
            The list of ``structs`` that must be imported for the C/C++ functions. 
        
        Note
        ----
        Must call :meth:`.functions` first.
        """
        return self._struct_imports

    @staticmethod
    def get_text_between_brackets(lines, index, bracket1, bracket2):
        """Get all the text (excluding comments) between two brackets.

        Parameters
        ----------
        lines : :obj:`list` of :obj:`str`
            A list of lines. Comes from :meth:`.get_lines`.
        index : :obj:`int`
            The current index in `lines`.
        bracket1 : :obj:`str`
            One of ``{``, ``(``, or ``[`` 
        bracket2 : :obj:`str`
            One of ``}``, ``)`` or ``]``

        Returns
        -------
        :obj:`str`
            The text between `bracket1` and `bracket2`.
        :obj:`int`
            The current index in `lines`. 
        """
        assert bracket1 in ('(', '{', '['), 'Invalid bracket1 "{}"'.format(bracket1)
        assert bracket2 in (')', '}', ']'), 'Invalid bracket2 "{}"'.format(bracket2)

        def _remove_comment(_line):
            # remove any comments that are on this line
            return _line.split('/')[0].strip()

        while bracket1 not in lines[index]:
            index += 1

        text = _remove_comment(lines[index].split(bracket1)[1])

        while True:
            if bracket2 in lines[index]:
                text = text.split(bracket2)[0].strip()
                break
            else:
                index += 1
                text += _remove_comment(lines[index])

        return text, index

    def _get_enums(self):
        """Find the ``enums``"""
        self._enums = {}
        i, n = 0, len(self._lines)
        while i < n:
            m = self._enum_regex.search(self._lines[i])
            if m is None:
                i += 1
                continue

            _, enum_name, data_type = m.groups()
            if data_type is not None:
                data_type = data_type.replace(':', '').strip()
                data_type = CTYPES_MAP[data_type]
            else:
                data_type = None

            # get all the text between { }
            text, i = CHeader.get_text_between_brackets(self._lines, i, '{', '}')
            if text.endswith(','):
                text = text[:-1]

            # determine if there is a naming convention
            m = self._enum_alias_regex.search(self._lines[i])
            alias = enum_name if m is None else m.group(1)

            # we now have a string with a "," separating the values
            members = {}
            is_hex = False
            auto_increment = 0
            for item in text.split(','):
                item_split = item.split('=')
                name = item_split[0].strip()
                if len(item_split) == 1:  # then no value
                    if is_hex:
                        value = str(hex(auto_increment))
                    else:
                        value = str(auto_increment)
                    auto_increment += 1
                else:
                    value = item_split[1].strip()
                    if value.lower().startswith('0x'):
                        is_hex = True
                        auto_increment = int(value, 16) + 1
                    else:
                        try:
                            auto_increment = int(value) + 1
                        except ValueError:
                            pass  # the value equals the name of a pre-defined value(s)
                members[name] = value

            self._enums[enum_name] = (alias, data_type, members)
            i += 1

    def _get_structs(self):
        """Find the ``structs``"""
        self._structs = {}
        i, n = 0, len(self._lines)
        while i < n:
            m = self._struct_regex.search(self._lines[i])
            if m is None:
                i += 1
                continue
            text, i = CHeader.get_text_between_brackets(self._lines, i, '{', '}')
            self._structs[m.group(2)] = self._split_datatype_name(text, ';')
            i += 1

    def _get_callbacks(self):
        """Find the ``callbacks``"""
        lines = list(self._lines)  # create a copy, since it will be modified
        self._callbacks = {}
        i, n = 0, len(lines)
        while i < n:
            m = self._callback_regex.search(lines[i])
            if m is None:
                i += 1
                continue
            lines[i] = self._callback_regex.split(lines[i])[-1]
            text, i = CHeader.get_text_between_brackets(lines, i, '(', ')')
            self._callbacks[m.group(2)] = self._split_datatype_name(text, ',')
            i += 1

    def _split_datatype_name(self, text, delimiter):
        """Splits a list of arguments into a (argument data type, argument name)
        
        Parameters
        ----------
        text : :obj:`str`
            The text from :meth:`.get_text_between_brackets`.
        delimiter : :obj:`str`
            The delimiter to use to split the data type and argument name.
    
        Returns
        -------
        :obj:`list` of :obj:`tup`
            A list of tuples [(argument data type, argument name), ... ].   
        """
        if text.endswith(delimiter):
            text = text[:-1]
        args = text.split(delimiter)

        _special = ('**', '*', '&')
        fields = []
        for item in args:
            item_split = item.split()

            if not item_split:
                fields.append(())
                continue

            if len(item_split) == 1:
                field_type = item_split[0]
                field_name = 'UNKNOWN'
            else:
                field_type = ' '.join(item_split[:-1])
                field_name = item_split[-1]

            for c in _special:
                if c in field_name:
                    field_type += c
                    field_name = field_name.replace(c, '')
                    break

            field_type = field_type.replace(' *', '*')
            field_type = self._convert_ctype(field_type)

            if ('[' in field_name) and (']' in field_name):
                field_name, end = field_name.split('[')
                field_type += ' * ' + end.split(']')[0]

            fields.append((field_type, field_name))

        return fields

    def _convert_ctype(self, c_type):
        """Convert a C data type to the appropriate ctype.

        Parameters
        ----------
        c_type : :obj:`str`
            The C/C++ data type. 

        Returns
        -------
        :obj:`str`
            The appropriate Python representation of the data type.
        """
        def _get_enum_dtype(tup):
            return 'c_int' if tup[1] is None else tup[1]

        dtype = c_type.strip()

        ptr = None
        if dtype.endswith('**'):
            ptr = 'POINTER(POINTER({}))'
            dtype = dtype[:-2].strip()
        elif dtype.endswith('*') and ('void' not in dtype) and ('char' not in dtype):
            ptr = 'POINTER({})'
            dtype = dtype[:-1].strip()
        elif dtype.endswith('&'):
            ptr = 'POINTER({})'
            dtype = dtype[:-1].strip()

        if dtype in self._structs:
            self._struct_imports.append(dtype)

        if dtype in CTYPES_MAP:
            dtype = CTYPES_MAP[dtype]
        else:
            if dtype in self._enums:
                dtype = _get_enum_dtype(self._enums[dtype])
            else:
                for item in self._enums.values():
                    if dtype in item[0]:
                        dtype = _get_enum_dtype(item)
                        break

        if ptr is not None:
            return ptr.format(dtype)
        else:
            return dtype
