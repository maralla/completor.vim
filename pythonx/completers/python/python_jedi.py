# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import json
import logging
import os.path
import sys

log_file = os.path.join(os.path.dirname(__file__), 'completor_python.log')
logging.basicConfig(
    filename=log_file, level=logging.INFO,
    format='%(asctime)s [%(levelname)s][%(module)s] %(message)s')


def write(msg):
    print(msg)
    sys.stdout.flush()


def process_request(args):
    import jedi
    script = jedi.Script(source=args['content'], line=args['line'] + 1,
                         column=args['col'], path=args['filename'])

    data = []
    if args['action'] == 'complete':
        for c in script.completions():
            res = {
                'word': c.name,
                'abbr': c.name_with_symbols,
                'menu': c.description,
                'info': c.docstring(),
            }
            data.append(res)
    elif args['action'] == 'definition':
        for d in script.goto_definitions():
            item = {'text': d.description}
            if d.in_builtin_module():
                item['text'] = 'Builtin {}'.format(item['text'])
            else:
                item.update({'filename': d.module_path, 'lnum': d.line,
                             'col': d.column + 1})
            data.append(item)
    elif args['action'] == 'doc':
        for d in script.goto_definitions():
            data.append(d.docstring(fast=False).strip())
    elif args['action'] == 'signature':
        for s in script.call_signatures():
            params = [p.description.replace('\n', '')[6:] for p in s.params]
            item = {
                'params': params,
                'func': s.call_name,
                'index': s.index or 0
            }
            logging.info(str(item))
            data.append(item)
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
            process_request(args)
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
