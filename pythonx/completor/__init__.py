# -*- coding: utf-8 -*-

import importlib
import json
import logging
import os
import re
import shlex
import threading
from os.path import expanduser

from ._vim import vim_obj as vim
from ._vim import vim_expand, vim_tempname, vim_support_popup, \
    vim_action_trigger, vim_in_comment_or_string, vim_daemon_send
from ._vim import vim_exists  # noqa
from .compat import integer_types, to_bytes, to_unicode
from ._log import config_logging

LIMIT = 50
COMMON_LIMIT = 10

# Cache for command arguments.
_arg_cache = {}

_ctx = threading.local()


class LogFilter(object):
    def filter(self, record):
        return bool(Completor.get_option('debug'))


config_logging('completor.LogFilter')
logger = logging.getLogger('completor')


def get_encoding():
    return to_unicode(
        vim.current.buffer.options['fileencoding'] or vim.options['encoding']
        or 'utf-8', 'utf-8')


def _unicode(text):
    encoding = get_encoding()
    try:
        return to_unicode(text, encoding)
    except Exception:
        return text


def _read_args(path):
    try:
        with open(path) as f:
            args = shlex.split(f.read(), comments=True, posix=True)
        return [os.path.expandvars(a) for a in args]
    except Exception:
        return []


class Meta(type):
    # Completor registry.
    registry = {}

    def __new__(mcls, name, bases, attrs):
        cls = type.__new__(mcls, name, bases, attrs)
        if name not in ('Completor', 'Base'):
            mcls.registry[to_unicode(cls.filetype, 'utf-8')] = cls()
        return cls


Base = Meta('Base', (object, ), {})


class Unusable(object):
    def __get__(self, inst, owner):
        raise RuntimeError('unusable')


class Completor(Base):
    filetype = Unusable()

    daemon = False
    sync = False
    trigger = None
    ident = re.compile(r'\w+', re.U)

    # Extra data come from vim.
    meta = None

    # Flag used to indicate that the completer is exited.
    _exited = False

    def __init__(self):
        self.input_data = ''
        self.ft = ''
        self.ft_orig = ''
        self.ft_args = {}
        self.stream_buf = []

    def copy_to(self, comp):
        comp.ft = self.ft
        comp.ft_orig = self.ft_orig
        comp.ft_args = self.ft_args
        comp.input_data = self.input_data

    @property
    def current_directory(self):
        """Return the directory of the file in current buffer

        :rtype: unicode
        """
        return to_unicode(vim_expand('%:p:h'), 'utf-8')

    @property
    def tempname(self):
        """Write buffer content to a temp file and return the file name

        :rtype: unicode
        """
        return to_unicode(vim_tempname(), 'utf-8')

    @property
    def support_popup(self):
        """Test whether the popup window is supported

        :rtype: bool
        """
        return vim_support_popup() == 1

    @property
    def filename(self):
        """Get the file name of current buffer

        :rtype: unicode
        """
        return vim.current.buffer.name

    @property
    def cursor_word(self):
        """Get the word under cursor.

        :rtype: unicode
        """
        try:
            return to_unicode(vim_expand('<cword>'), get_encoding())
        except vim.error:
            pass

    @property
    def cursor_line(self):
        """Get line under the cursor.

        :rtype: unicode
        """
        try:
            line, _ = vim.current.window.cursor
            return to_unicode(vim.current.buffer[line - 1], get_encoding())
        except vim.error:
            pass

    @property
    def cursor(self):
        return vim.current.window.cursor

    @cursor.setter
    def cursor(self, value):
        vim.current.window.cursor = value

    @staticmethod
    def get_option(key):
        option = vim.vars.get('completor_{}'.format(key))
        # expand ~ in binary path
        if option and key.endswith('_binary'):
            option = expanduser(option)
        return option

    @property
    def disabled(self):
        enable_types = self.get_option('enable_{}'.format(self.filetype))
        if isinstance(enable_types, (list, vim.List)):
            return to_bytes(self.ft) not in enable_types
        else:
            disable_types = self.get_option('disable_{}'.format(self.filetype))
            if isinstance(disable_types, integer_types):
                return bool(disable_types)
            if isinstance(disable_types, (list, vim.List)):
                return to_bytes(self.ft) in disable_types
            return False

    @staticmethod
    def daemon_send(data):
        """Send data to the daemon.
        """
        return vim_daemon_send(data)

    # input_data: unicode
    def match(self, input_data):
        if self.trigger is None:
            return True
        if isinstance(self.trigger, str):
            self.trigger = re.compile(self.trigger, re.X | re.U)

        return bool(self.trigger.search(input_data))

    def format_cmd(self):
        return ''

    def get_cmd_info(self, action):
        """Get command information of this completor action.

        :param action: request action (bytes)
        :rtype: vim.Dictionary (cmd, ftype, is_daemon, is_sync)
        """
        if action == b'complete':
            return vim.Dictionary(
                cmd=self.format_cmd(),
                ftype=self.filetype,
                is_daemon=self.daemon,
                is_sync=self.sync)
        return vim.Dictionary()

    def _do_complete(self, data):
        ret = []
        if callable(getattr(self, 'parse', None)):
            ret.extend(self.parse(data))
        else:
            ret.extend(self.on_complete(data))

        if ret and not isinstance(ret[0], (dict, vim.Dictionary)):
            offset = self.start_column()
            for i, e in enumerate(ret):
                ret[i] = {'word': e, 'offset': offset}

        common = get('common')
        if not common.is_common(self):
            if ret and 'offset' not in ret[0]:
                offset = self.start_column()
                for item in ret:
                    item['offset'] = offset
            if len(ret) < LIMIT/2:
                self.copy_to(common)
                ret.extend(common.parse(self.input_data)[:COMMON_LIMIT])
        if not self.support_popup and ret:
            offset = ret[0]['offset']
            for i, item in enumerate(ret):
                if item['offset'] != offset:
                    ret = ret[:i]
                    break
        return ret

    def on_stream(self, action, msg):
        """Called when channel message reached.

        :param action: the action which triggered the stream (bytes)
        :param msg: the message received from the stream (bytes)
        """
        for line in msg.split(b'\n'):
            if not line:
                continue
            self.stream_buf.append(line)
            if self.is_message_end(line):
                data = self.stream_buf
                self.stream_buf = []
                return self.on_data(action, data)

    def handle_stream(self, name, action, msg):
        """Wrapper around on_stream.

        When `on_stream` returns non-empty action trigger is called.
        """
        c = get_current_completer()
        logger.info("%s %s", c.filetype, name)
        if c and c.filetype != name:
            self.stream_buf = []
            return
        res = self.on_stream(action, msg)
        if res is None:
            return
        try:
            vim_action_trigger(res)
        except vim.error as e:
            logger.exception(e)

    def on_data(self, action, data):
        """Callback when received data.

        :param action: action bind to this data (bytes)
        :param data: data is a complete action item (bytes, list)
        :rtype: list
        """
        action = action.decode('ascii')
        if not isinstance(data, (list, vim.List)):
            data = _unicode(data)
        if action == 'complete':
            return self._do_complete(data)
        try:
            return getattr(self, 'on_' + action)(data)
        except AttributeError:
            return []

    @staticmethod
    def find_config_file(file):
        cwd = os.getcwd()
        while True:
            path = os.path.join(cwd, file)
            if os.path.exists(path):
                return path
            dirname = os.path.dirname(cwd)
            if dirname == cwd:
                break
            cwd = dirname

    def parse_config(self, files):
        if not isinstance(files, (list, tuple)):
            files = [files]
        for f in files:
            key = '{}-{}'.format(self.filetype, f)
            arg = _arg_cache.get(key)
            if arg:
                return arg
            if arg is not None:
                continue
            path = self.find_config_file(f)
            arg = [] if path is None else _read_args(path)
            _arg_cache[key] = arg
            if arg:
                return arg
        return []

    def ident_match(self, pat):
        if not self.input_data:
            return -1

        data = self.input_data
        index = len(self.input_data)
        for i in range(index):
            text = self.input_data[i:]
            matched = pat.match(text)
            if matched and matched.end() == len(text):
                data = self.input_data[:i]
                break
        return len(to_bytes(data, get_encoding()))

    def start_column(self):
        if not self.ident:
            return -1
        if isinstance(self.ident, str):
            self.ident = re.compile(self.ident, re.U | re.X)
        return self.ident_match(self.ident)

    # Deprecated, use `prepare_request` instead.
    def request(self):
        """Generate daemon complete request arguments
        """
        line, _ = self.cursor
        col = len(self.input_data)
        return json.dumps({
            'line': line - 1,
            'col': col,
            'filename': self.filename,
            'content': '\n'.join(vim.current.buffer[:])
        })

    def prepare_request(self, action=b'complete'):
        """Generate request payload.

        :param action: request action (bytes)
        """
        if action == b'complete':
            return self.request()
        return ''

    def gen_request(self, action=b'complete', args=None):
        """Internal wrapper for preparing a request.
        """
        req = self.prepare_request(action=action)
        if req and req[-1] != '\n':
            req += '\n'
        return req

    def is_message_end(self, msg):
        """Test the end of daemon response

        :param msg: the message received from daemon (bytes)
        """
        return True

    def is_comment_or_string(self):
        """Test current position is in comment or string.

        :returns:
            0   not in comment or string
            1   in comment
            2   in string
            3   in constant
        """
        return vim_in_comment_or_string()

    def reset(self):
        """Reset completer status.

        This method is called after daemonized completer command spawned.
        """

    def on_exit(self):
        """Handle the completer daemon exit event.
        """
        self._exited = True


def _resolve_ft(ft):
    """
    :param ft: file type (bytes)
    """
    m = Completor.get_option('filetype_map') or {}
    return to_unicode(m.get(ft, Meta.type_map.get(ft, ft)), 'utf-8')


def import_completer(ft):
    try:
        importlib.import_module("completers.{}".format(ft))
    except ImportError:
        try:
            importlib.import_module("completor_{}".format(ft))
        except ImportError:
            return


class _ft_context(object):
    def __init__(self, ft, input_data):
        self.c = None
        self.origin = ft
        self.input_data = _unicode(input_data)
        self._mapped = None
        self._ft_args = {}

    @staticmethod
    def _text(ft):
        return to_unicode(ft, 'utf-8')

    def __enter__(self):
        if self.origin:
            m = Completor.get_option('filetype_map') or {}
            info = m.get(self.origin, self.origin)
        else:
            info = b''
        ft = info
        if isinstance(info, (vim.Dictionary, dict)):
            ft = info.get(b'ft', self.origin)
            self._ft_args.update(info)
        self.mapped = self._text(ft)
        return self

    def __exit__(self, et, ev, tb):
        if self.c is None:
            return
        self.c.ft = self.mapped
        self.c.input_data = self.input_data
        self.c.ft_orig = self._text(self.origin)
        self.c.ft_args = self._ft_args


# ft: unicode
def _load(ft):
    if not ft:
        return
    if ft not in Meta.registry:
        import_completer(ft)
    return Meta.registry.get(ft)


def load(ft, input_data=b''):
    """Load a completer of the given file type.

    :param ft: file type (bytes)
    :param input_data: input data (bytes)
    """
    with _ft_context(ft, input_data) as f:
        f.c = _load(f.mapped)
    return f.c


# ft: bytes, input_data: bytes
def load_completer(ft, input_data):
    if 'common' not in Meta.registry:
        import completers.common  # noqa
    neoinclude = get('neoinclude')

    with _ft_context(ft, input_data) as f:
        if neoinclude.has_neoinclude() and neoinclude.match(f.input_data) \
                and not neoinclude.disabled:
            f.c = neoinclude
        elif not f.origin:
            f.c = get('common')
        else:
            # omni has the highest priority
            omni = get('omni')
            if omni.has_omnifunc(f.mapped):
                f.c = omni
            if f.c is None:
                f.c = _load(f.mapped)
            if f.c is None or f.c._exited or not f.c.match(f.input_data) \
                    or f.c.disabled:
                f.c = get('common')
    return None if f.c.disabled else f.c


# filetype: str, ft: bytes, input_data: bytes
def get(filetype, ft=None, input_data=None):
    completer = Meta.registry.get(filetype)
    if completer:
        if ft is not None:
            completer.ft = _unicode(ft)
        if input_data is not None:
            completer.input_data = _unicode(input_data)
    return completer


def set_current_completer(comp):
    _ctx.current_completer = comp


# Set current completer to None
set_current_completer(None)


def get_current_completer():
    return _ctx.current_completer
