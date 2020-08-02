# -*- coding: utf-8 -*-

import re
import logging
from completor.utils import check_subseq
from .utils import parse_uri

word_pat = re.compile(r'([\d\w]+)', re.U)
word_ends = re.compile(r'[\d\w]+$', re.U)

logger = logging.getLogger("completor")


# [
#   [{
#       u'range': {
#           u'start': {u'line': 273, u'character': 5},
#           u'end': {u'line': 273, u'character': 12}
#       },
#       u'uri': u'file:///home/linuxbrew/.linuxbrew/Cellar/go/1.12.4/libexec/src/fmt/print.go'  # noqa
#   }]
# ]
def gen_jump_list(ft, name, data):
    res = []

    if not data:
        return res
    items = data[0]

    if items is None:
        return res

    for item in items:
        uri = parse_uri(item['uri'])
        if ft == 'go':
            uri = uri.replace('%21', '!')
        start = item['range']['start']
        res.append({
            'filename': uri,
            'lnum': start['line'] + 1,
            'col': start['character'] + 1,
            'name': name,
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


def get_completion_word(item, insert_text):
    if insert_text != b'label':
        try:
            return item['textEdit']['newText'], \
                item['textEdit']['range']['start']['character']
        except KeyError:
            pass

    label = item['label'].strip()
    match = word_pat.match(label)
    return match.groups()[0] if match else '', -1


hiddenLines = ["on pkg.go.dev"]
escapes = re.compile(r'''\\([\\\x60*{}[\]()#+\-.!_>~|"$%&'\/:;<=?@^])''',
                     re.UNICODE)
escape_types = ['go', 'json']


def _shouldHidden(line):
    for item in hiddenLines:
        if item in line:
            return True

    return False


def gen_hover_doc(ft, value):
    if ft not in escape_types:
        return value

    lines = []

    for l in value.split("\n"):
        if _shouldHidden(l):
            continue

        lines.append(escapes.sub(r"\1", l).replace('&nbsp;', ' '))

    return "\n".join(lines)


def filter_items(items, input_data):
    target = ''
    match = word_ends.search(input_data)
    if match:
        target = match.group()

    if not target:
        return items

    filtered = []
    for item in items:
        score = check_subseq(target, item[1])
        if score is None:
            continue
        filtered.append((item, score))

    filtered.sort(key=lambda x: x[1])
    return [e for e, _ in filtered]
