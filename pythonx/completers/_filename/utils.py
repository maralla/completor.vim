# -*- coding: utf-8 -*-

PATH_PATTERN = r"""
    # Head part
    (?:
    # '/', './', '../', or '~'
    \.{0,2}/|~|

    # '$var/'
    \$[A-Za-z0-9{}_]+/
    )+

    # Tail part
    (?:
    # any alphanumeric, symbol or space literal
    [/a-zA-Z0-9(){}$+_~.\x80-\xff-\[\]]|

    # skip any special symbols
    [^\x20-\x7E]|

    # backslash and 1 char after it
    \\.
    )*$"""
