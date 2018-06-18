# -*- coding: utf-8 -*-

import logging
import functools


logger = logging.getLogger('completor')


def ignore_exception(fallback=()):
    """Ignore exception raised by the decorated function.

    When exception happened the fallback value is returned.
    """
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(e)
                return fallback
        return wrapper
    return deco
