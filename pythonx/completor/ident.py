# -*- coding: utf-8 -*-

import vim
import re

REGEX_MAP = {
    b'default': r"^[^\W\d]\w*$",

    # Spec: http://www.w3.org/TR/CSS2/syndata.html#characters
    # Good summary: http://stackoverflow.com/a/449000/1672783
    b'css': r"^-?[_a-zA-Z][\w-]*$",

    # Spec: http://www.w3.org/TR/html5/syntax.html#tag-name-state
    # But not quite since not everything we want to pull out is a tag name. We
    # also want attribute names (and probably unquoted attribute values).
    # And we also want to ignore common template chars like `}` and `{`.
    b'html': r"^[a-zA-Z][^\s/>='\"}{\.]*$",

    # Spec: http://cran.r-project.org/doc/manuals/r-release/R-lang.pdf
    # Section 10.3.2.
    # Can be any sequence of '.', '_' and alphanum BUT can't start with:
    #   - '.' followed by digit
    #   - digit
    #   - '_'
    b'r': r"^(?!(?:\.\d|\d|_))[\.\w]+$",

    # Spec: http://clojure.org/reader
    # Section: Symbols
    b'clojure': r"^[-\*\+!_\?:\.a-zA-Z][-\*\+!_\?:\.\w]*/?[-\*\+!_\?:\.\w]*$",

    # Spec: http://www.haskell.org/onlinereport/lexemes.html
    # Section 2.4
    b'haskell': r"^[_a-zA-Z][\w']*$",

    # Spec: ?
    # Labels like \label{fig:foobar} are very common
    b'tex': r"^[_a-zA-Z:-]+$",

    # Spec: http://doc.perl6.org/language/syntax
    b'perl6': r"^[_a-zA-Z](?:\w|[-'](?=[_a-zA-Z]))*$",

    b'php': r"^[_a-zA-Z$]\w*$",
}

for ty in (b'scss', b'sass', b'less'):
    REGEX_MAP[ty] = REGEX_MAP[b'css']
for ty in (b'elisp', b'lisp'):
    REGEX_MAP[ty] = REGEX_MAP[b'clojure']

for k, v in list(REGEX_MAP.items()):
    REGEX_MAP[k] = re.compile(v, re.U)


def start_column(ft, text=None):
    if text is None:
        index = vim.current.window.cursor[1]
        text = vim.current.line[:index]
    else:
        index = len(text)

    regex = REGEX_MAP.get(ft, REGEX_MAP[b'default'])
    for i in range(index):
        if regex.match(text[i:index]):
            return i
    return index
