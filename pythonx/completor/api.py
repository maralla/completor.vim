import threading
import functools
import vim

from . import load_completer, get, load as _load

ctx = threading.local()
ctx.current_completer = None


def _api(func):
    @functools.wraps(func)
    def wrapper():
        return func(vim.bindeval('a:'))
    return wrapper


@_api
def get_completer(args):
    c = load_completer(args['ft'], args['inputted'])
    ctx.current_completer = c
    return c.get_cmd_info(b'complete') if c else vim.Dictionary()


@_api
def load(args):
    c = _load(args['ft'], args['inputted'])
    ctx.current_completer = c
    return c.get_cmd_info(args['action']) if c else vim.Dictionary()


@_api
def on_data(args):
    c = ctx.current_completer
    return c.on_data(args['action'], args['msg']) if c else []


@_api
def get_start_column(args):
    c = ctx.current_completer
    return c.start_column() if c else -1


@_api
def prepare_request(args):
    c = ctx.current_completer
    return c.prepare_request(args['action']) if c else ''


@_api
def is_message_end(args):
    c = ctx.current_completer
    return c.is_message_end(args['msg']) if c else False


@_api
def fallback_to_common(args):
    c = ctx.current_completer
    if c and c.filetype != 'common':
        c = get('common', c.ft, c.input_data)
        ctx.current_completer = c
        return c.get_cmd_info(b'complete')
