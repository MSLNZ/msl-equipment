"""
Common functions.
"""
import datetime
import logging
import struct
from xml.dom import minidom
from xml.etree import cElementTree

import numpy as np

from .constants import DEFAULT_DATE


def _demo_logger(self, msg, *args, **kwargs):
    """A custom logger for :class:`~msl.equipment.connection_demo.ConnectionDemo` objects."""
    if self.isEnabledFor(logging.DEMO):
        self._log(logging.DEMO, msg, args, **kwargs)


logger = logging.getLogger(__package__)

# create a demo logger level between INFO and WARNING
logging.DEMO = logging.INFO + 5
logging.addLevelName(logging.DEMO, 'DEMO')
logging.Logger.demo = _demo_logger


def convert_to_enum(obj, enum, prefix=None, to_upper=False, strict=True):
    """Convert `obj` to an :class:`~enum.Enum` member.

    Parameters
    ----------
    obj : :class:`object`
        Any object to be converted to the specified `enum`. Can be a
        value of member of the specified `enum`.
    enum : Type[:class:`~enum.Enum`]
        The :class:`~enum.Enum` object that `obj` should be converted to.
    prefix : :class:`str`, optional
        If `obj` is a :class:`str`, then ensures that `prefix` is included at
        the beginning of `obj` before converting `obj` to the `enum`.
    to_upper : :class:`bool`, optional
        If `obj` is a :class:`str`, then whether to change `obj` to
        be upper case before converting `obj` to the `enum`.
    strict : :class:`bool`, optional
        Whether errors should be raised. If :data:`False` and `obj` cannot
        be converted to `enum` then `obj` is returned and the error is
        logged.

    Returns
    -------
    :class:`~enum.Enum`
        The `enum` member.

    Raises
    ------
    ValueError
        If `obj` is not in `enum` and `strict` is :data:`True`.
    """
    try:
        return enum(obj)
    except ValueError:
        pass

    # then `obj` must the Enum member name
    name = '{}'.format(obj).replace(' ', '_')
    if prefix and not name.startswith(prefix):
        name = prefix + name
    if to_upper:
        name = name.upper()

    try:
        return enum[name]
    except KeyError:
        pass

    msg = 'Cannot create {} from {!r}'.format(enum, obj)
    if strict:
        raise ValueError(msg)

    logger.error(msg)
    return obj


def convert_to_primitive(text):
    """Convert text into a primitive value.

    Parameters
    ----------
    text : :class:`str` or :class:`bytes`
        The text to convert.

    Returns
    -------
    The `text` as a :data:`None`, :class:`bool`, :class:`int`,
    :class:`float` or :class:`complex` object. Returns the
    original `text` if it cannot be converted to any of these types.
    The text 0 and 1 get converted to an integer not a boolean.
    """
    try:
        upper = text.upper().strip()
    except AttributeError:
        return text

    if upper == 'NONE':
        return None
    if upper == 'TRUE':
        return True
    if upper == 'FALSE':
        return False

    # TODO could consider using ast.literal_eval if text representations of
    #  list, dict, set, tuple would like to be supported
    for typ in (int, float, complex):
        try:
            return typ(text)
        except (ValueError, TypeError):
            pass

    return text


def convert_to_date(obj, fmt='%Y-%m-%d', strict=True):
    """Convert an object to a :class:`datetime.date` object.

    Parameters
    ----------
    obj : :class:`datetime.date`, :class:`datetime.datetime` or :class:`str`
        Any object that can be converted to a :class:`datetime.date` object.
    fmt : :class:`str`
        If `obj` is a :class:`str` then the format to use to convert `obj` to a
        :class:`datetime.date`.
    strict : :class:`bool`, optional
        Whether errors should be raised. If :data:`False` and `obj` cannot
        be converted to :class:`datetime.date` then ``datetime.date(datetime.MINYEAR, 1, 1)``
        is returned and the error is logged.

    Returns
    -------
    :class:`datetime.date`
        A :class:`datetime.date` object.
    """
    if isinstance(obj, datetime.date):
        return obj

    if isinstance(obj, datetime.datetime):
        return obj.date()

    if obj is None:
        return DEFAULT_DATE

    try:
        return datetime.datetime.strptime(obj, fmt).date()
    except (ValueError, TypeError) as e:
        if strict:
            raise
        else:
            logger.error(e)
            return DEFAULT_DATE


def convert_to_xml_string(element, indent='  ', encoding='utf-8', fix_newlines=True):
    """Convert an XML :class:`~xml.etree.ElementTree.Element` in to a string
    with proper indentation.

    Parameters
    ----------
    element : :class:`~xml.etree.ElementTree.Element`
        The element to convert.
    indent : :class:`str`, optional
        The value to use for the indentation.
    encoding : :class:`str`, optional
        The encoding to use.
    fix_newlines : :class:`bool`, optional
        Whether to remove newlines inside text nodes.

    Returns
    -------
    :class:`str`
        The `element` as a pretty string. The returned value can be
        directly written to a file (i.e., it includes the XML declaration).

    Examples
    --------
    If the :class:`~xml.etree.ElementTree.Element` contains unicode
    characters then you should use the :mod:`codecs` module to create the file
    if you are using Python 2.7::

        import codecs
        with codecs.open('my_file.xml', mode='w', encoding='utf-8') as fp:
            fp.write(convert_to_xml_string(element))

    otherwise you can use the builtin :func:`open` function::

        with open('my_file.xml', mode='w', encoding='utf-8') as fp:
            fp.write(convert_to_xml_string(element))

    """
    parsed = minidom.parseString(cElementTree.tostring(element))
    pretty = parsed.toprettyxml(indent=indent, encoding=encoding).decode(encoding)
    if fix_newlines:
        return '\n'.join(s for s in pretty.splitlines() if s.strip())
    return pretty


def xml_element(tag, text=None, tail=None, **attributes):
    """Create a new XML element.

    Parameters
    ----------
    tag : :class:`str`
        The element's name.
    text : :class:`str`, optional
        The text before the first sub-element. Can either be a string or :data:`None`.
    tail : :class:`str`, optional
        The text after this element's end tag, but before the next sibling element's start tag.
    attributes
        All additional key-value pairs are included as XML attributes
        for the element. The value must be of type :class:`str`.

    Returns
    -------
    :class:`~xml.etree.ElementTree.Element`
        The new XML element.
    """
    element = cElementTree.Element(tag, **attributes)
    element.text = text
    element.tail = tail
    return element


def xml_comment(text):
    """Create a new XML comment element.

    Parameters
    ----------
    text : :class:`str`
        The comment.

    Returns
    -------
    :func:`~xml.etree.ElementTree.Comment`
        A special element that is an XML comment.
    """
    return cElementTree.Comment(text)


def to_bytes(iterable, fmt='ieee', dtype='<f'):
    """Convert an iterable of numbers into bytes.

    .. _IEEE 488.2-1992: https://standards.ieee.org/ieee/488.2/718/
    .. _HP 8530A: https://www.keysight.com/us/en/product/8530A/microwave-receiver.html#resources

    Parameters
    ----------
    iterable
        An object to convert to bytes. Must be a 1-dimensional sequence of elements
        (not a multidimensional array).
    fmt : :class:`str` or :data:`None`, optional
        The format to use to convert `iterable`. Possible values are:

        * ``''`` (empty string or :data:`None`) -- convert `iterable` to bytes
          without a header.

          .. centered:: None: ``<byte><byte><byte>...``

        * ``'ascii'`` -- comma-separated ASCII characters, see the
          `<PROGRAM DATA SEPARATOR>` standard that is defined in Section 7.4.2.2,
          `IEEE 488.2-1992`_.

          .. centered:: ascii: ``<string>,<string>,<string>,...``

        * ``'ieee'`` -- arbitrary block data for `SCPI` messages, see the
          `<DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>` standard that
          is defined in Section 8.7.9, `IEEE 488.2-1992`_.

          .. centered:: ieee: ``#<length of num bytes value><num bytes><byte><byte><byte>...``

        * ``'hp'`` -- the HP-IB data transfer standard, i.e., the `FORM#` command
          option. See the programming guide for an `HP 8530A`_ for more details.

          .. centered:: hp: ``#A<num bytes as uint16><byte><byte><byte>...``

    dtype : :class:`str` or :class:`numpy.number`, optional
        The data type to cast each element in `iterable` to. If `fmt` is ``'ascii'``
        then `dtype` is used in :func:`format` to first convert each element
        in `iterable` to a string, and then it is encoded (e.g., ``'.2e'`` converts
        each element to scientific notation with two digits after the decimal point).
        If `dtype` includes a byte-order character, it is ignored. For all other
        values of `fmt`, the `dtype` can be a C-type or Python-type specification,
        for example, ``'H'``, ``'uint16'`` and :class:`numpy.ushort` are equivalent
        specifications to cast each element to an `unsigned short`. If a byte-order
        character is specified then it is used, otherwise the native byte order
        of the CPU architecture is used.

    Returns
    -------
    :class:`bytes`
        The `iterable` converted to bytes.
    """
    if fmt == 'ascii':
        format_spec = dtype.lstrip('@=<>!')
        return ','.join(format(item, format_spec) for item in iterable).encode('ascii')

    if isinstance(iterable, np.ndarray):
        array = iterable.astype(dtype=dtype)
    else:
        array = np.fromiter(iterable, dtype=dtype, count=len(iterable))

    if fmt == 'ieee':
        nbytes = str(array.nbytes)
        len_nbytes = len(nbytes)
        if len_nbytes > 9:
            # The IEEE-488.2 format allows for 1 digit to specify the number
            # of bytes in the array. This is extremely unlikely to occur in
            # practice since the instrument would require > 1GB of memory.
            raise OverflowError('length too big for IEEE-488.2 specification')
        return '#{}{}'.format(len_nbytes, nbytes).encode() + array.tobytes()

    if fmt == 'hp':
        byteorder = array.dtype.byteorder
        if byteorder == '|':
            # | means not applicable for the dtype specified, assign little endian
            # this redefinition is also declared in from_bytes()
            byteorder = '<'
        return b'#A' + struct.pack(byteorder + 'H', array.nbytes) + array.tobytes()

    if not fmt:
        return array.tobytes()

    raise ValueError("Invalid format {!r} -- must be 'ascii', 'ieee', 'hp' or None".format(fmt))


def from_bytes(buffer, fmt='ieee', dtype='<f'):
    """Convert bytes into an array.

    Parameters
    ----------
    buffer : :class:`bytes`, :class:`bytearray` or :class:`str`
        A byte buffer. Can be of type :class:`str`, but only if `fmt`
        equals ``'ascii'``.
    fmt : :class:`str` or :data:`None`, optional
        The format that `buffer` is in.
        See :func:`.to_bytes` for more details.
    dtype : :class:`str` or :class:`numpy.number`, optional
        The data type of each element in `buffer`.
        See :func:`.to_bytes` for more details.

    Returns
    -------
    :class:`numpy.ndarray`
        The array.
    """
    if fmt == 'ieee':
        offset = buffer.find(b'#')
        if offset == -1:
            raise ValueError('Invalid IEEE-488.2 format, '
                             'cannot find # character')

        try:
            len_nbytes = int(buffer[offset+1:offset+2])
        except ValueError:
            len_nbytes = None

        if len_nbytes is None:
            raise ValueError('Invalid IEEE-488.2 format, '
                             'character after # is not an integer')

        if len_nbytes == 0:
            # <INDEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>
            # Section 8.7.10, IEEE 488.2-1992
            nbytes = len(buffer) - offset

            # The standard states that the buffer must end in a NL (\n) character.
            # Not sure if a manufacturer will always honor this requirement, or if
            # it has already been stripped from the buffer
            if buffer.endswith(b'\n'):
                nbytes -= 1
        else:
            # <DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>
            # Section 8.7.9, IEEE 488.2-1992
            try:
                nbytes = int(buffer[offset + 2:offset + 2 + len_nbytes])
            except ValueError:
                nbytes = None

        if nbytes is None:
            raise ValueError('Invalid IEEE-488.2 format, '
                             'characters after #{} are not integers'.format(len_nbytes))

        dtype = np.dtype(dtype)
        offset += 2 + len_nbytes
        count = nbytes // dtype.itemsize
        return np.frombuffer(buffer, dtype=dtype, count=count, offset=offset)

    if fmt == 'hp':
        offset = buffer.find(b'#A')
        if offset == -1:
            raise ValueError('Invalid HP format, cannot find #A character')

        dtype = np.dtype(dtype)
        i, j = offset + 2, offset + 4

        byteorder = dtype.byteorder
        if byteorder == '|':
            # | means not applicable for the dtype specified, assign little endian
            # this redefinition is also declared in to_bytes()
            byteorder = '<'

        try:
            nbytes, = struct.unpack(byteorder + 'H', buffer[i:j])
        except struct.error:
            nbytes = None

        if nbytes is None:
            raise ValueError('Invalid HP format, '
                             'characters after #A are not an unsigned short integer')

        count = nbytes // dtype.itemsize
        return np.frombuffer(buffer, dtype=dtype, count=count, offset=j)

    if fmt == 'ascii':
        if isinstance(buffer, (bytes, bytearray)):
            buffer = buffer.decode('ascii')
        return np.fromstring(buffer, dtype=dtype, sep=',')

    if not fmt:
        return np.frombuffer(buffer, dtype=dtype)

    raise ValueError("Invalid format {!r} -- must be 'ascii', 'ieee', 'hp' or None".format(fmt))
