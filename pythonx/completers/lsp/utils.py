# -*- coding: utf-8 -*-


def gen_uri(path):
    return 'file://' + path


def parse_uri(uri):
    if uri.startswith('file://'):
        return uri[7:]
    return uri
