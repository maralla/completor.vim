" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:completions = []
let s:daemon = {}

function s:daemon.respawn(cmd)
  if self.status() == 'run'
    call job_stop(self.job)
  endif

  let self.job = job_start(a:cmd, {"out_cb": {c,m->s:trigger(m)}, "err_io": 'out', "mode": 'nl'})
endfunction

function s:daemon.write(data)
  let ch = job_getchannel(self.job)
  call ch_sendraw(ch, a:data."\n")
endfunction

function s:daemon.status()
  if !exists('self.job')
    return 'none'
  endif

  return job_status(self.job)
endfunction


function! completor#omnifunc(findstart, base)
  if a:findstart
    let word = matchstr(getline('.'), '\w*\%'.col('.').'c')
    return col('.') - 1 - len(word)
  endif
  return s:completions
endfunction


function! s:trigger(msg)
Py << EOF
import completor, vim
completer = completor.current_completer
result = completer.parse(vim.eval('a:msg')) if completer else []
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


function! s:handle(ch)
  let msg = []
  while ch_status(a:ch) == 'buffered'
    call add(msg, ch_read(a:ch))
  endwhile
  call s:trigger(msg)
endfunction


function! s:reset()
  let s:completions = []
  if exists('s:job') && job_status(s:job) == 'run'
    call job_stop(s:job)
  endif
endfunction


function! s:complete()
  call s:reset()

  let end = col('.') - 2
  let inputted = end >= 0 ? getline('.')[:end] : ''
  let ft = &filetype

Py << EOF
import completor, vim
inputted = vim.eval('inputted')
completer = completor.load_completer(vim.eval('ft'), inputted)
completor.current_completer = completer
cmd, daemon = '', False
if completer:
  cmd = completer.format_cmd()
  daemon = completer.daemon
EOF

  let cmd = Pyeval('cmd')
  if !empty(cmd)
    if Pyeval('daemon')
      if s:daemon.status() != 'run'
        call s:daemon.respawn(cmd)
      endif
      let filename = expand('%:p')
      let tempname = completor#utils#tempname()
      let req = {"line": line('.') - 1, "col": col('.') - 1, "filename": filename, "input": inputted, "path": tempname}
      call s:daemon.write(json_encode(req))
    else
      let s:job = job_start(cmd, {"close_cb": {c->s:handle(c)}, "in_io": 'null', "err_io": 'out'})
    endif
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

  if get(g:, 'completor_auto_close_doc', 1)
    autocmd! CompleteDone * if pumvisible() == 0 | pclose | endif
  endif

  Py import completers.common
  call s:set_events()
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
