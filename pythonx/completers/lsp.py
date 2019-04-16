# -*- coding: utf-8 -*-

# Completion with language server protocol.

import logging
import os
import json
import re
from io import BytesIO
from completor import Completor, vim, lsp
from completor.lsp.models import Initialize, DidOpen, Completion, DidChange

logger = logging.getLogger('completor')

word_pat = re.compile('([\d\w]+)', re.U)


class Lsp(Completor):
    filetype = 'lsp'

    def __init__(self, *args, **kwargs):
        Completor.__init__(self, *args, **kwargs)
        self.server_cmd = None
        self.initialized = False
        self.current_id = None
        self.open_file_map = {}
        self.buf = BytesIO()

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
            'uri': lsp.gen_uri(project_path),
            'name': project_name
        }])
        _, req = i.to_request()
        logger.info("******** %r", req)
        return req

    @property
    def file_content(self):
        return '\n'.join(vim.current.buffer[:])

    def open_request(self):
        f = lsp.gen_uri(self.filename)
        if f in self.open_file_map:
            return
        o = DidOpen(f, self.ft, 0, self.file_content)
        self.open_file_map[f] = {'version': 0}
        _, req = o.to_request()
        return req

    def change_request(self):
        f = lsp.gen_uri(self.filename)
        c = DidChange(f, self.get_version(f), self.file_content)
        _, req = c.to_request()
        return req

    def completion_request(self):
        line, _ = self.cursor
        offset = len(self.input_data)
        c = Completion(lsp.gen_uri(self.filename), line, offset)
        req_id, req = c.to_request()
        self.current_id = req_id
        return req

    def prepare_request(self, action):
        try:
            pwd = os.getcwd()
            project_name = os.path.basename(pwd)
            logger.info(project_name)
            items = []
            if not self.initialized:
                items.append(self.initialize_request(project_name, pwd))
                self.initialized = True
            req = self.open_request()
            if req:
                items.append(req)
            if action == b'complete':
                items.append(self.change_request())
                items.append(self.completion_request())
            logger.info('data: %r', items)
            return ''.join(items)
        except Exception as e:
            logger.exception(e)
            raise

    def get_cmd_info(self, action):
        try:
            logger.info("********* %s, %s", action, self.server_cmd.split())
            if not self.server_cmd:
                return vim.Dictionary()
            return vim.Dictionary(
                cmd=self.server_cmd.split(),
                is_daemon=True,
                ftype=self.filetype,
                is_sync=False)
        except Exception as e:
            logger.exception(e)
            raise

    def reset(self):
        self.initialized = False
        self.current_id = None
        self.open_file_map = {}
        self.buf = BytesIO()

    def parse_data(self):
        remain = self.buf.getvalue()
        while True:
            parts = remain.split('\r\n\r\n', 1)
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
            yield json.loads(data)
        self.buf = BytesIO(remain)

    def on_complete(self, data):
        if not data:
            return []
        res = []
        if 'items' not in data[0]:
            return []
        for item in data[0]['items']:
            label = item['label']
            match = word_pat.match(label)
            word = match.groups()[0] if match else ''
            d = vim.Dictionary(abbr=label, word=word)
            if 'detail' in item:
                d['menu'] = item['detail']
            res.append(d)
        return vim.List(res)

    def on_stream(self, action, data):
        try:
            logger.info('%s: %s', action, data)
            self.buf.write(data)
            res = []
            for item in self.parse_data():
                if item.get('id') == self.current_id:
                    res.append(item.get('result', {}))
            return self.on_data(action, res)
        except Exception as e:
            logger.exception(e)
            raise


def content_length(header):
    parts = header.split('\r\n')
    for part in parts:
        try:
            name, value = part.split(':')
        except ValueError:
            continue
        if name.strip().lower() != 'content-length':
            continue
        try:
            length = int(value.strip())
        except ValueError:
            length = None
        return length
