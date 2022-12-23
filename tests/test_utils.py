import datetime
import enum
import struct
import sys
from xml.etree.cElementTree import Comment
from xml.etree.cElementTree import Element

import numpy as np
import pytest

from msl.equipment.utils import _parse_lxi_html
from msl.equipment.utils import _parse_lxi_xml
from msl.equipment.utils import convert_to_date
from msl.equipment.utils import convert_to_enum
from msl.equipment.utils import convert_to_primitive
from msl.equipment.utils import convert_to_xml_string
from msl.equipment.utils import from_bytes
from msl.equipment.utils import ipv4_addresses
from msl.equipment.utils import to_bytes
from msl.equipment.utils import xml_comment
from msl.equipment.utils import xml_element


def test_convert_to_enum():

    class MyEnum(enum.Enum):
        ONE = 'value'
        XXX_TWO = 2
        three = 3.0
        F_O_U_R = 'f o U r'
        FiVe = -5+5j
        SIX = True
        BYTES = b'\x00\x01'

    assert convert_to_enum('unknown', MyEnum, strict=False) == 'unknown'
    assert convert_to_enum(99, MyEnum, strict=False) == 99
    assert convert_to_enum(8j, MyEnum, strict=False) == 8j
    assert convert_to_enum(7.2, MyEnum, strict=False) == 7.2

    assert convert_to_enum(MyEnum.ONE, MyEnum) == MyEnum.ONE
    assert convert_to_enum('value', MyEnum) == MyEnum.ONE
    assert convert_to_enum('ONE', MyEnum) == MyEnum.ONE
    assert convert_to_enum('ONE', MyEnum) == MyEnum.ONE
    assert convert_to_enum('ONE', MyEnum, prefix='O') == MyEnum.ONE
    assert convert_to_enum('ONE', MyEnum, prefix='ON') == MyEnum.ONE
    assert convert_to_enum('ONE', MyEnum, prefix='ONE') == MyEnum.ONE
    assert convert_to_enum('one', MyEnum, to_upper=True) == MyEnum.ONE
    with pytest.raises(ValueError):
        convert_to_enum('one', MyEnum)
    assert convert_to_enum('one', MyEnum, prefix='one', to_upper=True) == MyEnum.ONE

    assert convert_to_enum(MyEnum.XXX_TWO, MyEnum) == MyEnum.XXX_TWO
    assert convert_to_enum(2, MyEnum) == MyEnum.XXX_TWO
    assert convert_to_enum('XXX_TWO', MyEnum) == MyEnum.XXX_TWO
    assert convert_to_enum('XXX TWO', MyEnum) == MyEnum.XXX_TWO
    assert convert_to_enum('xXx_twO', MyEnum, to_upper=True) == MyEnum.XXX_TWO
    assert convert_to_enum('Xxx TwO', MyEnum, to_upper=True) == MyEnum.XXX_TWO
    assert convert_to_enum('two', MyEnum, prefix='xxx_', to_upper=True) == MyEnum.XXX_TWO
    with pytest.raises(ValueError):
        convert_to_enum('TWO', MyEnum, prefix='xxx')
    assert convert_to_enum('TWO', MyEnum, prefix='xx', strict=False) == 'TWO'
    assert convert_to_enum('TWO', MyEnum, prefix='XXX_') == MyEnum.XXX_TWO

    assert convert_to_enum(MyEnum.three, MyEnum) == MyEnum.three
    assert convert_to_enum(3, MyEnum) == MyEnum.three
    assert convert_to_enum(3.0, MyEnum) == MyEnum.three
    assert convert_to_enum('three', MyEnum) == MyEnum.three
    with pytest.raises(ValueError):
        convert_to_enum('three', MyEnum, to_upper=True)
    with pytest.raises(ValueError):
        convert_to_enum('THREE', MyEnum)

    assert convert_to_enum(MyEnum.F_O_U_R, MyEnum) == MyEnum.F_O_U_R
    assert convert_to_enum('F O U R', MyEnum) == MyEnum.F_O_U_R
    assert convert_to_enum('f o U r', MyEnum) == MyEnum.F_O_U_R
    assert convert_to_enum('f o u r', MyEnum, to_upper=True) == MyEnum.F_O_U_R
    with pytest.raises(ValueError):
        convert_to_enum('f o u r', MyEnum)
    assert convert_to_enum('F_O_U_R', MyEnum) == MyEnum.F_O_U_R

    assert convert_to_enum(MyEnum.FiVe, MyEnum) == MyEnum.FiVe
    assert convert_to_enum(-5+5j, MyEnum) == MyEnum.FiVe
    assert convert_to_enum('FiVe', MyEnum) == MyEnum.FiVe
    with pytest.raises(ValueError):
        assert convert_to_enum('FiVe', MyEnum, to_upper=True)
    with pytest.raises(ValueError):
        assert convert_to_enum('FiVe', MyEnum, prefix='FI')

    assert convert_to_enum(True, MyEnum) == MyEnum.SIX
    assert convert_to_enum(1, MyEnum) == MyEnum.SIX
    assert convert_to_enum('SIX', MyEnum) == MyEnum.SIX
    assert convert_to_enum('six', MyEnum, to_upper=True) == MyEnum.SIX
    assert convert_to_enum('six', MyEnum, prefix='six', to_upper=True) == MyEnum.SIX
    with pytest.raises(ValueError):
        convert_to_enum('six', MyEnum, prefix='Six', to_upper=True)
    convert_to_enum('Six', MyEnum, prefix='Si', to_upper=True)

    assert convert_to_enum(b'\x00\x01', MyEnum) == MyEnum.BYTES
    assert convert_to_enum('bytes', MyEnum, to_upper=True) == MyEnum.BYTES
    with pytest.raises(ValueError):
        convert_to_enum('bytes', MyEnum)


def test_string_to_bool_int_float_complex():
    assert convert_to_primitive('none') is None
    assert convert_to_primitive('None') is None
    assert convert_to_primitive('nOnE') is None
    assert convert_to_primitive('  None \t') is None
    assert convert_to_primitive(None) is None

    assert convert_to_primitive('true') is True
    assert convert_to_primitive('True') is True
    assert convert_to_primitive('TRuE') is True
    assert convert_to_primitive('  True\n') is True
    assert convert_to_primitive(True) is True
    assert convert_to_primitive('false') is False
    assert convert_to_primitive('False') is False
    assert convert_to_primitive('FaLSe') is False
    assert convert_to_primitive('\nFalse\n') is False
    assert convert_to_primitive(False) is False

    assert convert_to_primitive('0') == 0
    assert convert_to_primitive(' 0 ') == 0
    assert convert_to_primitive(0) == 0
    assert isinstance(convert_to_primitive('0'), int)
    assert convert_to_primitive('1') == 1
    assert convert_to_primitive('       1\n') == 1
    assert isinstance(convert_to_primitive('1'), int)
    assert convert_to_primitive('-999') == -999
    assert isinstance(convert_to_primitive('-999'), int)

    assert convert_to_primitive('1.9') == 1.9
    assert convert_to_primitive(1.9) == 1.9
    assert isinstance(convert_to_primitive('1.9'), float)
    assert convert_to_primitive('-49.4') == -49.4
    assert convert_to_primitive('\t-49.4\n') == -49.4
    assert isinstance(convert_to_primitive('-49.4'), float)
    assert convert_to_primitive('2.553e83') == 2.553e83
    assert isinstance(convert_to_primitive('2.553e83'), float)

    assert convert_to_primitive('1.9j') == 1.9j
    assert convert_to_primitive(' 1.9j\t  ') == 1.9j
    assert isinstance(convert_to_primitive('1.9j'), complex)
    assert convert_to_primitive('-3+2.4j') == -3 + 2.4j
    assert isinstance(convert_to_primitive('-3+2.4j'), complex)
    assert convert_to_primitive('1+0j') == 1 + 0j
    assert isinstance(convert_to_primitive('1+0j'), complex)
    assert convert_to_primitive('1.52+2.32e-3j') == complex(1.52, 2.32e-3)
    assert isinstance(convert_to_primitive('1.52e8+2.32e-5j'), complex)
    assert convert_to_primitive(-3.2+2.4j) == complex(-3.2, 2.4)

    assert convert_to_primitive('') == ''
    assert convert_to_primitive(' \t \n ') == ' \t \n '
    assert convert_to_primitive('hello') == 'hello'
    assert convert_to_primitive('hello\tworld\r\n') == 'hello\tworld\r\n'
    assert convert_to_primitive(b'\x00\x00') == b'\x00\x00'
    assert convert_to_primitive('16i') == '16i'
    assert convert_to_primitive('[1,2,3]') == '[1,2,3]'

    assert convert_to_primitive([1, 2, 3]) == [1, 2, 3]
    assert convert_to_primitive({'1': 1}) == {'1': 1}
    assert convert_to_primitive(bytearray([1, 2, 3])) == b'\x01\x02\x03'


def test_convert_to_date():

    # test datetime.date object
    d = datetime.date(2000, 8, 24)
    out = convert_to_date(d)
    assert isinstance(out, datetime.date)
    assert out is d
    assert out.year == 2000
    assert out.month == 8
    assert out.day == 24

    # test datetime.datetime object
    # (this is an important timestamp in the movie Back to the Future)
    d = datetime.datetime(1985, 10, 26, hour=1, minute=21, second=0)
    out = convert_to_date(d)
    assert isinstance(out, datetime.date)
    assert out.year == 1985
    assert out.month == 10
    assert out.day == 26

    # test string object
    out = convert_to_date('2010-3-12')
    assert isinstance(out, datetime.date)
    assert out.year == 2010
    assert out.month == 3
    assert out.day == 12

    # test string with format
    out = convert_to_date('22.6.2100', fmt='%d.%m.%Y')
    assert isinstance(out, datetime.date)
    assert out.year == 2100
    assert out.month == 6
    assert out.day == 22

    # test invalid string with strict=False
    for item in ['2010-13-12', 'xxx', '22.6.2100']:
        out = convert_to_date(item, strict=False)
        assert isinstance(out, datetime.date)
        assert out.year == datetime.MINYEAR
        assert out.month == 1
        assert out.day == 1

        with pytest.raises(ValueError):
            convert_to_date(item, strict=True)

    # test None object
    out = convert_to_date(None)
    assert isinstance(out, datetime.date)
    assert out.year == datetime.MINYEAR
    assert out.month == 1
    assert out.day == 1


def test_convert_to_xml_string():

    root = Element('msl')

    team = Element('team')
    team.text = 'Light'
    root.append(team)

    data = Element('data')
    for a, b in [('one', '1'), ('two', '2'), ('three', '3')]:
        element = Element(a)
        element.text = b
        data.append(element)
    root.append(data)

    lines = convert_to_xml_string(root).splitlines()
    assert lines[0] == '<?xml version="1.0" encoding="utf-8"?>'
    assert lines[1] == '<msl>'
    assert lines[2] == '  <team>Light</team>'
    assert lines[3] == '  <data>'
    assert lines[4] == '    <one>1</one>'
    assert lines[5] == '    <two>2</two>'
    assert lines[6] == '    <three>3</three>'
    assert lines[7] == '  </data>'
    assert lines[8] == '</msl>'


def test_xml_element():

    element = xml_element('tag')
    assert element.tag == 'tag'
    assert element.text is None
    assert element.tail is None
    assert len(element.attrib) == 0

    element = xml_element('tag', text='the text')
    assert element.tag == 'tag'
    assert element.text == 'the text'
    assert element.tail is None
    assert len(element.attrib) == 0

    element = xml_element('tag', tail='the tail')
    assert element.tag == 'tag'
    assert element.text is None
    assert element.tail == 'the tail'
    assert len(element.attrib) == 0

    element = xml_element('tag', text='the text', tail='the tail', one='1', two='2', three='3')
    assert element.tag == 'tag'
    assert element.text == 'the text'
    assert element.tail == 'the tail'
    assert len(element.attrib) == 3
    assert element.attrib['one'] == '1'
    assert element.attrib['two'] == '2'
    assert element.attrib['three'] == '3'


def test_xml_comment():
    element = xml_comment('this is a comment')
    assert element.tag == Comment
    assert element.text == 'this is a comment'


def test_convert_to_xml_string_v2():
    root = xml_element('root')
    housekeeping = xml_element('Housekeeping')

    job = xml_element('job', text='ABC123')

    client = xml_element('client', city='Wellington')
    client.text = 'NZ Mass Inc.'

    masses = xml_element('masses')
    for index, mass in enumerate(['1ug', '1mg', '1g', '1kg']):
        masses.append(xml_element('mass_{}'.format(index), text=mass))

    housekeeping.append(masses)
    housekeeping.append(job)
    housekeeping.append(xml_comment('the Client info'))
    housekeeping.append(client)
    housekeeping.append(xml_element('bug', tail='Bugger'))

    root.append(xml_comment('Here is some information from the Housekeeping GUI'))
    root.append(housekeeping)

    lines = convert_to_xml_string(root).splitlines()
    assert lines[0] == '<?xml version="1.0" encoding="utf-8"?>'
    assert lines[1] == '<root>'
    assert lines[2] == '  <!--Here is some information from the Housekeeping GUI-->'
    assert lines[3] == '  <Housekeeping>'
    assert lines[4] == '    <masses>'
    assert lines[5] == '      <mass_0>1ug</mass_0>'
    assert lines[6] == '      <mass_1>1mg</mass_1>'
    assert lines[7] == '      <mass_2>1g</mass_2>'
    assert lines[8] == '      <mass_3>1kg</mass_3>'
    assert lines[9] == '    </masses>'
    assert lines[10] == '    <job>ABC123</job>'
    assert lines[11] == '    <!--the Client info-->'
    assert lines[12] == '    <client city="Wellington">NZ Mass Inc.</client>'
    assert lines[13] == '    <bug/>'
    assert lines[14] == '    Bugger'
    assert lines[15] == '  </Housekeeping>'
    assert lines[16] == '</root>'


def test_to_bytes_ieee():
    assert to_bytes([]) == b'#10'
    assert to_bytes(()) == b'#10'
    assert to_bytes(np.ndarray((0,))) == b'#10'

    assert to_bytes([9.8]) == b'#14\xcd\xcc\x1cA'

    expected = b'#240\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@' \
               b'\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00' \
               b'\x00\x00A\x00\x00\x10A'
    assert to_bytes(range(10)) == expected
    assert to_bytes(list(range(10))) == expected

    expected = b'#240\x00\x00\x00\x00?\x80\x00\x00@\x00\x00\x00@@\x00\x00@' \
               b'\x80\x00\x00@\xa0\x00\x00@\xc0\x00\x00@\xe0\x00\x00A\x00' \
               b'\x00\x00A\x10\x00\x00'
    assert to_bytes(range(10), dtype='>f') == expected
    assert to_bytes(list(range(10)), dtype='>f') == expected
    assert to_bytes(np.array(range(10)), dtype='>f') == expected

    expected = b'#220\x00\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06' \
               b'\x00\x07\x00\x08\x00\t\x00'
    assert to_bytes(range(10), dtype=np.uint16) == expected
    assert to_bytes(list(range(10)), dtype='ushort') == expected
    assert to_bytes(np.array(range(10)), dtype='H') == expected

    expected = b'#15\x01\x00\x01\x01\x00'
    assert to_bytes([True, False, True, True, False], dtype=np.uint8) == expected
    assert to_bytes(np.array([True, False, True, True, False]), dtype='B') == expected

    expected = b'#280\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00' \
               b'\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00' \
               b'\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00' \
               b'\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00' \
               b'\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t'
    assert to_bytes(range(10), dtype='>Q') == expected
    assert to_bytes(list(range(10)), dtype='>Q') == expected
    assert to_bytes(np.array(range(10)), dtype='>Q') == expected

    assert to_bytes(range(123456), dtype='float64').startswith(b'#6987648')


def test_to_bytes_no_header():
    expected = b'\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@' \
               b'\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00' \
               b'\x00\x00A\x00\x00\x10A'
    assert to_bytes(range(10), fmt='') == expected
    assert to_bytes(list(range(10)), fmt=False) == expected  # False is considered None
    assert to_bytes(np.array(range(10)), fmt='') == expected
    assert to_bytes(np.array(range(10)), fmt=None) == expected

    assert to_bytes([], fmt=None) == b''
    assert to_bytes([0.1], fmt=None, dtype=np.float32) == b'\xcd\xcc\xcc='


def test_to_bytes_hp():
    expected = b'#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03' \
               b'\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00' \
               b'\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00'
    assert to_bytes(range(10), fmt='hp', dtype='<i') == expected

    expected = b'#A\x00(\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00' \
               b'\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06' \
               b'\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t'
    assert to_bytes(range(10), fmt='hp', dtype='>i') == expected

    assert to_bytes([], fmt='hp') == b'#A\x00\x00'
    assert to_bytes([-99], fmt='hp', dtype='d') == b'#A\x08\x00\x00\x00\x00\x00\x00\xc0X\xc0'
    assert to_bytes([-99], fmt='hp', dtype='b') == b'#A\x01\x00\x9d'


def test_to_bytes_exceptions():
    with pytest.raises(ValueError, match='Invalid format'):
        to_bytes([], fmt='raw')

    with pytest.raises(struct.error):
        to_bytes(range(0xffff), fmt='hp', dtype='H')

    with pytest.raises(ValueError):
        to_bytes(range(10), fmt='ascii', dtype='H')


def test_to_bytes_ascii():
    expected = b'0.000000,1.000000,2.000000,3.000000,4.000000,5.000000,6.000000,7.000000,8.000000,9.000000'
    assert to_bytes(range(10), fmt='ascii') == expected

    expected = b'0.000,1.000,2.000,3.000,4.000,5.000,6.000,7.000,8.000,9.000'
    assert to_bytes(range(10), fmt='ascii', dtype='.3f') == expected

    expected = b'0,1,2,3,4,5,6,7,8,9'
    assert to_bytes(range(10), fmt='ascii', dtype='d') == expected

    expected = b'+0.0E+00,+1.0E+00,+2.0E+00,+3.0E+00,+4.0E+00,+5.0E+00,+6.0E+00,+7.0E+00,+8.0E+00,+9.0E+00'
    assert to_bytes(range(10), fmt='ascii', dtype='+.1E') == expected

    expected = b'0000,0001,0002,0003,0004,0005,0006,0007,0008,0009'
    assert to_bytes(range(10), fmt='ascii', dtype='04d') == expected

    assert to_bytes([], fmt='ascii') == b''
    assert to_bytes([0], fmt='ascii') == b'0.000000'
    assert to_bytes([-1, 1], fmt='ascii', dtype='03d') == b'-01,001'


@pytest.mark.skipif(
    sys.version_info.major == 2,
    reason='Python 2 cannot use np.fromiter with bytes')
def test_to_bytes_as_bytes():
    assert to_bytes(b'abcxyz', dtype='b') == b'#16abcxyz'
    assert to_bytes(b'abcdwxyz', dtype='B') == b'#18abcdwxyz'
    assert to_bytes(bytearray(b'abcxyz'), fmt=None, dtype='b') == b'abcxyz'
    assert to_bytes(b'acegikmoqsuwy', fmt='', dtype='int8') == b'acegikmoqsuwy'


def test_from_bytes_no_header():
    dtype = '<f'
    array = np.arange(123, dtype=dtype)
    assert np.array_equal(from_bytes(array.tobytes(), fmt=None), array)

    dtype = 'ushort'
    array = np.arange(64, dtype=dtype)
    assert np.array_equal(from_bytes(array.tobytes(), fmt=None, dtype=dtype), array)

    array = from_bytes(b'', fmt=None)
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b'@\xe2\x01\x00\x00\x00\x00\x00', fmt=None, dtype='<Q')
    assert np.array_equal(array, [123456])


def test_from_bytes_ieee():
    array = from_bytes(b'#10')
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b'#0')
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b'#0\n')
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    assert np.array_equal(from_bytes(b'#14E\x17\xf0\x00', dtype='>f'), [2431.0])
    assert np.array_equal(from_bytes(b'#0E\x17\xf0\x00', dtype='>f'), [2431.0])

    buffer = b'#240\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@' \
             b'\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00' \
             b'\x00\x00A\x00\x00\x10A'
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b'c35de90ae*9a2-4932=bf1b!2312f1+46-af7f' + buffer
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b',#280\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
             b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00' \
             b'\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00' \
             b'\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00' \
             b'\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00' \
             b'\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t'
    assert np.array_equal(from_bytes(buffer, dtype='>Q'), list(range(10)))

    buffer = b'#0\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@' \
             b'\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00' \
             b'\x00\x00A\x00\x00\x10A\n'  # ends in LF, this is what the IEEE standard requires
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b'c35de90ae*9a2-4932=bf1b!2312f1+46-af7f8qwy3v87yq2' + buffer
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b', #0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
             b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00' \
             b'\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00' \
             b'\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00' \
             b'\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00' \
             b'\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t'  # does not end in LF, should still work
    assert np.array_equal(from_bytes(buffer, dtype='>Q'), list(range(10)))


def test_from_bytes_exceptions():
    with pytest.raises(ValueError, match=r'cannot find # character'):
        from_bytes(b'123')

    with pytest.raises(ValueError, match=r'character after # is not an integer'):
        from_bytes(b'#')

    with pytest.raises(ValueError, match=r'character after # is not an integer'):
        from_bytes(b'#A')

    with pytest.raises(ValueError, match=r'character after # is not an integer'):
        from_bytes(b'123#r')

    with pytest.raises(ValueError, match=r'characters after #3 are not integers'):
        from_bytes(b'#3a2')

    with pytest.raises(ValueError, match=r'characters after #3 are not integers'):
        from_bytes(b'#322a')

    with pytest.raises(ValueError, match=r'buffer is smaller'):
        from_bytes(b'#0\x00\x00\x00\x00\x00\x00\x80')

    with pytest.raises(ValueError, match=r'buffer is smaller'):
        from_bytes(b'#41024\x00\x00\x00\x00\x00\x00\x80')

    with pytest.raises(ValueError, match=r'cannot find #A character'):
        from_bytes(b'#22\x00\x00', fmt='hp')

    with pytest.raises(ValueError, match=r'characters after #A are not an unsigned short integer'):
        from_bytes(b'#A\x06', fmt='hp')

    with pytest.raises(ValueError, match='Invalid format'):
        from_bytes(b'', fmt='raw')


def test_from_bytes_hp():
    buffer = b'#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03' \
             b'\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00' \
             b'\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00'
    assert np.array_equal(from_bytes(buffer, fmt='hp', dtype='<i'), list(range(10)))

    buffer = b'#A\x00(\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00' \
             b'\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06' \
             b'\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t'
    assert np.array_equal(from_bytes(buffer, fmt='hp', dtype='>i'), list(range(10)))

    buffer = b'#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03' \
             b'\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00' \
             b'\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00\r\n'  # append CR+LF
    assert np.array_equal(from_bytes(buffer, fmt='hp', dtype='<i'), list(range(10)))

    array = from_bytes(b'#A\x00\x00', fmt='hp')
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    buffer = b'#A\x02\x00\x00\x00'
    assert np.array_equal(from_bytes(buffer, fmt='hp', dtype='<H'), [0])

    buffer = b'#A\x04\x00\x00\x00\x00\x01'
    assert np.array_equal(from_bytes(buffer, fmt='hp', dtype='<H'), [0, 256])


def test_from_bytes_ascii():
    buffer = b'1,2,3,4,5'
    expected = np.array([1, 2, 3, 4, 5], dtype=int)
    assert np.array_equal(from_bytes(buffer, fmt='ascii', dtype='<i'), expected)
    assert np.array_equal(from_bytes(bytearray(buffer), fmt='ascii', dtype='<i'), expected)
    assert np.array_equal(from_bytes(buffer.decode(), fmt='ascii', dtype='<i'), expected)

    buffer = b'1.1,2.2,3.3\n'
    expected = np.array([1.1, 2.2, 3.3], dtype=np.float32)
    assert np.array_equal(from_bytes(buffer, fmt='ascii'), expected)

    assert from_bytes('', fmt='ascii').size == 0
    assert np.array_equal(from_bytes('1', fmt='ascii', dtype='i'), [1])
    assert np.array_equal(from_bytes('1,2', fmt='ascii', dtype='i'), [1, 2])


@pytest.mark.parametrize(
    'size,fmt,dtype',
    [(0, None, int),
     (1, None, int),
     (2, None, int),
     (12345, None, '>Q'),
     (6432, None, np.ushort),
     (54, None, 'b'),
     (278, None, 'B'),
     (12, None, '<i'),
     (100, None, 'l'),
     (1234, None, float),
     (123456, None, 'd'),
     (0, 'ascii', 'd'),
     (1, 'ascii', 'd'),
     (2, 'ascii', 'd'),
     (12, 'ascii', '.2E'),
     (64321, 'ascii', 'f'),
     (54, 'ascii', ' .3f'),
     (278, 'ascii', 'g'),
     (12, 'ascii', '+.5e'),
     (100, 'ascii', ''),
     (100, 'ascii', '05d'),
     (0, 'ieee', int),
     (1, 'ieee', int),
     (2, 'ieee', int),
     (12345, 'ieee', '>Q'),
     (6432, 'ieee', np.ushort),
     (54, 'ieee', 'b'),
     (278, 'ieee', 'B'),
     (12, 'ieee', '<i'),
     (100, 'ieee', 'l'),
     (1234, 'ieee', float),
     (123456, 'ieee', 'd'),
     (0, 'hp', int),
     (1, 'hp', int),
     (2, 'hp', int),
     (6432, 'hp', np.ushort),
     (54, 'hp', '>Q'),
     (8000, 'hp', '<i'),
     (100, 'hp', 'l'),
     (100, 'hp', 'b'),
     (256, 'hp', '>l'),
     (1234, 'hp', float),
     (731, 'hp', 'B'),
     (128, 'hp', 'd')])
def test_to_bytes_from_bytes(size, fmt, dtype):
    if fmt == 'ascii':
        t = 'i' if 'd' in dtype else 'f'
        array = np.arange(size, dtype=t)
        buffer = to_bytes(array, fmt=fmt, dtype=dtype)
        assert np.array_equal(from_bytes(buffer, fmt=fmt, dtype=t), array)
    else:
        array = np.arange(size, dtype=dtype)
        buffer = to_bytes(array, fmt=fmt, dtype=dtype)
        assert np.array_equal(from_bytes(buffer, fmt=fmt, dtype=dtype), array)


def test_ipv4_addresses():
    assert len(ipv4_addresses()) >= 1


def test_parse_lxi_html1():
    string = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN">
<html>
  <head>
    <title>
Manufacturer Model <SerialNo.>  </title>
    <meta http-equiv="Content-Type" content= "text/html; charset=iso-8859-1">
  </head>
</html>
"""
    info = _parse_lxi_html(string)
    assert info['title'] == 'Manufacturer Model <SerialNo.>'


def test_parse_lxi_html2():
    string = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<link href="defultcss.css" rel="stylesheet" type="text/css">
<title>Company-Product Welcome Page    </title>
<style type="text/css">
<!--
-->
</style></head></html>
"""
    info = _parse_lxi_html(string)
    assert info['title'] == 'Company-Product Welcome Page'


def test_parse_lxi_html3():
    # no <title> tag
    string = '<html><body><h1>Hello, world!</h1></body></html>'
    info = _parse_lxi_html(string)
    assert info == {}


def test_parse_lxi_xml1():
    string = """<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentIdentification/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.lxistandard.org/InstrumentIdentification/1.0 http://hostname/Lxi/Identification/LxiIdentification.xsd">
  <Manufacturer>abcdefg</Manufacturer>
  <Model>xyz</Model>
  <SerialNumber>01234</SerialNumber>
  <FirmwareRevision>52.04.03</FirmwareRevision>
  <ManufacturerDescription>Our product</ManufacturerDescription>
  <HomepageURL>http://www.company.com/</HomepageURL>
  <DriverURL>http://www.company.com/drivers</DriverURL>
  <UserDescription>Buy our stuff</UserDescription>
  <IdentificationURL>http://hostname/Lxi/Identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4">
    <InstrumentAddressString>TCPIP::hostname::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::hostname::inst0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::hostname::5025::SOCKET</InstrumentAddressString>
    <Hostname>hostname</Hostname>
    <IPAddress>192.168.1.100</IPAddress>
    <SubnetMask>255.255.255.0</SubnetMask>
    <MACAddress>00-00-00-00-00-00</MACAddress>
    <Gateway>192.168.1.1</Gateway>
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <IVISoftwareModuleName>Device</IVISoftwareModuleName>
  <LXIVersion>1.4 LXI Core 2011</LXIVersion>
  <LXIExtendedFunctions>
    <Function FunctionName="LXI Wired Trigger Bus" Version="1.0" />
    <Function FunctionName="LXI Event Messaging" Version="1.0" />
    <Function FunctionName="LXI Clock Synchronization" Version="1.0" />
    <Function FunctionName="LXI Timestamped Data" Version="1.0" />
    <Function FunctionName="LXI Event Logs" Version="1.0" />
    <Function FunctionName="LXI IPv6" Version="1.0" />
    <Function FunctionName="LXI VXI-11" Version="1.0" />
    <Function FunctionName="LXI HiSLIP" Version="1.0">
      <Port>4880</Port>
    </Function>
  </LXIExtendedFunctions>
</LXIDevice>
"""
    info = _parse_lxi_xml(string)
    assert info == {
        'Manufacturer': 'abcdefg',
        'Model': 'xyz',
        'SerialNumber': '01234',
        'FirmwareRevision': '52.04.03',
        'ManufacturerDescription': 'Our product',
        'HomepageURL': 'http://www.company.com/',
        'DriverURL': 'http://www.company.com/drivers',
        'UserDescription': 'Buy our stuff',
        'IdentificationURL': 'http://hostname/Lxi/Identification',
        'Interfaces': [
            {
                'InterfaceType': 'LXI',
                'IPType': 'IPv4',
                'xsi:type': 'NetworkInformation',
                'InstrumentAddressStrings': [
                    'TCPIP::hostname::hislip0::INSTR',
                    'TCPIP::hostname::inst0::INSTR',
                    'TCPIP::hostname::5025::SOCKET'
                ],
                'Hostname': 'hostname',
                'IPAddress': '192.168.1.100',
                'SubnetMask': '255.255.255.0',
                'MACAddress': '00-00-00-00-00-00',
                'Gateway': '192.168.1.1',
                'DHCPEnabled': 'true',
                'AutoIPEnabled': 'true'
            }
        ],
        'IVISoftwareModuleName': 'Device',
        'LXIVersion': '1.4 LXI Core 2011',
        'LXIExtendedFunctions': [
            {'FunctionName': 'LXI Wired Trigger Bus', 'Version': '1.0'},
            {'FunctionName': 'LXI Event Messaging', 'Version': '1.0'},
            {'FunctionName': 'LXI Clock Synchronization', 'Version': '1.0'},
            {'FunctionName': 'LXI Timestamped Data', 'Version': '1.0'},
            {'FunctionName': 'LXI Event Logs', 'Version': '1.0'},
            {'FunctionName': 'LXI IPv6', 'Version': '1.0'},
            {'FunctionName': 'LXI VXI-11', 'Version': '1.0'},
            {'FunctionName': 'LXI HiSLIP', 'Version': '1.0', 'Port': '4880'}
        ]}


def test_parse_lxi_xml2():
    # change the LXI namespace and create a custom Interface
    string = """<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentId/2.17" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.lxistandard.org/InstrumentId/2.17  http://169.254.100.2/Lxi/LxiIdentification.xsd">
  <Manufacturer>Company</Manufacturer>
  <Model>Product</Model>
  <SerialNumber>xxxx</SerialNumber>
  <FirmwareRevision>1.06</FirmwareRevision>
  <ManufacturerDescription>Oscilloscope</ManufacturerDescription>
  <HomepageURL>http://www.company.com/</HomepageURL>
  <DriverURL>http://www.company.com/drivers</DriverURL>
  <UserDescription>Our best product</UserDescription>
  <IdentificationURL>http://hostname.local/lxi/identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4" InterfaceName="eth0">
    <InstrumentAddressString>TCPIP::hostname::5555::SOCKET</InstrumentAddressString>
    <Hostname>hostname</Hostname>
    <IPAddress>169.254.100.2</IPAddress>
    <SubnetMask>255.255.255.0</SubnetMask>
    <MACAddress>00:00:00:00:11:ab</MACAddress>
    <Gateway>169.254.100.1</Gateway>
    <DHCPEnabled>false</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <Interface InterfaceType="MyInterface" InterfaceName="MyName">
    <InstrumentAddressString>hostname:1234</InstrumentAddressString>
  </Interface>
  <Domain>1</Domain>
  <LXIVersion>1.5</LXIVersion>
</LXIDevice>
"""
    info = _parse_lxi_xml(string)
    assert info == {
        'Manufacturer': 'Company',
        'Model': 'Product',
        'SerialNumber': 'xxxx',
        'FirmwareRevision': '1.06',
        'ManufacturerDescription': 'Oscilloscope',
        'HomepageURL': 'http://www.company.com/',
        'DriverURL': 'http://www.company.com/drivers',
        'UserDescription': 'Our best product',
        'IdentificationURL': 'http://hostname.local/lxi/identification',
        'Interfaces': [
            {
                'InterfaceType': 'LXI',
                'IPType': 'IPv4',
                'xsi:type': 'NetworkInformation',
                'InterfaceName': 'eth0',
                'InstrumentAddressStrings': ['TCPIP::hostname::5555::SOCKET'],
                'Hostname': 'hostname',
                'IPAddress': '169.254.100.2',
                'SubnetMask': '255.255.255.0',
                'MACAddress': '00:00:00:00:11:ab',
                'Gateway': '169.254.100.1',
                'DHCPEnabled': 'false',
                'AutoIPEnabled': 'true'
            },
            {
                'InterfaceType': 'MyInterface',
                'InterfaceName': 'MyName',
                'InstrumentAddressStrings': ['hostname:1234']
            }
        ],
        'Domain': '1',
        'LXIVersion': '1.5'}


def test_parse_lxi_xml3():
    string = """<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentIdentification/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.lxistandard.org/InstrumentIdentification/1.0 http://10.12.102.2/Lxi/Identification/LxiIdentification.xsd">
  <Manufacturer>Manufacturer</Manufacturer>
  <Model>Model</Model>
  <SerialNumber>SerialNumber</SerialNumber>
  <FirmwareRevision>0.0.1</FirmwareRevision>
  <ManufacturerDescription>Manufacturer Description</ManufacturerDescription>
  <HomepageURL>http://www.home.page/</HomepageURL>
  <DriverURL>http://www.home.page/find/drivers</DriverURL>
  <UserDescription>User Description</UserDescription>
  <IdentificationURL>http://ip.address/Lxi/Identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4">
    <InstrumentAddressString>TCPIP::ip.address::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::inst0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::5025::SOCKET</InstrumentAddressString>
    <Hostname>ip.address</Hostname>
    <IPAddress>10.12.102.2</IPAddress>
    <SubnetMask>255.255.255.128</SubnetMask>
    <MACAddress>00-01-02-03-04-05</MACAddress>
    <Gateway>10.12.102.1</Gateway>
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv6">
    <InstrumentAddressString>TCPIP::ip.address::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::5025::SOCKET</InstrumentAddressString>
    <Hostname>ip.address</Hostname>
    <IPAddress>ab01::1234:2cd:ef03:0123a</IPAddress>
    <SubnetMask />
    <MACAddress>00-01-02-03-04-05</MACAddress>
    <Gateway />
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <IVISoftwareModuleName>Xx1234x</IVISoftwareModuleName>
  <LXIVersion>1.4 LXI Core 2011</LXIVersion>
  <LXIExtendedFunctions>
    <Function FunctionName="LXI HiSLIP" Version="1.0">
      <Port>4880</Port>
    </Function>
    <Function FunctionName="LXI IPv6" Version="1.0" />
  </LXIExtendedFunctions>
</LXIDevice>
"""
    info = _parse_lxi_xml(string)
    assert info == {
        'Manufacturer': 'Manufacturer',
        'Model': 'Model',
        'SerialNumber': 'SerialNumber',
        'FirmwareRevision': '0.0.1',
        'ManufacturerDescription': 'Manufacturer Description',
        'HomepageURL': 'http://www.home.page/',
        'DriverURL': 'http://www.home.page/find/drivers',
        'UserDescription': 'User Description',
        'IdentificationURL': 'http://ip.address/Lxi/Identification',
        'Interfaces': [
            {
                'InterfaceType': 'LXI',
                'IPType': 'IPv4',
                'xsi:type': 'NetworkInformation',
                'InstrumentAddressStrings': [
                    'TCPIP::ip.address::hislip0::INSTR',
                    'TCPIP::ip.address::inst0::INSTR',
                    'TCPIP::ip.address::5025::SOCKET'
                ],
                'Hostname': 'ip.address',
                'IPAddress': '10.12.102.2',
                'SubnetMask': '255.255.255.128',
                'MACAddress': '00-01-02-03-04-05',
                'Gateway': '10.12.102.1',
                'DHCPEnabled': 'true',
                'AutoIPEnabled': 'true'
            },
            {
                'InterfaceType': 'LXI',
                'IPType': 'IPv6',
                'xsi:type': 'NetworkInformation',
                'InstrumentAddressStrings': [
                    'TCPIP::ip.address::hislip0::INSTR',
                    'TCPIP::ip.address::5025::SOCKET',
                ],
                'Hostname': 'ip.address',
                'IPAddress': 'ab01::1234:2cd:ef03:0123a',
                'SubnetMask': None,
                'MACAddress': '00-01-02-03-04-05',
                'Gateway': None,
                'DHCPEnabled': 'true',
                'AutoIPEnabled': 'true'
            }
        ],
        'IVISoftwareModuleName': 'Xx1234x',
        'LXIVersion': '1.4 LXI Core 2011',
        'LXIExtendedFunctions': [
            {'FunctionName': 'LXI HiSLIP', 'Version': '1.0', 'Port': '4880'},
            {'FunctionName': 'LXI IPv6', 'Version': '1.0'}
        ]
    }


def test_parse_lxi_xml4():
    string = """<?xml version="1.0" encoding="UTF-8"?><Fruit><Apple/></Fruit>"""
    assert _parse_lxi_xml(string) == {}
