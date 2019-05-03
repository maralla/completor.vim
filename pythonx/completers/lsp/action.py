# -*- coding: utf-8 -*-

from .utils import parse_uri


# [
#   [{
#       u'range': {
#           u'start': {u'line': 273, u'character': 5},
#           u'end': {u'line': 273, u'character': 12}
#       },
#       u'uri': u'file:///home/linuxbrew/.linuxbrew/Cellar/go/1.12.4/libexec/src/fmt/print.go'  # noqa
#   }]
# ]
def gen_definition(data):
    res = []
    if not data:
        return res
    items = data[0]
    for item in items:
        start = item['range']['start']
        res.append({
            'filename': parse_uri(item['uri']),
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
