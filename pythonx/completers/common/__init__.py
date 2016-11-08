# -*- coding: utf-8 -*-

import os

from .filename import Filename  # noqa
from .buffer import Buffer  # noqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass

from .utils import subseq_binary


if os.path.exists(subseq_binary()):
    from .acce_common import Common  # noqa
    Filename.sync = False
    Filename.daemon = True
else:
    from .sync_common import Common  # noqa
