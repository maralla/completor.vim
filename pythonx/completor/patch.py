def _bytes(data):
    if isinstance(data, str):
        return data.encode('utf-8')

    if isinstance(data, list):
        for i, e in enumerate(data):
            data[i] = _bytes(e)
    elif isinstance(data, dict):
        for k, v in data.items():
            data[_bytes(k)] = _bytes(v)

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

    vim.Function = function
    vim.bindeval = bindeval
    vim.List = list
