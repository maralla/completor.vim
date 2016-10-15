# -*- coding: utf-8 -*-

from completor import Completor, start_column

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
            start = vim.eval('function(&omnifunc)(1,"")')
            if start < 0:
                return []
            codepoint = start_column(ft, base)
            res = vim.eval('function(&omnifunc)(0,"{}")'.format(
                base[codepoint:len(base)]))
            if isinstance(res, dict) and 'words' in res:
                res = res['words']
            if not isinstance(res, list):
                return []
            return [r for r in res if r]
        except vim.error:
            return []
