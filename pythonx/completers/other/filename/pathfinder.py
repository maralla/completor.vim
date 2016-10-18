# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import os


def find(input_data):
    path_dir = os.path.expanduser(os.path.expandvars(input_data))
    if not path_dir:
        return []

    dirname, basename = os.path.split(path_dir)
    if not dirname:
        dirname = '.'

    entries = set(os.listdir(dirname))
    high = [e for e in entries if e.startswith(basename)]
    entries = entries.difference(high)
    mid = [e for e in entries if basename in e]
    return high + mid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_data')

    try:
        args = parser.parse_args()
        res = find(args.input_data)
    except Exception:
        res = []

    for item in res:
        print(item)


if __name__ == '__main__':
    main()
