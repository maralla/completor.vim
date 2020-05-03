# -*- coding: utf-8 -*-

import uuid
import json

JSONRPC_VERSION = '2.0'

# Workflow: initilize -> initialized -> open -> completion


class Base(object):
    method = ''
    # Is this request a notification?
    notify = False

    def to_dict(self):
        return

    def gen_request(self, params=None):
        req = {
            'jsonrpc': JSONRPC_VERSION,
            'method': self.method,
        }
        if params is not None:
            req['params'] = params
        if not self.notify:
            req['id'] = uuid.uuid4().hex[:16]
        return req

    def to_request(self):
        req = self.gen_request(params=self.to_dict())
        req_id = req.get('id')
        data = json.dumps(req)
        items = ['Content-Length: {}'.format(len(data)), '', data]
        return req_id, '\r\n'.join(items)


class Initialize(Base):
    method = 'initialize'

    def __init__(self, ppid, workspace):
        self.ppid = ppid
        self.workspace = workspace

    def to_dict(self):
        return {
            'processId': self.ppid,
            'capabilities': {
                'workspace': {},
                'textDocument': {}
            },
            'rootUri': self.workspace[0]['uri'],
            # 'workspaceFolders': self.workspace,
        }


class Initialized(Base):
    method = 'initialized'
    notify = True

    def to_dict(self):
        return {}


class DidOpen(Base):
    method = 'textDocument/didOpen'
    notify = True

    def __init__(self, uri, language_id, version, text):
        self.uri = uri
        self.language_id = language_id
        self.version = version
        self.text = text

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri,
                'languageId': self.language_id,
                'version': self.version,
                'text': self.text
            }
        }


class DidSave(Base):
    method = 'textDocument/didSave'
    notify = True

    def __init__(self, uri, version, text):
        self.uri = uri
        self.version = version
        self.text = text

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri,
                'version': self.version
            },
            'text': self.text
        }


class DidChange(Base):
    method = 'textDocument/didChange'
    notify = True

    def __init__(self, uri, version, text):
        self.uri = uri
        self.version = version
        self.text = text

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri,
                'version': self.version
            },
            'contentChanges': [
                {
                    'text': self.text
                }
            ]
        }


class Completion(Base):
    method = 'textDocument/completion'

    def __init__(self, uri, line, offset):
        self.uri = uri
        self.line = line
        self.offset = offset

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri,
            },
            'position': {
                'line': self.line,
                'character': self.offset
            }
        }


class Definition(Completion):
    method = 'textDocument/definition'


class Format(Base):
    method = 'textDocument/formatting'

    def __init__(self, uri):
        self.uri = uri

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri
            }
        }


class Rename(Completion):
    method = 'textDocument/rename'

    def __init__(self, *args, **kwargs):
        Completion.__init__(self, *args, **kwargs)
        self.name = ''

    def set_name(self, name):
        self.name = name

    def to_dict(self):
        ret = Completion.to_dict(self)
        ret['newName'] = self.name
        return ret


class Signature(Completion):
    method = "textDocument/signatureHelp"


class Hover(Completion):
    method = "textDocument/hover"


class Implementation(Completion):
    method = "textDocument/implementation"
