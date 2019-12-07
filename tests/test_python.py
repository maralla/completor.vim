# -*- coding: utf-8 -*-

import completor

def test_python_jedi_requests(vim_mod):
    import jedi
    from completers.python.python_jedi import JediProcessor
    
    args = {'action': 'complete', 'line': 0, 'col': 28, 'filename': '1.py', 'content': 'import requests; requests.ge'}
    processor = JediProcessor(jedi)
    try:
        import requests
        assert processor.process(args)[0]['menu'] == 'def get'
    except ImportError:
        assert processor.process(args)[0]['menu'] == 'get = api.get'
