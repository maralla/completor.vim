# -*- coding: utf-8 -*-

from completor import Completor, get_encoding, vim
from completor.compat import to_unicode, to_bytes

import re
import logging

from .utils import REGEX_MAP

logger = logging.getLogger('completor')


class Omni(Completor):
    filetype = 'omni'
    sync = True

    trigger_cache = {}

    # ft: str
    def has_omnifunc(self, ft):
        if ft not in self.trigger_cache:
            name = '{}_omni_trigger'.format(ft)
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

    # base: unicode
    def parse(self, base):
        trigger = self.trigger_cache.get(self.ft)
        if not trigger or not trigger.search(base):
            return []

        cursor = self.cursor
        try:
            func_name = vim.current.buffer.options['omnifunc']
            logger.info('omnifunc: %s', func_name)
            if not func_name:
                return []

            omnifunc = vim.Function(func_name)
            start = omnifunc(1, '')
            codepoint = self.start_column()
            logger.info('start: %s,%s', start, codepoint)
            if start < 0 or start != codepoint:
                return []
            res = omnifunc(0, to_bytes(base, get_encoding())[codepoint:])
            for i, e in enumerate(res):
                if not isinstance(e, (dict, vim.Dictionary)):
                    res[i] = {'word': e}
                res[i]['offset'] = codepoint
            return res
        except (vim.error, ValueError, KeyboardInterrupt):
            return []
        finally:
            self.cursor = cursor
