# -*- coding: utf-8 -*-

import re

LIMIT = 50
REGEX_MAP = {
    # Spec: http://www.w3.org/TR/CSS2/syndata.html#characters
    # Good summary: http://stackoverflow.com/a/449000/1672783
    'css': r"-?[_a-zA-Z][\w-]*",

    # Spec: http://www.w3.org/TR/html5/syntax.html#tag-name-state
    # But not quite since not everything we want to pull out is a tag name. We
    # also want attribute names (and probably unquoted attribute values).
    # And we also want to ignore common template chars like `}` and `{`.
    'html': r"[a-zA-Z][^\s/>='\"}{\.]*",

    # Spec: http://cran.r-project.org/doc/manuals/r-release/R-lang.pdf
    # Section 10.3.2.
    # Can be any sequence of '.', '_' and alphanum BUT can't start with:
    #   - '.' followed by digit
    #   - digit
    #   - '_'
    'r': r"(?!(?:\.\d|\d|_))[\.\w]+",

    # Spec: http://clojure.org/reader
    # Section: Symbols
    'clojure': r"[-\*\+!_\?:\.a-zA-Z][-\*\+!_\?:\.\w]*/?[-\*\+!_\?:\.\w]*",

    # Spec: http://www.haskell.org/onlinereport/lexemes.html
    # Section 2.4
    'haskell': r"[_a-zA-Z][\w']*",

    # Spec: ?
    # Labels like \label{fig:foobar} are very common
    'tex': r"[_a-zA-Z:-]+",

    # Spec: http://doc.perl6.org/language/syntax
    'perl6': r"[_a-zA-Z](?:\w|[-'](?=[_a-zA-Z]))*",

    'php': r"[_a-zA-Z$]\w*",
    'html': r"[\w-]+",
}

for ty in ('scss', 'sass', 'less'):
    REGEX_MAP[ty] = REGEX_MAP['css']
for ty in ('elisp', 'lisp'):
    REGEX_MAP[ty] = REGEX_MAP['clojure']

for k, v in list(REGEX_MAP.items()):
    REGEX_MAP[k] = re.compile(v, re.U)


def test_subseq(src, target):
    if not src:
        return 0

    score = i = 0
    src, target = src.lower(), target.lower()
    src_len, target_len = len(src), len(target)
    for index, e in enumerate(target):
        if src_len - i > target_len - index:
            return
        if e != src[i]:
            continue
        if index == 0:
            score = -999
        score += index
        i += 1
        if i == src_len:
            return score
