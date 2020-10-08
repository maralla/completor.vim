# -*- coding: utf-8 -*-

from completers.lsp.edit import edit


def test_edit():
    data = [
        'pppp\n',
        'hello world foo bar\n',
        'foo, yoyo\n',
        'pp foo, hi foo, yoyo\n',
        'foo, yoyo\n',
    ]

    text = edit(data, [
        {'range': {'start': {'line': 1, 'character': 12}, 'end': {'line': 1, 'character': 15}}, 'newText': "ppoo"},  # noqa
        {'range': {'start': {'line': 2, 'character': 0}, 'end': {'line': 2, 'character': 3}}, 'newText': "ppoo"},  # noqa
        {'range': {'start': {'line': 3, 'character': 3}, 'end': {'line': 3, 'character': 6}}, 'newText': "ppoo"},  # noqa
        {'range': {'start': {'line': 3, 'character': 11}, 'end': {'line': 3, 'character': 14}}, 'newText': "ppoo"},  # noqa
        {'range': {'start': {'line': 4, 'character': 0}, 'end': {'line': 4, 'character': 3}}, 'newText': "ppoo"},  # noqa
    ])

    assert text == 'pppp\nhello world ppoo bar\nppoo, yoyo\npp ppoo, hi ppoo, yoyo\nppoo, yoyo\n'  # noqa
