import functools

from . import load_completer, load as _load, vim, set_current_completer, \
    get_current_completer


def _api(func):
    @functools.wraps(func)
    def wrapper():
        return func(vim.bindeval('a:'))
    return wrapper


@_api
def get_completer(args):
    c = load_completer(args['ft'], args['inputted'])
    set_current_completer(c)
    return c.get_cmd_info(b'complete') if c else vim.Dictionary()


@_api
def load(args):
    c = _load(args['ft'], args['inputted'])
    set_current_completer(c)
    if not c:
        return vim.Dictionary()
    try:
        c.meta = args['meta']
        return c.get_cmd_info(args['action'])
    finally:
        c.meta = None


@_api
def on_data(args):
    c = get_current_completer()
    return c.on_data(args['action'], args['msg']) if c else []


@_api
def get_start_column(args):
    c = get_current_completer()
    return c.start_column() if c else -1


@_api
def prepare_request(args):
    c = get_current_completer()
    return c.prepare_request(args['action']) if c else ''


@_api
def is_message_end(args):
    c = get_current_completer()
    return c.is_message_end(args['msg']) if c else False
