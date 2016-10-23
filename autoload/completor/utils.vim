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


function! completor#utils#get_completions(msg, inputted)
Py << EOF
import completor, vim
c = completor.current
result = c.parse(vim.eval('a:msg')) if c else []
if not result and c.filetype != 'common':
  result = completor.get('common').parse(vim.eval('a:inputted'))
EOF
  return Pyeval('result')
endfunction
