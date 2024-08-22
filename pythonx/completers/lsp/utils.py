# -*- coding: utf-8 -*-

try:
    from urlparse import unquote
except ImportError:
    from urllib.parse import unquote


def gen_uri(path):
    return 'file://' + path


def parse_uri(uri):
    if uri.startswith('file://'):
        return uri[7:]
    return uri


def to_filename(uri):
    return unquote(parse_uri(uri))
