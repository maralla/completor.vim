# -*- coding: utf-8 -*-

from completor import Completor

import vim
import re


class Omni(Completor):
    filetype = 'omni'
    sync = True

    name_map = {}
    trigger_cache = {}

    def has_omnifunc(self, ft):
        name = self.name_map.get(ft, 'completor_{}_omni_trigger'.format(ft))
        option = self.get_option(name)
        if not option:
            return False

        try:
            self.trigger_cache[ft] = re.compile(option)
        except Exception:
            return False

        try:
            return bool(vim.eval('&omnifunc'))
        except vim.error:
            return False

    def parse(self, base):
        ft = vim.eval('&ft')
        trigger = self.trigger_cache.get(ft)
        enc_base = base.encode('unicode-escape').decode('utf-8')
        if not trigger or not trigger.search(enc_base):
            return []

        try:
            func_name = vim.eval('&omnifunc')
            if not func_name:
                return []

            omnifunc = vim.Function(func_name)
            start = omnifunc(1, '')
            if start < 0:
                return []
            return omnifunc(0, base[start:len(base)])
        except (vim.error, ValueError, KeyboardInterrupt):
            return []
