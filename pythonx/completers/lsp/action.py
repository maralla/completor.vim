# -*- coding: utf-8 -*-

import re
from .utils import parse_uri

word_pat = re.compile(r'([\d\w]+)', re.U)


# [
#   [{
#       u'range': {
#           u'start': {u'line': 273, u'character': 5},
#           u'end': {u'line': 273, u'character': 12}
#       },
#       u'uri': u'file:///home/linuxbrew/.linuxbrew/Cellar/go/1.12.4/libexec/src/fmt/print.go'  # noqa
#   }]
# ]
def gen_definition(ft, data):
    res = []
    if not data:
        return res
    items = data[0]
    for item in items:
        uri = parse_uri(item['uri'])
        if ft == 'go':
            uri = uri.replace('%21', '!')
        start = item['range']['start']
        res.append({
            'filename': uri,
            'lnum': start['line'] + 1,
            'col': start['character'] + 1,
            'name': 'definition'
        })
    return res


# [
#     [
#         {
#             u'newText': u'',
#             u'range': {
#                 u'start': {u'line': 8, u'character': 0},
#                 u'end': {u'line': 9, u'character': 0}
#             }
#         }, {
#             u'newText': u'',
#             u'range': {
#                 u'start': {u'line': 9, u'character': 0},
#                 u'end': {u'line': 10, u'character': 0}
#             }
#         }, {
#             u'newText': u'\tfmt.Println()\n',
#             u'range': {
#                 u'start': {u'line': 10, u'character': 0},
#                 u'end': {u'line': 10, u'character': 0}
#             }
#         }, {
#             u'newText': u'}\n',
#             u'range': {
#                 u'start': {u'line': 10, u'character': 0},
#                 u'end': {u'line': 10, u'character': 0}
#             }
#         }
#     ]
# ]
def format_text(data):
    if not data:
        return
    for item in data[0]:
        pass


def get_completion_word(item):
    try:
        return item['textEdit']['newText'], \
            item['textEdit']['range']['start']['character']
    except KeyError:
        pass
    label = item['label'].strip()
    match = word_pat.match(label)
    return match.groups()[0] if match else '', -1
