# -*- coding: utf-8 -*-

import completor
from completers.rust import Racer  # noqa


def test_parse():
    items = [
        b'MATCH FrameHandler,155,7,./src/event.rs,Struct,struct FrameHandler',
        b'MATCH tcp_port,1075,4,./src/event.rs,StructField,Option<u16>',
        b'MATCH run,1092,11,./src/event.rs,Function,pub fn run(&mut self)'
    ]
    racer = completor.get('rust')
    assert racer.get_completions(items) == [
        {'dup': 0, 'menu': b'struct FrameHandler', 'word': b'FrameHandler'},
        {'dup': 0, 'menu': b'Option<u16>', 'word': b'tcp_port'},
        {'dup': 0, 'menu': b'fn run(&mut self)', 'word': b'run'}
    ]
