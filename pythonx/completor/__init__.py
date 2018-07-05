# -*- coding: utf-8 -*-

import importlib
import json
import os
import re
import shlex
import threading
import logging
from os.path import expanduser

from ._vim import vim_obj as vim
from .compat import integer_types, to_bytes, to_unicode
from ._log import config_logging

# Cache for command arguments.
_arg_cache = {}

_ctx = threading.local()


class LogFilter(object):
    def filter(self, record):
        return bool(Completor.get_option('debug'))


config_logging('completor.LogFilter')
logger = logging.getLogger('completor')


def get_encoding():
    return to_unicode(vim.current.buffer.options['fileencoding'] or
                      vim.options['encoding'] or 'utf-8', 'utf-8')


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
    # Type alias collector.
    type_map = {
        b'c': 'cpp',
        b'javascript.jsx': 'javascript',
        b'python.django': 'python',
        b'typescript.tsx': 'typescript',
        b'typescript.jsx': 'typescript',
    }

    def __new__(mcls, name, bases, attrs):
        cls = type.__new__(mcls, name, bases, attrs)
        if name not in ('Completor', 'Base'):
            mcls.registry[to_unicode(cls.filetype, 'utf-8')] = cls()
        return cls


Base = Meta('Base', (object,), {})


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

    def __init__(self):
        self.input_data = ''
        self.ft = ''

    @property
    def current_directory(self):
        """Return the directory of the file in current buffer

        :rtype: unicode
        """
        return to_unicode(vim.Function('expand')('%:p:h'), 'utf-8')

    @property
    def tempname(self):
        """Write buffer content to a temp file and return the file name

        :rtype: unicode
        """
        return to_unicode(vim.Function('completor#utils#tempname')(), 'utf-8')

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
            return to_unicode(vim.Function('expand')('<cword>'),
                              get_encoding())
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
        types = self.get_option('disable_{}'.format(self.filetype))
        if isinstance(types, integer_types):
            return bool(types)
        if isinstance(types, (list, vim.List)):
            return to_bytes(self.ft) in types
        return False

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
                is_sync=self.sync
            )
        return vim.Dictionary()

    def do_complete(self, data):
        ret = []
        if callable(getattr(self, 'parse', None)):
            ret.extend(self.parse(data))
        else:
            ret.extend(self.on_complete(data))

        common = get('common')
        if not common.is_common(self):
            if not ret:
                set_current_completer(common)
            if not ret or self.ident == common.ident:
                common.ft = self.ft
                common.input_data = self.input_data
                ret.extend(common.parse(self.input_data))
        return ret

    def on_data(self, action, data):
        """Callback when received data.

        :param action: action bind to this data (bytes)
        :param data: data to process (bytes, list)
        :rtype: list
        """
        action = action.decode('ascii')
        if not isinstance(data, (list, vim.List)):
            data = _unicode(data)
        if action == 'complete':
            return self.do_complete(data)
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

        index = len(self.input_data)
        for i in range(index):
            text = self.input_data[i:]
            matched = pat.match(text)
            if matched and matched.end() == len(text):
                return len(to_bytes(self.input_data[:i], get_encoding()))
        return index

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
        return vim.Function('completor#utils#in_comment_or_string')()


def _resolve_ft(ft):
    """
    :param ft: file type (bytes)
    """
    m = Completor.get_option('filetype_map') or {}
    return to_unicode(m.get(ft, Meta.type_map.get(ft, ft)), 'utf-8')


# ft: unicode
def _load(ft):
    if not ft:
        return
    if ft not in Meta.registry:
        try:
            importlib.import_module("completers.{}".format(ft))
        except ImportError:
            try:
                importlib.import_module("completor_{}".format(ft))
            except ImportError:
                return
    return Meta.registry.get(ft)


def load(ft, input_data=b''):
    """Load a completer of the given file type.

    :param ft: file type (bytes)
    :param input_data: input data (bytes)
    """
    input_data = _unicode(input_data)
    ft = _resolve_ft(ft)
    c = _load(ft)
    if c:
        c.input_data = input_data
        c.ft = ft
    return c


# ft: bytes, input_data: bytes
def load_completer(ft, input_data):
    input_data = _unicode(input_data)
    if not input_data.strip():
        return
    ft = _resolve_ft(ft)

    if 'common' not in Meta.registry:
        import completers.common  # noqa

    filename = get('filename')
    if filename.match(input_data) and not filename.disabled:
        c = filename
    elif not ft:
        c = get('common')
    else:
        c = None
        # omni has the highest priority
        omni = get('omni')
        if omni.has_omnifunc(ft):
            c = omni
        if c is None:
            c = _load(ft)
        if c is None or not c.match(input_data) or c.disabled:
            c = get('common')
    c.input_data = input_data
    c.ft = ft
    return None if c.disabled else c


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
