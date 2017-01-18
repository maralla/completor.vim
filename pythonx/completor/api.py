import threading
import functools
import vim

from . import load_completer, get

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
    return [c.format_cmd(), c.filetype, c.daemon, c.sync] if c else []


@_api
def get_completions(args):
    c = ctx.current_completer
    res, ft, ty = ((c.get_completions(args['msg']), c.ft, c.filetype)
                   if c else ([], args['ft'], ''))
    if not res and ty != 'common':
        c = get('common', ft, args['inputted'])
        ctx.current_completer = c
        res = c.get_completions(args['inputted'])
    return res


@_api
def get_start_column(args):
    c = ctx.current_completer
    return c.start_column() if c else -1


@_api
def get_daemon_request(args):
    c = ctx.current_completer
    return c.request() if c else ''


@_api
def is_message_end(args):
    c = ctx.current_completer
    return c.is_message_end(args['msg']) if c else False
