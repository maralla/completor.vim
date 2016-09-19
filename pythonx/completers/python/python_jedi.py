# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import json
import re


def get_completions(src, args):
    import jedi
    script = jedi.Script(source=src, line=args.line, column=args.col,
                         path=args.filename)

    for c in script.completions():
        res = {
            'word': c.name,
            'abbr': c.name_with_symbols,
            'menu': c.description,
            'info': c.docstring(),
        }
        print(json.dumps(res))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--line', type=int, required=True)
    parser.add_argument('-c', '--col', type=int, required=True)
    parser.add_argument('-n', '--filename', required=True)
    parser.add_argument('-d', '--input_data', required=True)
    parser.add_argument('path')
    args = parser.parse_args()

    input_data = args.input_data.strip()
    if not input_data or not re.search('(\w|\.)+$', input_data):
        return

    try:
        with open(args.path) as f:
            src = f.read()
        get_completions(src, args)
    except Exception:
        pass


if __name__ == '__main__':
    main()
