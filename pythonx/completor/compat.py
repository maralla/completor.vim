# -*- coding: utf-8 -*-

import sys


# py2
if sys.version_info[0] == 2:
    integer_types = (int, long)
    text_type = unicode

    to_bytes = lambda s: s
    to_str = lambda s: s

# py3
else:
    integer_types = (int,)
    text_type = str

    def to_bytes(s):
        return s.encode('utf-8')

    def to_str(s):
        return s.decode('utf-8')


def to_unicode(x, charset):
    if x is None:
        return None
    if not isinstance(x, bytes):
        return text_type(x)
    return x.decode(charset)
