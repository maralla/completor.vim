# -*- coding: utf-8 -*-

import logging
import json
import os.path
from completor import Completor, vim
from completor.compat import to_unicode
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

    def _gen_archive(self, fname):
        content = '\n'.join(vim.current.buffer[:])
        return '\n'.join([fname, str(len(content)), content])

    def _complete_cmd(self):
        binary = self.get_option('gocode_binary') or 'gocode'
        cmd = [binary, '-f=csv',
               'autocomplete', self.filename, self.get_offset()]
        return cmd, '\n'.join(vim.current.buffer[:])

    def _doc_cmd(self):
        fname = self.filename
        binary = self.get_option('gogetdoc_binary') or 'gogetdoc'
        cmd = [binary, '-json', '-u']
        if not os.path.exists(fname):
            fname = self.tempname
            archive = ''
        else:
            cmd.append('-modified')
            archive = self._gen_archive(fname)
        cmd.extend(['-pos', '{}:#{}'.format(fname, self.get_offset())])
        return cmd, archive

    def _def_cmd(self):
        guru = self.get_option('go_guru_binary')
        if not guru:
            return self._doc_cmd()
        fname = self.filename
        self.use_guru_for_def = True
        cmd = [guru, '-json', '-modified', 'definition',
               '{}:#{}'.format(fname, self.get_offset())]
        return cmd, self._gen_archive(fname)

    def get_cmd_info(self, action):
        if action == b'complete':
            cmd, input_content = self._complete_cmd()
        elif action == b'doc':
            cmd, input_content = self._doc_cmd()
        elif action == b'definition':
            cmd, input_content = self._def_cmd()
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
        path, lnum, col = pos.rsplit(':', 2)
        return [{
            'filename': path,
            'lnum': lnum,
            'col': col,
            'name': name
        }]
