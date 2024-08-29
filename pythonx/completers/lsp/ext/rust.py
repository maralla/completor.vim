# -*- coding: utf-8 -*-

from completor import vim
from ..models import Completion


def get_action_handler(action):
    if action == b'view_hir':
        return ViewHir
    if action == b'view_mir':
        return ViewMir
    if action == b'expand_macro':
        return ExpandMacro

    return ''


def on_data(action, data):
    if action == b'expand_macro':
        try:
            data = [data[0]['expansion']]
        except Exception:
            return []
    return vim.Dictionary(data=data, action='view', ft='rust')


class ViewHir(Completion):
    method = 'rust-analyzer/viewHir'


class ViewMir(Completion):
    method = 'rust-analyzer/viewMir'


class ExpandMacro(Completion):
    method = 'rust-analyzer/expandMacro'
