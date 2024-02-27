# -*- coding:utf-8 -*-
# классом обертка с кэшированием
from functools import wraps

class Cache(object):
    def __init__(self, fn):
        self.fn = fn
        self.cach = {}

    def clear(self):
        self.cach.clear()

    def __call__(self, *args, **kwargs):
        res = self.fn(*args, **kwargs)
        self.cach[args] = res
        return res

# обертка debug
def debug_decorator(func):
    @wraps(func)
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"INFO: func {func.__name__, args, kwargs}")
        print(f'Результат  {result}')
        return result
    return inner



# обертка debug
def debug(f):
    def inner(*args, **kwargs):
        res = f(*args, **kwargs)
        print(args, kwargs, res)
        return res

    return inner

@Cache
@debug
def tost_fun(x, y):
    return x + y


if __name__ == "__main__":
    rslt = tost_fun(4, 5)
    print('stop')