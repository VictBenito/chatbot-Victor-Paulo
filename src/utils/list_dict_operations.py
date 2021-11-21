# Filter-MSMARCO
# @File:   list_dict_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

from copy import deepcopy
from typing import List, Tuple


def drop_duplicates(ls: list) -> list:
    """Removes empty and duplicated elements from a list."""
    return list(filter(None, set(ls)))


def flatten(ls: list) -> list:
    """Flattens a list by 1 dimension."""
    return [item for sublist in ls for item in sublist]


def unzip(zipped: List[Tuple]) -> Tuple[List]:
    """Does the opposite of zip() -- returns a tuple of lists."""
    return tuple(zip(*zipped))


def remove(ls: list, to_remove: list) -> list:
    """Subtracts one list from another."""
    return [item for item in ls if item not in to_remove]


def inner_join(a: list, b: list):
    return [v for v in a + b if v in a and v in b]


def is_flat(x) -> bool:
    """Returns true if the input is neither a list nor a dict."""
    return not (isinstance(x, list) or isinstance(x, dict))


def is_flat_list(x) -> bool:
    """Returns whether a list is flat."""
    return all(is_flat(y) for y in x)


def mix_list(a: list, b: list, priority: dict = None) -> list:
    """
    Performs an outer join between lists by first converting them to
    dictionaries. Accepts an optional dict that sets the priority for
    choosing which of possible keys to use as the global key between dicts.
    """
    if priority is None:
        priority = {}
    if is_flat_list(a) and is_flat_list(b):
        return drop_duplicates(a + b)
    elif is_flat_list(a) or is_flat_list(b):
        raise ValueError(a, b)

    a_keys = get_possible_global_keys(a)
    b_keys = get_possible_global_keys(b)
    common_keys = inner_join(a_keys, b_keys)
    if len(common_keys) > 0:
        common_keys.sort(key=lambda x: priority.get(x, 999))
        a_key = common_keys[0]
        b_key = a_key
    else:
        raise ValueError(
            f"Different global keys were found for each list: {a_keys} "
            f"and {b_keys}, respectively"
        )

    a_dict = {subdict[a_key]: subdict for subdict in a}
    b_dict = {subdict[b_key]: subdict for subdict in b}
    mixed_dicts = mix_dict(a_dict, b_dict)
    return list(mixed_dicts.values())


def get_possible_global_keys(ls: List[dict]) -> List[str]:
    """
    Out of a list of dicts, returns a list of keys which exist, are unique and
    flat in all dicts.
    >>> people = [{'name': 'george', 'age': 27}, {'name': 'kali', 'age': 27}]
    >>> get_possible_global_keys(people)
    ['name']
    >>> fruits = [
    ...     {'name': 'pear', 'price': 2},
    ...     {'name': 'banana', 'price': 1},
    ...     {'name': 'apple', 'price': 2, 'color': 'green'},
    ...     {'name': 'apple', 'price': 2, 'color': 'red'},
    ... ]
    >>> get_possible_global_keys(fruits)
    []
    """
    first_dict = ls[0]
    global_keys = []
    for key in first_dict:
        # if not all dicts have this key
        if not all(key in d_ for d_ in ls):
            continue
        # if the value for this key is not flat in all dicts
        if not all(is_flat(d_[key]) for d_ in ls):
            continue
        # if not all dicts have a truthy value for this key
        if not all(bool(d_[key]) for d_ in ls):
            continue
        # if not all dicts have a unique value for this key
        if not len(set(d_[key] for d_ in ls)) == len(ls):
            continue
        global_keys.append(key)
    return global_keys


def mix_dict(a: dict, b: dict) -> dict:
    """
    Returns a dict containing items from both dicts and using values from
    b on key conflicts.
    """
    out = deepcopy(b)
    for k, v in a.items():
        if k not in out:
            out[k] = v
        elif isinstance(v, list):
            if not isinstance(b[k], list):
                raise ValueError(f"a is a list in {k}, but b is {type(b[k])}")
            out[k] = mix_list(v, b[k])
        elif isinstance(v, dict):
            if not isinstance(b[k], dict):
                raise ValueError(f"a is a dict in {k}, but b is {type(b[k])}")
            out[k] = mix_dict(v, b[k])
        else:
            out[k] = v
    return out


def remove_nans(d: dict) -> dict:
    """Removes keys with nan value from a dict."""
    return {k: v for k, v in d.items() if v == v}
