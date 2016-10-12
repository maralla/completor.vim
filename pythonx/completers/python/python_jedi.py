# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import json
import logging
import os.path
import sys

log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "completor.log")
logging.basicConfig(
    filename=log_file, level=logging.INFO,
    format='%(asctime)s [%(levelname)s][%(module)s] %(message)s')


def write(msg):
    print(msg)
    sys.stdout.flush()


def get_completions(args):
    import jedi
    script = jedi.Script(source=args['content'], line=args['line'] + 1,
                         column=args['col'], path=args['filename'])

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
        "content": <string>,
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

        try:
            get_completions(args)
        except Exception as e:
            logging.exception(e)
            write(json.dumps([]))


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
