# -*- coding: utf-8 -*-

import re
import vim

from completor import Completor


LIMIT = 50
word = re.compile('\w+$')


def gen_tokens(base):
    current = vim.current.buffer
    line, _ = vim.current.window.cursor

    pat = re.compile('{}\w+'.format(base), re.M | re.I)

    for buffer in vim.buffers:
        if not buffer.valid or \
                (buffer.number != current.number and len(buffer) > 10000):
            continue

        if buffer.number == current.number:
            start = line - 1000
            end = line + 1000
            if start < 0:
                start = 0
            data = '\n'.join(buffer[start:end])
        else:
            data = '\n'.join(buffer[:])
        for match in pat.finditer(data):
            yield match.group()


class Buffer(Completor):
    filetype = 'buffer'

    sync = True

    def parse(self, base):
        match = word.search(base)
        if not match:
            return []

        base = match.group()

        res = set()

        for token in gen_tokens(base):
            res.add(token)
            if len(res) >= LIMIT:
                break

        return [{'word': token, 'menu': '[ID]'} for token in res]
