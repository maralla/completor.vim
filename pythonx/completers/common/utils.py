# -*- coding: utf-8 -*-

LIMIT = 50


def test_subseq(src, target):
    if not src:
        return 0

    score = i = 0
    src, target = src.lower(), target.lower()
    src_len, target_len = len(src), len(target)
    for index, e in enumerate(target):
        if src_len - i > target_len - index:
            return
        if e != src[i]:
            continue
        if index == 0:
            score = -999
        score += index
        i += 1
        if i == src_len:
            return score
