# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import os
import re
import sys

PATH = os.path.dirname(__file__)
sys.path.insert(0, PATH)

from utils import PATH_PATTERN


def find(input_data):
    match = re.search(PATH_PATTERN, input_data, re.X)
    path_dir = (os.path.expanduser(os.path.expandvars(match.group()))
                if match else '')
    if not path_dir:
        return []

    dirname, basename = os.path.split(path_dir)
    if not dirname:
        dirname = '.'

    entries = set(os.listdir(dirname))
    high = [e for e in entries if e.startswith(basename)]
    entries = entries.difference(high)
    mid = [e for e in entries if basename in e]
    entries = entries.difference(mid)
    low = [(len(set(basename).intersection(e)), e) for e in entries]
    low.sort(key=lambda x: x[0], reverse=True)
    return high + mid + [e for _, e in low]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_data')
    args = parser.parse_args()

    try:
        res = find(args.input_data)
    except Exception:
        res = []

    for item in res:
        print(item)


if __name__ == '__main__':
    main()
