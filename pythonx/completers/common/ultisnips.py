# -*- coding: utf-8 -*-

from completor import Completor
from UltiSnips import UltiSnips_Manager


class Ultisnips(Completor):
    filetype = 'ultisnips'
    sync = True

    def parse(self, base):
        try:
            snips = UltiSnips_Manager._snips(base, True)
        except Exception:
            return []

        return [{
            'word': snip.trigger,
            'menu': ' '.join(['[snip]', snip.description]),
        } for snip in snips]
