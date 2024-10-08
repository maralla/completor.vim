# -*- coding: utf-8 -*-

import uuid
import json
import logging
from completor import vim

JSONRPC_VERSION = '2.0'

logger = logging.getLogger("completor")

# Workflow: initilize -> initialized -> open -> completion


class VimEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, vim.Dictionary):
            return {k.decode('utf-8'): v for k, v in obj.items()}

        if isinstance(obj, vim.List):
            return list(obj)

        if isinstance(obj, bytes):
            return obj.decode('utf-8')

        return json.JSONEncoder.default(self, obj)


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
        data = json.dumps(req, cls=VimEncoder)
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
                'workspace': {
                    'workspaceFolders': True,
                },
                'textDocument': {
                    'hover': {
                        'contentFormat': ['markdown', 'plaintext']
                    },
                    'completion': {
                        'completionItem': {
                            'snippetSupport': False,
                            'commitCharactersSupport': False,
                        }
                    },
                    'codeAction': {
                        'codeActionLiteralSupport': {
                            'codeActionKind': {
                                'valueSet': ['quickfix'],
                            }
                        },
                        'resolveSupport': {
                            'properties': ['edit'],
                        }
                    },
                }
            },
            'rootUri': self.workspace[0]['uri'],
            'workspaceFolders': self.workspace,
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

    def __init__(self, uri, options=None):
        self.uri = uri
        self.options = options or {}

    def to_dict(self):
        return {
            'textDocument': {
                'uri': self.uri
            },
            'options': self.options
        }


class CodeAction(Base):
    method = 'textDocument/codeAction'

    def __init__(self, uri, action=None, text_range=None):
        self.uri = uri
        self.action = action
        self.text_range = text_range

    def to_dict(self):
        r = {
            'textDocument': {
                'uri': self.uri
            },
            'context': {
                'diagnostics': []
            }
        }

        if self.action is not None:
            r['context']['only'] = self.action

        if self.text_range:
            start = self.text_range[b'start']
            end = self.text_range[b'end']
            r['range'] = {
                'start': {'line': start[b'line'], 'character': start[b'col']},
                'end': {'line': end[b'line'], 'character': end[b'col']}
            }

        return r


class CodeResolve(Base):
    method = 'codeAction/resolve'

    def __init__(self, params):
        self.params = params

    def to_dict(self):
        return self.params


class DocumentSymbol(Format):
    method = 'textDocument/documentSymbol'


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


class References(Completion):
    method = "textDocument/references"

    def to_dict(self):
        d = super(References, self).to_dict()
        d['context'] = {
            'includeDeclaration': True
        }

        return d


class DidChangeConfiguration(Base):
    method = "workspace/didChangeConfiguration"
    notify = True

    def __init__(self, conf):
        self.conf = conf

    def to_dict(self):
        return {
            "settings": self.conf
        }


class Symbol(Base):
    method = "workspace/symbol"

    def __init__(self, query=""):
        self.query = query

    def to_dict(self):
        return {
            "query": self.query,
        }


class PrepareCallHierarchy(Completion):
    method = "textDocument/prepareCallHierarchy"


class IncomingCalls(Base):
    method = "callHierarchy/incomingCalls"

    def __init__(self, item):
        self.item = item

    def to_dict(self):
        return {
            "item": self.item
        }


class OutgoingCalls(IncomingCalls):
    method = "callHierarchy/outgoingCalls"
