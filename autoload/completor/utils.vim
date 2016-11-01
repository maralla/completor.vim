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
args = vim.bindeval('a:')
c = completor.load_completer(args['ft'], args['inputted'])
info = [c.format_cmd(), c.filetype, c.daemon, c.sync] if c else []
completor.current = c
EOF
  return Pyeval('info')
endfunction


function! completor#utils#get_completions(ft, msg, inputted)
Py << EOF
import completor, vim
args = vim.bindeval('a:')
c = completor.current
result, ft, ty = ((c.get_completions(args['msg']), c.ft, c.filetype)
                  if c else ([], args['ft'], ''))
if not result and ty != 'common':
  c = completor.get('common', ft, args['inputted'])
  completor.current = c
  result = c.get_completions(args['inputted'])
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


function! completor#utils#daemon_request()
Py << EOF
import completor
args = completor.current.request() if completor.current else ''
EOF
  return Pyeval('args')
endfunction


function! completor#utils#message_ended(msg)
Py << EOF
import completor
msg = vim.bindeval('a:')['msg']
ended = completor.current.message_ended(msg) if completor.current else False
EOF
  return Pyeval('ended')
endfunction
