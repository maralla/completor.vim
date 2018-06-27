# -*- coding: utf-8 -*-

import json
import os.path

from completor import Completor
from completor.compat import to_unicode

dirname = os.path.dirname(__file__)


class Tern(Completor):
    filetype = 'javascript'
    daemon = True
    trigger = r'\w+$|[\w\)\]\}\'\"]+\.\w*$'

    def format_cmd(self):
        binary = self.get_option('node_binary') or 'node'
        tern_config = self.find_config_file('.tern-project')
        cmd = [binary, os.path.join(dirname, 'tern_wrapper.js')]
        if tern_config:
            cmd.append(os.path.dirname(tern_config))
        return cmd

    def parse(self, data):
        try:
            data = to_unicode(data[0], 'utf-8')
            return [i for i in json.loads(data)
                    if not self.input_data.endswith(i['word'])]
        except Exception:
            return []
