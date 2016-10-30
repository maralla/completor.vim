# -*- coding: utf-8 -*-

from completor import Completor
from completor.compat import to_unicode, nvim

import vim
import re

from .utils import REGEX_MAP


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
                self.trigger_cache[ft] = re.compile(
                    to_unicode(option, 'utf-8'), re.X | re.U)
            except Exception:
                return False

        try:
            return bool(vim.current.buffer.options['omnifunc'])
        except vim.error:
            return False

    def start_column(self):
        sup = super(Omni, self)
        pat = REGEX_MAP.get(self.ft) or sup.ident
        if isinstance(pat, str):
            pat = re.compile(pat, re.U | re.X)
        idx = self.ident_match(pat)
        return idx

    def parse(self, base):
        trigger = self.trigger_cache.get(self.ft)
        if not trigger or not trigger.search(base):
            return []

        try:
            func_name = vim.current.buffer.options['omnifunc']
            if not func_name:
                return []

            if nvim:
                start = int(vim.eval(func_name + '(1, "")'))
                if start < 0:
                    return []
                return int(vim.eval(func_name = '(0, "%s")' % base[start:len(base)]))
            else:
                omnifunc = vim.Function(func_name)
                start = omnifunc(1, '')
                if start < 0:
                    return []
                return omnifunc(0, base[start:len(base)])
        except (vim.error, ValueError, KeyboardInterrupt):
            return []
