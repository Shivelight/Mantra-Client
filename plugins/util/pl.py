# -*- coding: utf-8 -*-


def plugin(name=None, group=None, in_help=True, var=None):
    def wrapper(func):
        func.name = name
        func.group = group
        func.in_help = in_help
        func.is_plugin = True
        func.var = var
        return func
    return wrapper
