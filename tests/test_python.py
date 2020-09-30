# -*- coding: utf-8 -*-


def test_python_jedi_requests(vim_mod):
    import jedi
    from completers.python.python_jedi import JediProcessor

    args = {
        'action': 'complete',
        'line': 0,
        'col': 28,
        'filename': '1.py',
        'content': 'import requests; requests.ge'
    }

    processor = JediProcessor(jedi)
    items = processor.process(args)

    menus = [i['menu'] for i in items]

    assert 'def get' in menus
