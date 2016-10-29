# -*- coding: utf-8 -*-

import sys
import pytest


@pytest.fixture
def vim_mod():
    vim = sys.modules['vim']
    yield vim
    vim.reset()
