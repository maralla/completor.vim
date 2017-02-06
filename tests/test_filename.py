# -*- coding: utf-8 -*-

import os.path
import completor

from completers.common import Filename  # noqa


def test_get_completions(vim_mod):
    filename = completor.get('filename')

    vim_mod.vars = {}
    vim_mod.funcs['expand'] = lambda _: os.path.join(os.getcwd(), 'tests')
    data = list(set([item['menu'] for item in filename.get_completions('./')]))
    assert data == ['[F]']

    vim_mod.vars = {'completor_disable_filename': [b'python']}
    filename.ft = 'python'
    assert filename.disabled
