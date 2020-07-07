import os
import vim


def _bytes(data):
    from completor import get_encoding

    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode(get_encoding())

    if isinstance(data, list):
        for i, e in enumerate(data):
            data[i] = _bytes(e)
    elif isinstance(data, dict):
        for k in list(data.keys()):
            data[_bytes(k)] = _bytes(data.pop(k))
    return data


class _Vim(object):
    def __getattr__(self, attr):
        return getattr(vim, attr)


vim_obj = _Vim()


def _patch_nvim(vim):
    class Bindeval(object):
        def __init__(self, data):
            self.data = data

        def __getitem__(self, key):
            return _bytes(self.data[key])

    def function(name):
        def inner(*args, **kwargs):
            ret = vim.call(name, *args, **kwargs)
            return _bytes(ret)
        return inner

    def bindeval(value):
        data = vim.eval(value)
        return Bindeval(data)

    vim_vars = vim.vars

    class vars_wrapper(object):
        def get(self, *args, **kwargs):
            item = vim_vars.get(*args, **kwargs)
            return _bytes(item)

    vim.Function = function
    vim.bindeval = bindeval
    vim.List = list
    vim.Dictionary = dict
    vim.vars = vars_wrapper()


if hasattr(vim, 'from_nvim'):
    _patch_nvim(vim_obj)


def _cached(f):
    if os.getenv('DISABLE_CACHE'):
        def wrap(*args, **kwargs):
            func = f()
            return func(*args, **kwargs)
    else:
        func = f()

        def wrap(*args, **kwargs):
            return func(*args, **kwargs)

    wrap.__name__ = f.__name__
    wrap.__doc__ = f.__doc__
    wrap.__module__ = f.__module__

    return wrap


@_cached
def vim_expand():
    return vim_obj.Function('expand')


@_cached
def vim_tempname():
    return vim_obj.Function('completor#utils#tempname')


@_cached
def vim_support_popup():
    return vim_obj.Function('completor#support_popup')


@_cached
def vim_action_trigger():
    return vim_obj.Function('completor#action#trigger')


@_cached
def vim_in_comment_or_string():
    return vim_obj.Function('completor#utils#in_comment_or_string')


@_cached
def vim_daemon_send():
    return vim_obj.Function('completor#daemon#send')


@_cached
def vim_exists():
    return vim_obj.Function('exists')
