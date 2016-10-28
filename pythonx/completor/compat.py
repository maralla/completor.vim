# -*- coding: utf-8 -*-

import sys


# py2
if sys.version_info[0] == 2:
    integer_types = (int, long)
    text_type = unicode

    def to_bytes(s, charset='utf-8'):
        return s

# py3
else:
    integer_types = (int,)
    text_type = str

    def to_bytes(s, charset='utf-8'):
        return s.encode(charset)


def to_unicode(x, charset):
    if x is None:
        return None
    if not isinstance(x, bytes):
        return text_type(x)
    return x.decode(charset)
