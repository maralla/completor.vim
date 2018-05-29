# -*- coding: utf-8 -*-

import logging
import subprocess
from completor import Completor, vim

logger = logging.getLogger('completor')


class Go(Completor):
    filetype = 'go'
    trigger = r'(?:\w{2,}\w*|\.\w*)$'

    def offset(self):
        line, col = vim.current.window.cursor
        line2byte = vim.Function('line2byte')
        return line2byte(line) + col - 1

    def format_cmd(self):
        binary = self.get_option('gocode_binary') or 'gocode'
        return [binary, '-f=csv-with-package', '-in={}'.format(self.tempname),
                'autocomplete', self.filename, self.offset()]

    def parse(self, items):
        res = []
        for item in items:
            parts = item.split(b',,')
            if len(parts) < 4:
                continue
            res.append({
                'word': parts[1],
                'menu': parts[2],
                'info': subprocess.check_output(['godoc', parts[3], parts[1].decode('utf-8')])
            })
        return res
