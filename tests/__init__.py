# -*- coding: utf-8 -*-

import mock
import sys
import types


class UltiSnips(object):
    def _snips(self, base, other):
        if base != 'urt':
            return []

        return [mock.Mock(
            trigger='ultisnips_trigger', description='mock snips')]

sys.path.append('./pythonx')
sys.modules['vim'] = types.ModuleType('vim')
sys.modules['UltiSnips'] = mock.Mock(UltiSnips_Manager=UltiSnips())
