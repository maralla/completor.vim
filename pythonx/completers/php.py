# -*- coding: utf-8 -*-

import vim
import json
import pprint

from completor import Completor
from completor.compat import to_unicode

class Php(Completor):
    filetype = 'php'
    trigger = r'(?::\w{2,}\w*|->\w*)$'

    def offset(self):
        line, col = vim.current.window.cursor
        line2byte = vim.Function('line2byte')
        return line2byte(line) + col - 3

    def format_cmd(self):
        binary = self.get_option('phpactor_binary') or 'phpactor'
        return [binary, 'complete', self.tempname, self.offset(), '--format=json']

    def parse(self, data):
        res = []
        data = to_unicode(data[0], 'utf-8')
        data = json.loads(data)

        if 'error' in data:
            pprint.pprint(data)
            return []

        for item in data['suggestions']:
            res.append({
                'word': item['name'],
                'menu': item['type']
            })

        return res
