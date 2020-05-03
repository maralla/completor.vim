# -*- coding: utf-8 -*-

import mock
import completor
import completers.common  # noqa
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
    assert racer.on_data(b'complete', items) == [
        {'offset': 5, 'dup': 0, 'menu': b'struct FrameHandler', 'word': b'FrameHandler'},  # noqa
        {'offset': 5, 'dup': 0, 'menu': b'Option<u16>', 'word': b'tcp_port'},
        {'offset': 5, 'dup': 0, 'menu': b'fn run(&mut self)', 'word': b'run'}
    ]


def test_request(vim_mod):
    vim_mod.funcs['completor#utils#tempname'] = mock.Mock(
        return_value=b'/tmp/vJBio2A/2.vim')
    vim_mod.current.buffer.name = '/home/vagrant/bench.vim'
    vim_mod.current.window.cursor = (1, 5)
    racer = completor.get('rust')
    racer.input_data = to_unicode('self.', 'utf-8')
    assert racer.prepare_request(b'complete') == \
        'complete 1 5 /home/vagrant/bench.vim /tmp/vJBio2A/2.vim'


def test_message_end(vim_mod):
    racer = completor.get('rust')
    assert racer.is_message_end(b'END')


def test_on_doc(vim_mod):
    racer = completor.get('rust')
    data = [
        (b'MATCH io;io;1;1;'
         b'/Users/maralla/Workspace/src/rust/src/libstd/io/mod.rs;Module;'
         b'/Users/maralla/Workspace/src/rust/src/libstd/io/mod.rs;'
         b'"Traits, helpers, and type definitions for core I/O functionality.'
         b'\\n\\nThe `std::io` module contains a number of common things'
         b" you\\'ll need\\nwhen doing input and output.\"")
    ]
    r = racer.on_doc(data)
    assert r == [b"Traits, helpers, and type definitions for core I/O"
                 b" functionality.\n\nThe `std::io` module contains a number"
                 b" of common things you'll need\nwhen doing input and "
                 b"output."]
