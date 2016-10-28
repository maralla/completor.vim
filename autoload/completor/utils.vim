function! completor#utils#tempname()
  let tmp = escape(tempname(), ' ')
  let ext = expand('%:p:e')
  let ext = empty(ext) ? '' : '.'.ext
  let tmp .= ext
  call writefile(getline(1, '$'), tmp)
  return tmp
endfunction


function! completor#utils#get_completer(ft, inputted)
Py << EOF
import completor, vim
c = completor.load_completer(vim.eval('a:ft'), vim.eval('a:inputted'))
info = [c.format_cmd(), c.filetype, c.daemon, c.sync] if c else []
completor.current = c
EOF
  return Pyeval('info')
endfunction


function! completor#utils#get_completions(ft, msg, inputted)
Py << EOF
import completor, vim
inputted = vim.eval('a:inputted')
c = completor.current
result, ft, ty = ((c.get_completions(vim.eval('a:msg')), c.ft, c.filetype)
                  if c else ([], vim.eval('a:ft'), ''))
if not result and ty != 'common':
  c = completor.get('common', ft, inputted)
  completor.current = c
  result = c.get_completions(inputted)
EOF
  return Pyeval('result')
endfunction


function! completor#utils#get_start_column()
Py << EOF
import completor
column = completor.current.start_column() if completor.current else -1
EOF
  return Pyeval('column')
endfunction
