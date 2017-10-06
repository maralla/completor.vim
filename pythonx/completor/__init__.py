# -*- coding: utf-8 -*-

import importlib
import json
import os
import re
import vim

from .patch import patch_nvim
if hasattr(vim, 'from_nvim'):
    patch_nvim(vim)

from .compat import integer_types, to_bytes, to_unicode  # noqa
from ._log import config_logging  # noqa


class LogFilter(object):
    def filter(self, record):
        return bool(Completor.get_option('debug'))


config_logging('completor.LogFilter')


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
            return [l.strip() for l in f.readlines()]
    except Exception:
        return []


class Meta(type):
    def __init__(cls, name, bases, attrs):
        if name not in ('Completor', 'Base'):
            Completor._registry[to_unicode(cls.filetype, 'utf-8')] = cls()

        return super(Meta, cls).__init__(name, bases, attrs)


Base = Meta('Base', (object,), {})


class Unusable(object):
    def __get__(self, inst, owner):
        raise RuntimeError('unusable')


class Completor(Base):
    _registry = {}

    filetype = Unusable()

    daemon = False
    sync = False
    trigger = None
    ident = re.compile(r'\w+', re.U)

    _type_map = {
        b'c': b'cpp',
        b'javascript.jsx': b'javascript'
    }

    _arg_cache = {}

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
    def cursor(self):
        line, _ = vim.current.window.cursor
        return line, len(self.input_data)

    @cursor.setter
    def cursor(self, value):
        vim.current.window.cursor = value

    # use cached property
    @property
    def filetype_map(self):
        m = self.get_option('filetype_map') or {}
        self._type_map.update(m)
        return self._type_map

    @staticmethod
    def get_option(key):
        return vim.vars.get('completor_{}'.format(key))

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
        filename = get('filename')
        if filename.match(self.input_data) and not filename.disabled:
            ret.extend(filename.parse(self.input_data))

        if callable(getattr(self, 'parse', None)):
            ret.extend(self.parse(data))
        else:
            ret.extend(self.on_complete(data))
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
            if os.path.dirname(cwd) == cwd:
                break
            cwd = os.path.split(cwd)[0]

    def parse_config(self, file):
        key = "{}-{}".format(self.filetype, file)
        if key not in self._arg_cache:
            path = self.find_config_file(file)
            self._arg_cache[key] = [] if path is None else _read_args(path)
        return self._arg_cache[key]

    def ident_match(self, pat):
        if not self.input_data:
            return -1

        _, index = self.cursor
        for i in range(index):
            text = self.input_data[i:index]
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
        line, col = self.cursor
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


_completor = Completor()


# ft: unicode
def _load(ft):
    if ft not in _completor._registry:
        try:
            importlib.import_module("completers.{}".format(ft))
        except ImportError:
            try:
                importlib.import_module("completor_{}".format(ft))
            except ImportError:
                return
    return _completor._registry.get(ft)


def load(ft, input_data=b''):
    """Load a completer of the given file type.

    :param ft: file type (bytes)
    :param input_data: input data (bytes)
    """
    input_data = _unicode(input_data)
    ft = to_unicode(_completor.filetype_map.get(ft, ft), 'utf-8')
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
    ft = to_unicode(_completor.filetype_map.get(ft, ft), 'utf-8')

    if 'common' not in _completor._registry:
        import completers.common  # noqa

    if not ft:
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
    completer = _completor._registry.get(filetype)
    if completer:
        if ft is not None:
            completer.ft = _unicode(ft)
        if input_data is not None:
            completer.input_data = _unicode(input_data)
    return completer
