# -*- coding: utf-8 -*-

import json
import os.path

from completor import Completor

dirname = os.path.dirname(__file__)


class Tern(Completor):
    filetype = 'javascript'
    daemon = True
    trigger = r'\w+$|[\w\)\]\}\'\"]+\.\w*$'

    def format_cmd(self):
        binary = self.get_option('completor_node_binary') or 'node'
        tern_config = self.find_config_file('.tern-project')
        cmd = [binary, os.path.join(dirname, 'tern_wrapper.js')]
        if tern_config:
            cmd.append(os.path.dirname(tern_config))
        return cmd

    def parse(self, data):
        try:
            return json.loads(data)
        except Exception:
            return []
