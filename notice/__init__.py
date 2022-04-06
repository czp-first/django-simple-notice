# -*- coding: UTF-8 -*-
"""
@Summary : version
@Author  : Rey
@Time    : 2022-04-02 14:01:49
"""
VERSION = (0, 1, 0)


def get_version():
    """Return the version as a human-format string"""
    return ".".join([str(i) for i in VERSION])
