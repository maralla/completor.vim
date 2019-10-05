# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import json
import contextlib
import logging
import os.path
import sys

log_file = os.path.join(os.path.dirname(__file__), 'completor_python.log')
logger = logging.getLogger('python-jedi')
handler = logging.FileHandler(log_file, delay=1)
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s][%(module)s] %(message)s'))
logger.addHandler(handler)


def write(msg):
    print(msg)
    sys.stdout.flush()


class JediProcessor(object):
    def __init__(self, jedi):
        self.jedi = jedi
        self.script = None

    @contextlib.contextmanager
    def jedi_context(self, args):
        self.script = self.jedi.Script(
            source=args['content'], line=args['line'] + 1,
            column=args['col'], path=args['filename'])
        try:
            yield
        finally:
            self.script = None

    def ignore(self):
        script = self.script
        try:
            node = script._module_node.get_leaf_for_position(script._pos)
            return not node or node.type in ('string', 'number')
        except Exception as e:
            logger.exception(e)
            return False

    def process(self, args):
        action = args.get('action')
        func = getattr(self, 'on_{}'.format(action), None)
        if not func:
            return []
        with self.jedi_context(args):
            if self.ignore():
                return []
            return list(func())

    def _statement(self, c):
        if c.type == 'statement':
            assignments = c.goto_assignments()
            if assignments:
                return assignments[-1]
        return c

    def on_complete(self):
        for c in self.script.completions():
            statement_c = self._statement(c)
            try:
                yield {
                    'word': c.name,
                    'abbr': c.name_with_symbols,
                    'menu': statement_c.description,
                    'info': statement_c.docstring(),
                }
            except Exception as e:
                logger.exception(e)
                continue

    def on_definition(self):
        for d in self.script.goto_assignments(follow_imports=True):
            item = {'text': d.description}
            if d.in_builtin_module():
                item['text'] = 'Builtin {}'.format(item['text'])
            else:
                item.update({
                    'filename': d.module_path,
                    'lnum': d.line,
                    'col': d.column + 1,
                    'name': d.name,
                })
            yield item

    def on_doc(self):
        for d in self.script.goto_assignments(follow_imports=True):
            yield d.docstring(fast=False).strip()

    def on_signature(self):
        for s in self.script.call_signatures():
            params = [p.description.replace('\n', '')[6:] for p in s.params]
            yield {
                'params': params,
                'func': s.call_name,
                'index': s.index or 0
            }


def run(jedi):
    """
    input data:
    {
        "line": <int>,
        "col": <int>,
        "filename": <string>,
        "content": <string>,
    }
    """
    processor = JediProcessor(jedi)

    while True:
        data = sys.stdin.readline()
        logger.info(data)

        try:
            args = json.loads(data)
        except Exception as e:
            logger.exception(e)
            continue

        try:
            ret = processor.process(args)
        except Exception as e:
            logger.exception(e)
            ret = []
        write(json.dumps(ret))


def main():
    try:
        import jedi
    except ImportError:
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    class Filter(object):
        def filter(self, record):
            return args.verbose

    logger.addFilter(Filter())
    run(jedi)


if __name__ == '__main__':
    main()
