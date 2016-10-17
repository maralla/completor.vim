# -*- coding: utf-8 -*-

import collections
import itertools
import re
import vim

from completor import Completor, get

LIMIT = 50
word = re.compile('\w+$')


def test_subseq(src, target):
    i = 0
    score = None
    src, target = src.lower(), target.lower()
    for index, e in enumerate(target):
        if e == src[i]:
            if index == 0:
                score = -999
            elif score is None:
                score = index
            else:
                score += index
            i += 1
        if i == len(src):
            return score


def getftime(nr):
    try:
        bufname = vim.Function('bufname')
        ftime = vim.Function('getftime')
        return ftime(bufname(nr))
    except vim.error:
        return -1


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
            self.current = set(self.pat.findall(data))
            self.current.difference_update([base])
        elif buffer.valid and len(buffer) <= 10000:
            ftime = getftime(nr)
            if ftime < 0:
                return
            if nr not in self.cache or ftime > self.cache[nr]['t']:
                self.cache[nr] = {'t': ftime}
                data = ' '.join(buffer[:])
                self.store.extend(set(self.pat.findall(data)))

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
        completions = []
        ultisnips = get('ultisnips')
        if ultisnips:
            completions.extend(ultisnips.parse(base))

        match = word.search(base)
        if not match:
            return completions

        ident = match.group()

        token_store.parse_buffers(ident)

        res = set()
        for token, factor in token_store.search(ident):
            if token == ident:
                continue
            res.add((token, factor))
            if len(res) >= LIMIT:
                break

        res = list(res)
        res.sort(key=lambda x: x[1])
        completions.extend([{'word': token, 'menu': '[ID]'}
                            for token, _ in res])
        return completions
