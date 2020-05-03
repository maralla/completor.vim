import functools
import logging

from . import load_completer, load as _load, vim, set_current_completer, \
    get_current_completer

logger = logging.getLogger('completor')


def _api(func):
    @functools.wraps(func)
    def wrapper():
        try:
            return func(vim.bindeval('a:'))
        except Exception as e:
            logger.exception(e)
            raise
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
def gen_request(args):
    c = get_current_completer()
    return c.gen_request(args['action'], args['args']) if c else ''


@_api
def is_message_end(args):
    c = get_current_completer()
    return c.is_message_end(args['msg']) if c else False


@_api
def reset(args):
    c = get_current_completer()
    if not c:
        return
    c.reset()


@_api
def on_stream(args):
    c = get_current_completer()
    if not c:
        return
    name = args['name'].decode()
    parts = name.split(':', 1)
    if parts:
        name = parts[0]
    c.handle_stream(name, args['action'], args['msg'])


@_api
def on_exit(args):
    c = get_current_completer()
    if not c:
        return
    c.on_exit()
