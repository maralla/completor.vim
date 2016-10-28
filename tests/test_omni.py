# -*- coding: utf-8 -*-

import completor
import re

from completers.common import Omni  # noqa


def sample_omnifunc(start, base):
    if start:
        return 1
    return [b'text-transform']


def test_has_omnifunc(vim_mod):
    vim_mod.vars = {
        'completor_css_omni_trigger': b'([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$'
    }
    vim_mod.current.buffer.options['omnifunc'] = b''

    omni = completor.get('omni')
    assert omni.has_omnifunc('css') is False

    omni.trigger_cache = {}
    vim_mod.current.buffer.options['omnifunc'] = b'csscomplete#CompleteCSS'
    assert omni.has_omnifunc('css') is True


def test_get_completions(vim_mod):
    vim_mod.current.buffer.options['omnifunc'] = b'csscomplete#CompleteCSS'
    vim_mod.funcs[b'csscomplete#CompleteCSS'] = sample_omnifunc

    omni = completor.get('omni')
    omni.trigger_cache = {}
    omni.ft = 'css'

    assert omni.get_completions('text') == []

    omni.trigger_cache = {
        'css': re.compile('([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$', re.X | re.U)}

    assert omni.get_completions('#') == []
    assert omni.get_completions('text') == [b'text-transform']
