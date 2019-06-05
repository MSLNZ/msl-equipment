"""
Common functions.
"""
import logging
import datetime
from xml.etree import cElementTree
from xml.dom import minidom

logger = logging.getLogger(__name__)

DEFAULT_DATE = datetime.date(datetime.MINYEAR, 1, 1)


def convert_to_enum(obj, enum, prefix=None, to_upper=False, strict=True):
    """Convert `obj` to an Enum.

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
    :class:`object`
        The `enum` value.

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


def string_to_none_bool_int_float_complex(string):
    """Convert a string into :data:`None`, :data:`True`, :data:`False`,
    :class:`int`, :class:`float` or :class:`complex`.

    Returns `string` if it cannot be converted to any of these types.

    0 and 1 get converted to an integer not a boolean.
    """
    su = string.upper()
    if su == 'NONE':
        return None
    if su == 'TRUE':
        return True
    if su == 'FALSE':
        return False
    for typ in (int, float, complex):
        try:
            return typ(string)
        except (ValueError, TypeError):
            pass
    return string


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


def convert_to_xml_string(element, indent='  ', encoding='utf-8'):
    """Convert an XML :class:`~xml.etree.ElementTree.Element` in to a string
    with proper indentation.

    Parameters
    ----------
    element : :class:`~xml.etree.ElementTree.Element`
        The element to convert.
    indent : :class:`str`
        The value to use for the indentation.
    encoding : :class:`str`
        The encoding to use.

    Returns
    -------
    :class:`str`
        The `element` as a pretty string. The returned value can be
        directly written to a file (i.e., it includes the XML declaration).

    Examples
    --------
    If the :class:`~xml.etree.ElementTree.Element` contains unicode
    characters then you should use the :mod:`codecs` module to create the file::

        import codecs
        with codecs.open('my_file.xml', mode='w', encoding='utf-8') as fp:
            fp.write(convert_to_xml_string(element))

    otherwise you can use the builtin :func:`open` function::

        with open('my_file.xml', mode='w') as fp:
            fp.write(convert_to_xml_string(element))

    """
    parsed = minidom.parseString(cElementTree.tostring(element))
    return parsed.toprettyxml(indent=indent, encoding=encoding).decode(encoding)
