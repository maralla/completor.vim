# -*- coding: utf-8 -*-

import sys
import types

sys.path.append('./pythonx')
sys.modules['vim'] = types.ModuleType('vim')
