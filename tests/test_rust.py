# -*- coding: utf-8 -*-

import mock
import completor
from completor.compat import to_unicode

from completers.rust import Racer  # noqa


def test_parse():
    items = [
        b'MATCH FrameHandler,155,7,./src/event.rs,Struct,struct FrameHandler',
        b'MATCH tcp_port,1075,4,./src/event.rs,StructField,Option<u16>',
        b'MATCH run,1092,11,./src/event.rs,Function,pub fn run(&mut self)'
    ]
    racer = completor.get('rust')
    racer.input_data = to_unicode('self.', 'utf-8')
    assert racer.get_completions(items) == [
        {'dup': 0, 'menu': b'struct FrameHandler', 'word': b'FrameHandler'},
        {'dup': 0, 'menu': b'Option<u16>', 'word': b'tcp_port'},
        {'dup': 0, 'menu': b'fn run(&mut self)', 'word': b'run'}
    ]


def test_request(vim_mod):
    vim_mod.funcs['completor#utils#tempname'] = mock.Mock(
        return_value=b'/tmp/vJBio2A/2.vim')
    vim_mod.current.buffer.name = '/home/vagrant/bench.vim'
    vim_mod.current.window.cursor = (1, 5)
    racer = completor.get('rust')
    racer.input_data = to_unicode('self.', 'utf-8')
    assert racer.request() == \
        'complete 1 5 /home/vagrant/bench.vim /tmp/vJBio2A/2.vim'


def test_message_end(vim_mod):
    racer = completor.get('rust')
    assert racer.is_message_end(b'END')
