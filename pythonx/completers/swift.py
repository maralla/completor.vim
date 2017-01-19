# -*- coding: utf-8 -*-

import re
import json
import vim

from completor import Completor

pat = re.compile('\.\s*(\w*)$', re.U)


class SourceKitten(Completor):
    filetype = 'swift'
    trigger = r'[\w\)\]\}\'\"]+\.\w*$'

    def offset(self):
        line, col = vim.current.window.cursor
        line2byte = vim.Function('line2byte')
        return line2byte(line) + col - 1

    def format_cmd(self):
        binary = self.get_option('sourcekitten_binary') or 'sourcekitten'
        extra_args = self.get_option('sourcekitten_extra_args') or ''
        spm_module = self.get_option('sourcekitten_spm_module') or ''

        offset = self.offset() - 1

        match = pat.search(self.input_data)
        if match:
            start, end = match.span()
            offset -= end - start - 2

        args = [
            binary, 'complete',
            '--text', '\n'.join(vim.current.buffer[:]),
            '--offset', offset,
        ]
        if spm_module:
            args.extend(['--spm-module', spm_module])
        if extra_args:
            args.append('--')
            args.extend(extra_args.split())
        return args

    def parse(self, items):
        res = []
        try:
            data = json.loads(''.join(items))
        except Exception:
            data = []

        prefix = ''
        match = pat.search(self.input_data)
        if match:
            prefix, = match.groups()

        for item in data:
            word = item[b'descriptionKey']
            if not word.startswith(prefix):
                continue
            res.append({
                'word': word,
                'menu': item[b'kind'].replace('source.lang.swift.decl.', '')
            })
        return res
