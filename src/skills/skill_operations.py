# Filter-MSMARCO
# @File:   skill_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

from copy import deepcopy


def mix_skills(base, **kwargs):
    new = deepcopy(base)
    for k, v in kwargs.items():
        new[k] = v
    return new
