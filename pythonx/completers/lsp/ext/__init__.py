# -*- coding: utf-8 -*-

from completor import vim


def get_action_handler(action, ft):
    if ft == 'rust':
        from .rust import get_action_handler
        return get_action_handler(action)

    return ''


def on_data(action, ft, data):
    if not data:
        return []

    if ft == 'rust':
        from .rust import on_data
        return on_data(action, data)

    return vim.Dictionary(data=data, action='view', ft=ft)
