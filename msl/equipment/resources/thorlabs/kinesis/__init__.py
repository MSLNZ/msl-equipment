"""
Wrapper package around the Thorlabs.MotionControl.C_API.
 
The Kinesis software can be downloaded from the `Thorlabs website`_

.. _Thorlabs website:
    https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
"""


def _print(cls, fcns, header_filename):
    # useful when creating/updating a new wrapper class

    from msl.equipment.resources.utils import CHeader
    from msl.equipment.resources.utils import camelcase_to_underscore as convert

    def get_comment(lines, name):
        # used when creating a new wrapper class
        comments = []
        found_it = False
        for line in lines:
            if name in line and '__cdecl' in line:
                found_it = True
                continue
            if found_it:
                if line.startswith('///'):
                    comments.append(line[3:].strip())
                else:
                    break
        return '        """{}\n        """'.format('        \n        '.join(comments[::-1]))

    already_defined = (vars(cls))

    header = CHeader('C:/Program Files/Thorlabs/Kinesis/' + header_filename, remove_comments=False)
    lines = header.get_lines()[::-1]

    for item in sorted(fcns):
        method_name = item[0].replace('MMIparams', 'MmiParams')
        method_name = method_name.replace('LEDswitches', 'LedSwitches')
        method_name = convert(method_name.split('_')[1])
        args_p = ''
        args_c = ''
        for i, arg in enumerate(item[3]):
            if i == 0 and 'c_char_p' in str(arg[0]):
                args_c += 'self._serial, '
            elif 'PyCPointerType' in str(type(arg[0])):
                args_c += 'byref({}), '.format(convert(arg[1]))
            else:
                a = convert(arg[1])
                args_p += '{}, '.format(a)
                args_c += '{}, '.format(a)

        if method_name in already_defined:
            continue

        args_p = args_p[:-2]
        if args_p:
            print('    def {}(self, {}):'.format(method_name, args_p))
        else:
            print('    def {}(self):'.format(method_name))
        print(get_comment(lines, item[0]))
        print('        return self.sdk.{}({})\n'.format(item[0], args_c[:-2]))
