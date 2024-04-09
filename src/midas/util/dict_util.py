"""This module contains a set of utility functions for dictionaries."""
import collections.abc
import numpy as np

from midas.util import LOG


def update(src, upd):
    """Recursive update of dictionaries.

    See stackoverflow:

        https://stackoverflow.com/questions/3232943/
        update-value-of-a-nested-dictionary-of-varying-depth

    """
    for key, val in upd.items():
        if isinstance(val, collections.abc.Mapping):
            src[key] = update(src.get(key, {}), val)
        else:
            src[key] = val
    return src


def convert(src):
    """Recursive conversion to basic data types."""
    for key, val in src.items():
        if isinstance(val, collections.abc.Mapping):
            src[key] = convert(val)
        elif isinstance(val, (list, np.ndarray)):
            src[key] = convert_list(val)
        else:
            src[key] = convert_val(val)
    return src


def convert_list(old_list):
    new_list = list()
    for val in old_list:
        if isinstance(val, collections.abc.Mapping):
            new_list.append(convert(val))
        elif isinstance(val, (list, tuple, np.ndarray)):
            new_list.append(convert_list(val))
        else:
            new_list.append(convert_val(val))
    return new_list


def convert_val(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return int(val)
    if isinstance(val, float):
        return float(val)

    try:
        return int(val)
    except (ValueError, TypeError):
        pass
    try:
        return float(val)
    except (ValueError, TypeError):
        pass
    try:
        return str(val)
    except (ValueError, TypeError):
        LOG.info("Unable to convert value %s", val)

    return "MISSING_VALUE"
