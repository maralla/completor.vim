# -*- coding: utf-8 -*-

import sys


# py2
if sys.version_info[0] == 2:
    integer_types = (int, long)

    to_bytes = lambda s: s
    to_str = lambda s: s

# py3
else:
    integer_types = (int,)

    def to_bytes(s):
        return s.encode('utf-8')

    def to_str(s):
        return s.decode('utf-8')
