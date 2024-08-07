# -*- coding: utf-8 -*-

import collections
import itertools
import re
import logging

from completor import Completor, vim, LIMIT, get_encoding as get_current_buffer_encoding
from completor.compat import to_unicode, to_bytes

from .utils import test_subseq

logger = logging.getLogger('completor')
word = re.compile(r'[^\W\d]\w*$', re.U)


def getftime(nr):
    try:
        bufname = vim.Function('bufname')
        ftime = vim.Function('getftime')
        return ftime(bufname(nr))
    except vim.error:
        return -1


def get_encoding(nr):
    try:
        getbufvar = vim.Function('getbufvar')
        encoding = getbufvar(nr, '&encoding')
    except vim.error:
        encoding = ''
    return to_unicode(encoding or 'utf-8', 'utf-8')


class TokenStore(object):
    pat = re.compile(r'[^\W\d]{3}\w{0,45}', re.U)

    def __init__(self):
        self.cache = {}
        self.store = collections.deque(maxlen=10000)
        self.current = set()

    def search(self, base):
        words = itertools.chain(self.current, self.store)
        for token in words:
            score = test_subseq(base, token)
            if score is None:
                continue
            yield token, (score, len(token))

    def store_buffer(self, buffer, base, cur_nr, cur_line):
        nr = buffer.number
        encoding = get_encoding(nr)

        if nr == cur_nr:
            start = cur_line - 1000
            end = cur_line + 1000
            if start < 0:
                start = 0
            data = ' '.join(itertools.chain(buffer[start:cur_line],
                                            buffer[cur_line + 1:end]))
            self.current = set(self.pat.findall(to_unicode(data, encoding)))
            self.current.difference_update([base])
        elif buffer.valid and len(buffer) <= 10000:
            ftime = getftime(nr)
            if ftime < 0:
                return
            if nr not in self.cache or ftime > self.cache[nr]['t']:
                self.cache[nr] = {'t': ftime}
                data = to_unicode(' '.join(buffer[:]), encoding)
                words = set(self.store)
                words.update(set(self.pat.findall(data)))
                self.store.clear()
                self.store.extend(words)

    def parse_buffers(self, base):
        nr = vim.current.buffer.number
        line, _ = vim.current.window.cursor

        for buffer in vim.buffers:
            self.store_buffer(buffer, base, nr, line)


token_store = TokenStore()


class Buffer(Completor):
    filetype = 'buffer'
    sync = True

    def parse(self, base):
        match = word.search(base)
        if not match:
            return []
        identifier = match.group()
        if len(identifier) < self.get_option('min_chars'):
            return []
        token_store.parse_buffers(identifier)

        res = set()
        for token, factor in token_store.search(identifier):
            if token == identifier:
                continue
            line = self.cursor_line
            column = len(self.input_data)
            if (identifier + line[column:])[:len(token)] == token:
                continue
            res.add((token, factor))
            if len(res) >= LIMIT:
                break

        # NOTE: base class Completor expects the offset in nr of bytes in the
        # buffer's encoding (Completor.start_column will also be in nr of bytes)
        current_buf_encoding = get_current_buffer_encoding()
        offset = (len(to_bytes(base, current_buf_encoding)) -
                  len(to_bytes(identifier, current_buf_encoding)))

        res = list(res)
        res.sort(key=lambda x: (x[1], x[0]))
        return [{'word': token, 'menu': '[ID]', 'offset': offset}
                for token, _ in res]
