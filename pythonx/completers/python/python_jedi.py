# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import json
import logging
import os.path
import re
import sys

log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "completor.log")
logging.basicConfig(
    filename=log_file, level=logging.INFO,
    format='%(asctime)s [%(levelname)s][%(module)s] %(message)s')


def write(msg):
    print(msg)
    sys.stdout.flush()


def get_completions(src, args):
    import jedi
    script = jedi.Script(source=src, line=args['line'] + 1, column=args['col'],
                         path=args['filename'])

    data = []
    for c in script.completions():
        res = {
            'word': c.name,
            'abbr': c.name_with_symbols,
            'menu': c.description,
            'info': c.docstring(),
        }
        data.append(res)
    write(json.dumps(data))


def run():
    """
    input data:
    {
        "line": <int>,
        "col": <int>,
        "filename": <string>,
        "input": <string>,
        "path": <string>
    }
    """
    while True:
        data = sys.stdin.readline()
        logging.info(data)

        try:
            args = json.loads(data)
        except Exception as e:
            logging.exception(e)
            continue

        input_data = args['input'].strip()
        if not input_data or not re.search('(\w|\.)+$', input_data):
            return

        try:
            with open(args['path']) as f:
                src = f.read()
            get_completions(src, args)
        except Exception as e:
            logging.exception(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    class Filter(object):
        def filter(self, record):
            return args.verbose

    logging.root.addFilter(Filter())
    run()


if __name__ == '__main__':
    main()
