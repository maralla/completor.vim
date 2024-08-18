# -*- coding: utf-8 -*-

from ..models import Completion


def get_action_handler(action):
    if action == b'view_hir':
        return ViewHir
    if action == b'view_mir':
        return ViewMir

    return ''


class ViewHir(Completion):
    method = 'rust-analyzer/viewHir'


class ViewMir(Completion):
    method = 'rust-analyzer/viewMir'
