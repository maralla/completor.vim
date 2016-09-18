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
completer = completor.current_completer
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
  if exists('s:job') && job_status(s:job) == 'run'
    call job_stop(s:job)
    let s:completions = []
  endif

  let s:job = job_start(a:cmd, {"close_cb": {c->s:handle(c)}, "in_io": 'null', "err_io": 'out'})
endfunction


function! s:complete()
  let s:completions = []
  let end = col('.') - 2
  let inputted = end >= 0 ? getline('.')[:end] : ''

Py << EOF
import completor, vim
inputted = vim.eval('inputted')
completer = completor.load_completer(vim.current.buffer.options['ft'], inputted)
completor.current_completer = completer
cmd = completer.format_cmd() if completer else ''
EOF

  let cmd = Pyeval('cmd')
  if !empty(cmd)
    call s:execute(cmd)
  endif
endfunction


function! s:on_text_change()
  if exists('s:timer')
    let info = timer_info(s:timer)
    if !empty(info)
      call timer_stop(s:timer)
    endif
  endif

  let s:timer = timer_start(16, {t->s:complete()})
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    autocmd TextChangedI * call s:on_text_change()
  augroup END
endfunction


function! completor#enable()
  if &diff
    return
  endif

  Py import completers.common
  call s:set_events()
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
