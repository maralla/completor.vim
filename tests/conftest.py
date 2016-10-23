# -*- coding: utf-8 -*-

import mock
import sys
import pytest


@pytest.fixture
def vim_mod():
    vim = sys.modules['vim']
    attrs = dict(vim.__dict__)
    vim.current = mock.Mock()
    yield vim
    vim.__dict__.clear()
    vim.__dict__.update(attrs)
