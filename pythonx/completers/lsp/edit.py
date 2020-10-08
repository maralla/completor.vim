# -*- coding: utf-8 -*-


def edit(data, changes):
    parts = []
    current_line = 0
    current_column = 0

    for i, change in enumerate(changes):
        start_line = change['range']['start']['line']
        if start_line > current_line:
            parts.append(''.join(data[current_line:start_line]))

        start_column = change['range']['start']['character']
        if start_column > 0:
            parts.append(data[start_line][current_column:start_column])

        end_line = change['range']['end']['line']
        current_line = end_line + 1

        parts.append(change['newText'])

        current_column = end_column = change['range']['end']['character']

        if i >= len(changes) - 1 or \
                changes[i+1]['range']['start']['line'] != end_line:
            parts.append(data[end_line][end_column:])
            current_column = 0

    if current_line < len(data):
        parts.append(''.join(data[current_line:]))

    return ''.join(parts)
