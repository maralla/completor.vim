# -*- coding: utf-8 -*-

from completor import Completor


class Ultisnips(Completor):
    filetype = 'ultisnips'
    sync = True

    def parse(self, base):
        from UltiSnips import UltiSnips_Manager
        return [
            {
                'word': snip.trigger,
                'menu': ' '.join(['[snip]', snip.description]),
            } for snip in UltiSnips_Manager._snips(base, True)]
