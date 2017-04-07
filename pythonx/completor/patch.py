def _bytes(data):
    from completor import get_encoding

    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode(get_encoding())

    if isinstance(data, list):
        for i, e in enumerate(data):
            data[i] = _bytes(e)
    elif isinstance(data, dict):
        for k in list(data.keys()):
            data[_bytes(k)] = _bytes(data.pop(k))
    return data


def patch_nvim(vim):
    class Bindeval(object):
        def __init__(self, data):
            self.data = data

        def __getitem__(self, key):
            return _bytes(self.data[key])

    def function(name):
        def inner(*args, **kwargs):
            ret = vim.call(name, *args, **kwargs)
            return _bytes(ret)
        return inner

    def bindeval(value):
        data = vim.eval(value)
        return Bindeval(data)

    vim_vars = vim.vars

    class vars_wrapper(object):
        def get(self, *args, **kwargs):
            item = vim_vars.get(*args, **kwargs)
            return _bytes(item)

    vim.Function = function
    vim.bindeval = bindeval
    vim.List = list
    vim.vars = vars_wrapper()
