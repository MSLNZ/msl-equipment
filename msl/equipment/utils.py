"""
Common functions.
"""
import logging

logger = logging.getLogger(__name__)


def convert_to_enum(obj, enum, prefix=None, to_upper=False, strict=True):
    """Convert `obj` to an Enum.

    Parameters
    ----------
    obj : :class:`object`
        Any object to be converted to the specified `enum`. Can be a
        value of member of the specified `enum`.
    enum : :class:`~enum.Enum`
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
        The `enum`.

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
