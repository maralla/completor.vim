# -*- coding: utf-8 -*-

from completor import Completor
from UltiSnips import UltiSnips_Manager


class Ultisnips(Completor):
    filetype = 'ultisnips'
    sync = True

    def parse(self, base):
        token = self.input_data.split()[-1]
        try:
            snips = UltiSnips_Manager._snips(token, True)
        except Exception:
            return []
        candidates = [{
            'word': snip.trigger,
            'dup': 1,
            'menu': ' '.join(['[snip]', snip.description]),
        } for snip in snips]

        index = token.rfind(base)
        if index > 0 and candidates:
            prefix = len(token[:index])
            for c in candidates:
                c['abbr'] = c['word']
                c['word'] = c['word'][prefix:]
        return candidates
