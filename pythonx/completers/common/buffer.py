# -*- coding: utf-8 -*-

import collections
import itertools
import re
import vim

from completor import Completor

from .utils import test_subseq, LIMIT

word = re.compile('\w+$')


def getftime(nr):
    try:
        bufname = vim.Function('bufname')
        ftime = vim.Function('getftime')
        return ftime(bufname(nr))
    except vim.error:
        return -1


def filter_words(words):
    return (w for w in words if len(w) > 3)


class TokenStore(object):
    pat = re.compile('\w+')

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
        if nr == cur_nr:
            start = cur_line - 1000
            end = cur_line + 1000
            if start < 0:
                start = 0
            data = ' '.join(itertools.chain(buffer[start:cur_line],
                                            buffer[cur_line + 1:end]))
            self.current = set(filter_words(set(self.pat.findall(data))))
            self.current.difference_update([base])
        elif buffer.valid and len(buffer) <= 10000:
            ftime = getftime(nr)
            if ftime < 0:
                return
            if nr not in self.cache or ftime > self.cache[nr]['t']:
                self.cache[nr] = {'t': ftime}
                data = ' '.join(buffer[:])
                words = set(self.store)
                words.update(filter_words(set(self.pat.findall(data))))
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

        base = match.group()

        token_store.parse_buffers(base)

        res = set()
        for token, factor in token_store.search(base):
            if token == base:
                continue
            res.add((token, factor))
            if len(res) >= LIMIT:
                break

        res = list(res)
        res.sort(key=lambda x: x[1])
        return [{'word': token, 'menu': '[ID]'} for token, _ in res]
