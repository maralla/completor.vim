# -*- coding: utf-8 -*-

# Completion with language server protocol.

import logging
import os
import json
import io
from completor import Completor, vim, import_completer, get
from completor.compat import to_unicode

from .models import Initialize, DidOpen, Completion, DidChange, DidSave, \
    Definition, Format, Rename, Hover, Initialized, Implementation, \
    References, DidChangeConfiguration, Symbol, Signature, DocumentSymbol, \
    CodeAction
from .action import gen_jump_list, get_completion_word, gen_hover_doc, \
    filter_items, parse_symbols, rename
from .utils import gen_uri

logger = logging.getLogger('completor')


class Lsp(Completor):
    filetype = 'lsp'
    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*|->\w*)$'

    def __init__(self, *args, **kwargs):
        Completor.__init__(self, *args, **kwargs)
        self.server_cmd = None
        self.initialized = False
        self.current_id = None
        self.current_options = None
        self.open_file_map = {}
        self.buf = io.BytesIO()

        self.initialize_id = None
        self._pending = None

    def get_version(self, f):
        args = self.open_file_map.get(f)
        if args is None:
            return 0
        args['version'] += 1
        return args['version']

    def set_server_cmd(self, cmd):
        logger.info(cmd)
        self.server_cmd = cmd

    def initialize_request(self, project_name, project_path):
        pid = os.getpid()
        i = Initialize(pid, [{
            'uri': gen_uri(project_path),
            'name': project_name
        }])
        req_id, req = i.to_request()
        self.initialize_id = req_id
        return req

    def initialized_request(self):
        _, req = Initialized().to_request()
        return req

    @property
    def file_content(self):
        content = '\n'.join(vim.current.buffer[:])
        if content:
            content += '\n'
        return content

    def open_request(self):
        f = gen_uri(self.filename)
        if f in self.open_file_map:
            return
        o = DidOpen(f, self.ft, 0, self.file_content)
        self.open_file_map[f] = {'version': 0}
        _, req = o.to_request()
        return req

    def change_request(self):
        f = gen_uri(self.filename)
        c = DidChange(f, self.get_version(f), self.file_content)
        _, req = c.to_request()
        return req

    def save_request(self):
        f = gen_uri(self.filename)
        c = DidSave(f, self.get_version(f), self.file_content)
        _, req = c.to_request()
        return req

    def gen_position_request(self, category):
        line, _ = self.cursor
        offset = len(self.input_data)
        return category(gen_uri(self.filename), line - 1, offset)

    def gen_symbol_request(self, word=None):
        if word is None:
            word = "'" + self.cursor_word
        req_id, req = Symbol(word).to_request()
        self.current_id = req_id
        return req

    def position_request(self, category):
        c = self.gen_position_request(category)
        req_id, req = c.to_request()
        self.current_id = req_id
        return req

    def text_document_request(self, category):
        f = gen_uri(self.filename)
        c = category(f)
        req_id, req = c.to_request()
        self.current_id = req_id
        return req

    def rename_request(self, name):
        c = self.gen_position_request(Rename)
        c.set_name(to_unicode(name, 'utf-8'))
        req_id, req = c.to_request()
        self.current_id = req_id
        return req

    def code_action(self, action):
        uri = gen_uri(self.filename)
        c = CodeAction(uri, action)
        req_id, req = c.to_request()
        self.current_id = req_id
        return req

    def _gen_action_args(self, action, args):
        if action == b'complete':
            return self.position_request(Completion)

        if action == b'definition':
            return self.position_request(Definition)

        if action == b'signature':
            return self.position_request(Signature)

        if action == b'format':
            return self.text_document_request(Format)

        if action == b'document_symbol':
            return self.text_document_request(DocumentSymbol)

        if action == b'implementation':
            return self.position_request(Implementation)

        if action == b'references':
            return self.position_request(References)

        if action == b'symbol':
            s = None
            if args:
                s = args[0]
            return self.gen_symbol_request(s)

        if action == b'rename':
            if not args:
                return ''
            return self.rename_request(args[0])

        if action == b'code_action':
            if not args:
                return ''
            return self.code_action([args[0]])

        if action == b'hover':
            return self.position_request(Hover)

        return ''

    def gen_request(self, action, args):
        self.current_options = None
        if args:
            last = args[-1]
            if isinstance(last, (dict, vim.Dictionary)):
                self.current_options = last
                args = args[:-1]

        try:
            pwd = os.getcwd()
            project_name = os.path.basename(pwd)
            items = []

            req = self.open_request()
            if req:
                items.append(req)
            items.append(self.change_request())

            action_args = self._gen_action_args(action, args)
            if action_args:
                items.append(action_args)

            if not self.initialized:
                self._pending = ''.join(items)

                items = []
                items.append(self.initialize_request(project_name, pwd))
                self.initialized = True

            logger.info('data: %r', items)
            return ''.join(items)
        except Exception as e:
            logger.exception(e)
            raise

    def get_cmd_info(self, action):
        ft = self.ft_orig
        args = self.ft_args
        lsp_cmd = args.get(b'cmd')
        if not lsp_cmd:
            return vim.Dictionary()
        # if action == b'format' and ft != self.ft:
        #     import_completer(ft)
        #     c = get(ft, ft, self.input_data)
        #     if not c:
        #         return ''
        #     return c.get_cmd_info(action)
        return vim.Dictionary(cmd=lsp_cmd.split(),
                              is_daemon=True,
                              ftype=self.filetype + ':' + ft,
                              is_sync=False)

    def reset(self):
        self.initialized = False
        self.current_id = None
        self.open_file_map = {}
        self.buf = io.BytesIO()

    def parse_data(self):
        remain = self.buf.getvalue()
        while True:
            try:
                parts = remain.split(b'\r\n\r\n', 1)
                if len(parts) != 2:
                    break
                header = parts[0]
                body = parts[1]
                length = content_length(header)
                if length is None:
                    logger.warning('no content-length')
                    break
                if len(body) < length:
                    break
                data = body[:length]
                remain = body[length:]
                logger.info("parsing %r", data)
                try:
                    yield json.loads(to_unicode(data, 'utf-8'))
                except json.JSONDecodeError:
                    break
            except Exception as e:
                logger.exception(e)
                raise
        self.buf = io.BytesIO(remain)
        # Seek to end.
        self.buf.seek(0, 2)

    def on_complete(self, data):
        logger.info("complete %r", data)
        if not data:
            return []
        res = []
        candidates = data[0] or []
        items = []
        if isinstance(candidates, list):
            items = candidates
        elif 'items' in candidates:
            items = candidates['items']

        completions = []

        for item in items:
            label = item['label'].strip()
            word, offset = get_completion_word(
                item, self.ft_args.get(b'insertText'))
            completions.append((label, word, offset, item.get('detail')))

        completions = filter_items(completions, self.input_data)

        for label, word, offset, detail in completions:
            d = vim.Dictionary(abbr=label, word=word, category='lsp')
            if detail:
                d['menu'] = detail
            if offset != -1:
                d['offset'] = offset
            res.append(d)

        return vim.List(res)

    def on_definition(self, data):
        return gen_jump_list(self.cursor_word, data)

    def on_rename(self, data):
        logger.info("rename -> %r", data)
        if data:
            rename(data[0])
        return vim.Dictionary(data=[], action='rename')

    def on_format(self, data):
        logger.info("foramt -> %r", data)
        return vim.Dictionary(data=data, action='format')

    def on_implementation(self, data):
        logger.info("implementation -> %r", data)
        return gen_jump_list(self.cursor_word, data)

    def on_references(self, data):
        logger.info("references -> %r", data)
        return gen_jump_list(self.cursor_word, data)

    def on_symbol(self, data):
        if not data:
            return []
        item = data[0]
        if not item:
            return []
        items = parse_symbols(item)
        return vim.Dictionary(data=items, action="select")

    def on_signature(self, data):
        logger.info("signature -> %r", data)
        return []

    def on_document_symbol(self, data):
        logger.info("document_symbol -> %r", data)
        return []

    def on_code_action(self, data):
        logger.info("code_action -> %r", data)
        if not data:
            return []

        item = data[0]
        if not item:
            return []

        item = item[0]
        if not item or 'edit' not in item:
            return []

        rename(item['edit'])
        return vim.Dictionary(data=[], action='rename')

    def on_hover(self, data):
        logger.info("hover -> %r", data)
        if not data:
            return []
        item = data[0]

        contents = item.get('contents')
        if not contents:
            return []

        values = []

        if isinstance(contents, list):
            for content in contents:
                if isinstance(content, dict):
                    values.append(content.get('value', ''))
                else:
                    values.append(content)
        else:
            values.append(contents.get('value', ''))

        if not values:
            return []

        return [gen_hover_doc(self.ft_orig, '\n\n'.join(values))]

    def on_stream(self, action, data):
        logger.info('received %r', data)
        self.buf.write(data)
        res = []
        for item in self.parse_data():
            req_id = item.get('id')
            if not req_id:
                continue

            if req_id == self.initialize_id:
                if self._pending:
                    p = self._pending
                    self._pending = None
                    logger.info("send pending data -> %r", p)
                    self.daemon_send(self.initialized_request())
                    self.send_config()
                    self.daemon_send(p)

            if req_id == self.current_id:
                res.append(item.get('result', {}))

        if res:
            ret = self.on_data(action, res)
            if not isinstance(ret, (dict, vim.Dictionary)):
                ret = vim.Dictionary(data=ret)

            if self.current_options:
                ret['opt'] = self.current_options

            return ret

    def send_config(self):
        conf = self.ft_args.get(b'config')
        if not conf:
            return

        a = DidChangeConfiguration(conf)
        _, req = a.to_request()
        self.daemon_send(req)


def content_length(header):
    parts = header.split(b'\n')
    for part in parts:
        part = part.strip(b'\r')
        try:
            name, value = part.split(b':')
        except ValueError:
            continue
        if name.strip().lower() != b'content-length':
            continue
        try:
            length = int(value.strip())
        except ValueError:
            length = None
        return length
