# -*- coding: utf-8 -*-

import logging
import json
from completor import Completor, vim, get_encoding
from completor.compat import to_unicode, to_bytes
from completor.utils import ignore_exception

logger = logging.getLogger('completor')


class Go(Completor):
    filetype = 'go'
    trigger = r'(?:\w{2,}\w*|\.\w*)$'

    # Use guru for go to definition.
    use_guru_for_def = False

    def get_offset(self):
        line, col = vim.current.window.cursor
        line2byte = vim.Function('line2byte')
        return line2byte(line) + col - 1

    def _gen_archive(self):
        if not vim.current.buffer.options['modified']:
            return ''
        content = '\n'.join(vim.current.buffer[:])
        n = len(to_bytes(content, get_encoding()))
        return '\n'.join([self.filename, str(n), content])

    def _complete_cmd(self):
        binary = self.get_option('gocode_binary') or 'gocode'
        cmd = [binary, '-f=csv',
               'autocomplete', self.filename, self.get_offset()]
        return cmd, '\n'.join(vim.current.buffer[:])

    def _doc_cmd(self):
        binary = self.get_option('gogetdoc_binary') or 'gogetdoc'
        archive = self._gen_archive()
        cmd = [binary, '-json', '-u']
        if archive:
            cmd.append('-modified')
        cmd.extend(['-pos', '{}:#{}'.format(self.filename, self.get_offset())])
        return cmd, archive

    def _def_cmd(self):
        guru = self.get_option('go_guru_binary')
        if not guru:
            return self._doc_cmd()

        self.use_guru_for_def = True
        cmd = [guru, '-json']
        archive = self._gen_archive()
        if archive:
            cmd.append('-modified')
        pos = '{}:#{}'.format(self.filename, self.get_offset())
        cmd.extend(['definition', pos])
        return cmd, archive

    def _format(self):
        gofmt = self.get_option('go_gofmt_binary') or 'gofmt'
        return [gofmt, '-w', self.filename], ''

    def get_cmd_info(self, action):
        if action == b'complete':
            cmd, input_content = self._complete_cmd()
        elif action == b'doc':
            cmd, input_content = self._doc_cmd()
        elif action == b'definition':
            cmd, input_content = self._def_cmd()
        elif action == b'format':
            cmd, input_content = self._format()
        else:
            cmd, input_content = [], ''
        return vim.Dictionary(
            cmd=cmd,
            ftype=self.filetype,
            is_daemon=False,
            is_sync=False,
            input_content=input_content,
        )

    def on_complete(self, items):
        res = []
        for item in items:
            parts = item.split(b',,')
            if len(parts) < 3:
                continue
            res.append({
                'word': parts[1],
                'menu': parts[2],
            })
        return res

    @ignore_exception()
    def on_doc(self, items):
        data = to_unicode(items[0], 'utf-8')
        spec = json.loads(data)
        _import = 'import "{}"'.format(spec['import'])
        doc = '\n\n'.join([_import, spec['decl'], spec['doc']])
        return [doc]

    @ignore_exception()
    def on_definition(self, items):
        data = to_unicode(b''.join(items), 'utf-8')
        spec = json.loads(data)
        if self.use_guru_for_def:
            pos = spec['objpos']
            name = spec['desc']
        else:
            pos = spec['pos']
            name = spec['name']
        if ' ' in name:
            name = self.cursor_word
        path, lnum, col = pos.rsplit(':', 2)
        return [{
            'filename': path,
            'lnum': lnum,
            'col': col,
            'name': name
        }]
