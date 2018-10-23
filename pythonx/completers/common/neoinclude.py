# -*- coding: utf-8 -*-

import logging, re
from completor import Completor, vim, get_encoding
from completor.compat import to_bytes

logger = logging.getLogger('completor')


class Neoinclude(Completor):
    filetype = 'neoinclude'
    trigger_cache = {
        b'java'     : r'^\s*import', 
        b'haskell'  : r'^\s*import', 
        b'c'        : r'^\s*\#\s*include', 
        b'cpp'      : r'^\s*\#\s*include', 
        b'cs'       : r'^\s*using', 
        b'ruby'     : r'^\s*(load|require|require_relative)', 
        b'r'        : r'^\s*source(', 
        b'html'     : r'(src|href)="(?=[^"]*)$', 
        b'xhtml'    : r'(src|href)="(?=[^"]*)$', 
        b'markdown' : r'(src|href)="(?=[^"]*)$', 
        b'mkd'      : r'(src|href)="(?=[^"]*)$', 
    }
    sync = True

    @property
    def trigger(self):
        ft = vim.current.buffer.options['filetype']
        return self.trigger_cache.get(ft)

    @trigger.setter
    def trigger(self, value):
        ft = vim.current.buffer.options['filetype']
        self.trigger_cache[ft] = value

    def has_neoinclude(self):
        if vim.vars.get('loaded_neoinclude'):
            return True
        return False

    # input_data: unicode
    def match(self, input_data):
        ft = vim.current.buffer.options['filetype']
        trigger = self.trigger_cache.get(ft)
        if not trigger:
            return False
        if isinstance(trigger, str):
            trigger = re.compile(trigger, re.X | re.U)
            self.trigger_cache[ft] = trigger

        return bool(trigger.search(input_data))

    def parse(self, base):
        if not self.ft or not base:
            return []
        logger.info('start neoinclude parse: %s', base)

        input_data = to_bytes(self.input_data, get_encoding())
        get_complete_position = vim.Function(
            'neoinclude#file_include#get_complete_position')
        start_column = get_complete_position(input_data)
        if start_column == -1:
            return []

        get_include_files = vim.Function(
            'neoinclude#file_include#get_include_files')

        try:
            candidates = [{
                'word': item[b'word'],
                'dup': 1,
                'menu': b'[include]',
                'kind': item[b'kind']
            } for item in get_include_files(input_data)[:]]
        except TypeError as e:
            logger.exception(e)
            candidates = []
        logger.info(candidates)

        return candidates
