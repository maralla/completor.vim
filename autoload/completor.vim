" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:completions = []


function! completor#omnifunc(findstart, base)
  if a:findstart
    let word = matchstr(getline('.'), '\w*\%'.col('.').'c')
    return col('.') - 1 - len(word)
  endif
  return s:completions
endfunction


function! s:handle(ch)
  let msg = []
  while ch_status(a:ch) == 'buffered'
    call add(msg, ch_read(a:ch))
  endwhile

Py << EOF
import completor, vim
completer = completor.load_completer(vim.current.buffer.options['ft'])
result = completer.parse(vim.eval('msg')) if completer else []
EOF

  let s:completions = Pyeval('result')
  setlocal omnifunc=completor#omnifunc
  if !empty(s:completions)
    setlocal completeopt-=longest
    setlocal completeopt+=menuone
    setlocal completeopt-=menu
    if &completeopt !~# 'noinsert\|noselect'
      setlocal completeopt+=noselect
    endif
    call feedkeys("\<C-x>\<C-o>", 'n')
  endif
endfunction


function! s:execute(cmd)
  let job = job_start(a:cmd, {"close_cb": {c->s:handle(c)}, "in_io": 'null', "err_io": 'out'})
endfunction


function! s:complete()
Py << EOF
import completor, vim
completer = completor.load_completer(vim.current.buffer.options['ft'])
cmd = completer.format_cmd() if completer else ''
EOF

  let cmd = Pyeval('cmd')
  if !empty(cmd)
    call s:execute(cmd)
  endif
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    autocmd TextChangedI * call s:complete()
  augroup END
endfunction


function! completor#enable()
  if &diff
    return
  endif

  call s:set_events()
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
