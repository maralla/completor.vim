# -*- coding: utf-8 -*-

import re
import os
import logging
import functools
from completor import Completor, vim
from completor.compat import to_bytes

path = os.path.dirname(__file__)

word_patten = re.compile(r'\w+$')
trigger = re.compile(r'(\.|->|#|::)\s*(\w*)$')
logger = logging.getLogger('completor')
ast_pat = re.compile(
    br'.*?'
    br'<(.*?):(\d+):(\d+), (?:col|line):\d+(?::\d+)?>'
    br' (line|col):(\d+)(?::(\d+))? (.*)')
tag_pattern = re.compile(br'\s\((InBase|Hidden|Inaccessible|,)+\)')

VIM_FILES = ['placeholder.vim']


def _inject_vim_files():
    for f in VIM_FILES:
        filename = os.path.join(path, f)
        vim.command('source {}'.format(filename))


def _utf8(b):
    return b.decode('utf-8')


def sanitize(menu):
    if not menu:
        return menu

    # type
    menu = menu.replace(b'[#', b'').replace(b'#]', b' ')
    # argument
    menu = menu.replace(b'<#', b'').replace(b'#>', b'')
    # optional
    menu = menu.replace(b'{#', b'').replace(b'#}', b'')
    return menu


def strip_optional(menu):
    return re.sub(br'{#.*#}|\[#.*#\]', b'', menu)


def strip_tag(word):
    return tag_pattern.sub(b'', word)


def get_word(text):
    parts = re.split(br'[ (\[{<]', text, 1)
    if not parts:
        return text
    return parts[0]


def get_token_path(line, column, word):
    prefix = line[:column]
    item = re.sub(r'[^\w\0]+', ' ', prefix.replace('::', '\0')).replace(
        '\0', '::').strip().split(' ')[-1]
    parts = item.split('::')
    parts[-1] = word
    return '::'.join(parts)


def group(data, condition):
    it = iter(data)
    g = []
    while True:
        try:
            d = next(it)
        except StopIteration:
            break
        if condition(d.decode('utf-8')):
            if g:
                yield g
            g = []
        else:
            g.append(d)
    if g:
        yield g


def is_group(word, heading):
    if not heading.startswith('Dumping'):
        return
    heading = heading[8:].rstrip(':')
    logger.info('%r', [word, heading])
    return heading.endswith(word)


def parse_ast_dump(data, word, line, column):
    """
    :param data: List<bytes>
    :param word: text
    :param line: text
    :param column: int
    """
    ret = {b'line': [], b'col': []}
    path = get_token_path(line, column, word)
    logger.info('heading: %r', [line, column, word, path])
    for item in group(data, functools.partial(is_group, path)):
        if not item:
            continue
        match = ast_pat.match(item[0])
        if not match:
            continue
        logger.info('%r', item)
        fname, line, col, tp, ext1, ext2, text = match.groups()
        if tp == b'line':
            line = ext1
            col = ext2
        elif tp == b'col':
            col = ext1
        ret[tp].append({
            'filename': _utf8(fname),
            'lnum': int(_utf8(line)),
            'col': int(_utf8(col)),
            'name': word,
            'text': _utf8(text)
        })
    return ret[b'line'] or ret[b'col']


class Clang(Completor):
    filetype = 'cpp'

    args_file = ['.clang_complete', '.clang']

    def __init__(self, *args, **kwargs):
        Completor.__init__(self, *args, **kwargs)
        _inject_vim_files()
        self.disable_placeholders = self.get_option(
            'clang_disable_placeholders'
        ) or 1

    def _gen_args(self):
        binary = self.get_option('clang_binary') or 'clang'
        args = [
            binary,
            '-fsyntax-only',
            '-I',
            self.current_directory
        ]
        args.extend(self.parse_config(self.args_file))
        return args

    def _gen_complete_args(self):
        row, _ = self.cursor
        col = len(self.input_data)
        tempfile = self.tempname

        match = trigger.search(self.input_data)
        if match:
            start, _ = match.span()
            sign, _ = match.groups()
            col = start + (2 if sign in ('->', '::') else 1)
        elif not word_patten.search(self.input_data):
            return []

        args = self._gen_args()
        complatfile = tempfile
        if os.getenv('MSYSTEM') is not None:
            cmd = 'cygpath -a -w {}'.format(complatfile)
            complatfile = os.popen(cmd).read()
            complatfile = complatfile.strip().replace('\\', '\\\\')
        args.extend([
            '-Xclang',
            '-code-completion-macros',
            '-Xclang',
            '-code-completion-at={}:{}:{}'.format(complatfile, row, col + 1),
            tempfile
        ])
        return args

    def _gen_definition_args(self):
        args = self._gen_args()
        args.extend([
            '-Xclang',
            '-ast-dump',
            '-Xclang',
            '-ast-dump-filter',
            '-Xclang',
            self.cursor_word,
            self.filename
        ])
        return args

    def get_cmd_info(self, action):
        if action == b'complete':
            args = self._gen_complete_args()
        elif action == b'definition':
            args = self._gen_definition_args()
        else:
            return vim.Dictionary()

        return vim.Dictionary(
            cmd=args,
            is_daemon=False,
            ftype=self.filetype,
            is_sync=False)

    def on_complete(self, items):
        """
        :param items: List<bytes>
        """
        match = trigger.search(self.input_data)
        if match:
            _, prefix = match.groups()
        else:
            match = word_patten.search(self.input_data)
            if not match:
                return []
            prefix = match.group()
        prefix = to_bytes(prefix)

        res = []
        for item in items:
            logger.info(item)
            if not item.startswith(b'COMPLETION:'):
                continue

            parts = [e.strip() for e in item.split(b':')]
            if len(parts) < 2:
                continue

            data = {'word': parts[1], 'dup': 1, 'menu': b''}
            if parts[1] == b'Pattern':
                data['word'] = get_word(parts[2])
                data['menu'] = parts[2]
            else:
                data['menu'] = b':'.join(parts[2:])
            func_sig = sanitize(data['menu'])
            data['abbr'] = data['word']
            if self.disable_placeholders != 1 and data['menu']:
                data['word'] = strip_optional(data['menu'])
            else:
                data['word'] = strip_tag(data['word'])
            data['menu'] = func_sig

            # Show function signature in the preview window
            # data['info'] = func_sig

            if data['word'].startswith(prefix):
                res.append(data)
        return res

    def on_definition(self, items):
        word = self.cursor_word
        line = self.cursor_line
        if not (line and word):
            return []
        column = len(self.input_data)
        try:
            return parse_ast_dump(items, word, line, column)
        except Exception as e:
            logger.exception(e)
        return []
