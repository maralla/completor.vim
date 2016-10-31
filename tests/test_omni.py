# -*- coding: utf-8 -*-

import mock
import completor
import re

from completers.common import Omni  # noqa
from completor.compat import to_unicode


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
    omnifunc = mock.Mock()

    vim_mod.current.buffer.options['omnifunc'] = b'csscomplete#CompleteCSS'
    vim_mod.funcs[b'csscomplete#CompleteCSS'] = omnifunc

    omni = completor.get('omni')
    omni.trigger_cache = {}
    omni.ft = 'css'

    assert omni.get_completions('text') == []

    omni.trigger_cache = {
        'css': re.compile('([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$', re.X | re.U)}

    omnifunc.side_effect = [1, [b'text-transform']]
    assert omni.get_completions('#') == []

    omnifunc.side_effect = [0, [b'text-transform']]
    vim_mod.current.window.cursor = (1, 2)
    omni.input_data = 'text'
    assert omni.get_completions('text') == [b'text-transform']
    omnifunc.assert_called_with(0, b'text')

    omnifunc.side_effect = [17, [b'text-transform']]
    vim_mod.current.window.cursor = (1, 2)
    omni.input_data = to_unicode('które się nią opiekują', 'utf-8')
    omni.get_completions(omni.input_data)
    omnifunc.assert_called_with(0, b'opiekuj\xc4\x85')
