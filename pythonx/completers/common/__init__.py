# -*- coding: utf-8 -*-

import os

from ._common import Common
from ._filename import Filename
from .buffer import Buffer  # noqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass

from .utils import subseq_binary


if os.path.exists(subseq_binary()):
    Filename.sync = False
    Filename.daemon = True

    Common.sync = False
    Common.daemon = True
