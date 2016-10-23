# -*- coding: utf-8 -*-

from completor import Completor
from completor.compat import to_str

import vim
import re


class Omni(Completor):
    filetype = 'omni'
    sync = True

    trigger_cache = {}

    # ft: str
    def has_omnifunc(self, ft):
        if ft not in self.trigger_cache:
            name = 'completor_{}_omni_trigger'.format(ft)
            option = self.get_option(name)
            if not option:
                return False

            try:
                self.trigger_cache[ft] = re.compile(to_str(option), re.X | re.U)
            except Exception:
                return False

        try:
            return bool(vim.current.buffer.options['omnifunc'])
        except vim.error:
            return False

    def parse(self, base):
        ft = to_str(self.current_ft)
        trigger = self.trigger_cache.get(ft)
        enc_base = base.encode('unicode-escape').decode('utf-8')
        if not trigger or not trigger.search(enc_base):
            return []

        try:
            func_name = vim.current.buffer.options['omnifunc']
            if not func_name:
                return []

            omnifunc = vim.Function(func_name)
            start = omnifunc(1, '')
            if start < 0:
                return []
            return omnifunc(0, base[start:len(base)])
        except (vim.error, ValueError, KeyboardInterrupt):
            return []
