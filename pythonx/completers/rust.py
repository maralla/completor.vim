# -*- coding: utf-8 -*-

from completor import Completor

type_map = {
    'Struct': 's', 'Module': 'M', 'Function': 'f',
    'Crate': 'C', 'Let': 'v', 'StructField': 'm',
    'Impl': 'i', 'Enum': 'e', 'EnumVariant': 'E',
    'Type': 't', 'FnArg': 'v', 'Trait': 'T'
}


class Racer(Completor):
    filetype = 'rust'

    name = 'racer'

    def format_cmd(self):
        line, col = self.cursor
        return "{} complete {} {} {} {}".format(self.name, line, col,
                                                self.filename, self.tempname)

    def parse(self, items):
        completions = []
        for item in items:
            if not item.startswith('MATCH'):
                continue

            parts = item.split(',')
            name = parts[0][6:]
            kind = type_map.get(parts[4], '')
            spec = ', '.join(parts[5:])

            completions.append({
                'kind': kind,
                'word': name,
                'menu': spec,
                'dup': 0
            })
        return completions
