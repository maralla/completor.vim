# -*- coding: utf-8 -*-

# Completion using ALE.

import logging
from completor import Completor, vim, vim_exists


logger = logging.getLogger("completor")


def _gen_ale_completions(input_data):
    if not vim_exists('g:loaded_ale'):
        return []

    s = vim.Function("ale#completion#GetCompletionPositionForDeoplete")(input_data)  # noqa

    add_offset = 'completor#utils#add_offset(cs, {})'.format(s)
    args = "{'callback': {cs -> completor#action#trigger(" + add_offset + ")}}"
    cmd = ":call ale#completion#GetCompletions('ale-callback', " + args + ")"

    vim.command(cmd)


class ALE(Completor):
    filetype = 'ale'
    sync = True
    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*|->\w*)$'

    def parse(self, base):
        try:
            _gen_ale_completions(self.input_data)
        except vim.error:
            pass
        return []
