"""
Common functions.
"""
import datetime
import logging
from struct import pack
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
        * ``'ascii'`` -- comma-separated ASCII characters, see the
          `<PROGRAM DATA SEPARATOR>` standard that is defined in
          Section 7.4.2.2, `IEEE 488.2-1992`_.
        * ``'ieee'`` -- arbitrary block data for `SCPI` messages, see the
          `<DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>` standard that
          is defined in Section 8.7.9, `IEEE 488.2-1992`_.
          Syntax, ``#<length of num bytes value><num bytes><byte><byte><byte>...``.
        * ``'hp'`` -- the HP-IB data transfer standard, i.e., the `FORM#` command
          option. See the programming guide for an `HP 8530A`_ for more details.
          Syntax, ``#A<num bytes as uint16><byte><byte><byte>...``.

    dtype : :class:`str` or :class:`numpy.number`, optional
        The data type to cast each element in `iterable` to. If `fmt` is ``'ascii'``
        then `dtype` is used in :func:`format` to first convert each element
        in `iterable` to a string, and then it is encoded (e.g., ``'.2e'`` converts
        each element to scientific notation with two digits after the decimal point).
        If `dtype` includes a byte-order character, it is ignored. For all other
        values of `fmt`, the `dtype` can be a C-type or Python-type specification,
        for example, ``'H'``, ``'ushort'`` and ``numpy.uint16`` are equivalent
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
        return b'#A' + pack(array.dtype.byteorder + 'H', array.nbytes) + array.tobytes()

    if not fmt:
        return array.tobytes()

    raise ValueError("Invalid format {!r} -- must be 'ascii', 'ieee', 'hp' or None".format(fmt))
