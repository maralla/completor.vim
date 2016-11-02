" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:completions = []
let s:daemon = {'msgs': [], 'requested': v:false, 't': 0}
let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}

function s:daemon.respawn(cmd, name)
  if self.status(a:name) == 'run'
    call job_stop(self.job)
  endif

  let self.job = job_start(a:cmd, {
        \   "out_cb": {c,m->s:daemon_handler(m)},
        \   "err_io": 'out',
        \   "mode": 'nl'
        \ })
  let self.type = a:name
  let self.requested = v:false
  let self.t = localtime()
endfunction

function s:daemon.kill()
  if exists('self.job') && job_status(self.job) == 'run'
    let self.requested = v:false
    call job_stop(self.job, 'kill')
  endif
endfunction

function s:daemon.write(data)
  let ch = job_getchannel(self.job)
  call ch_sendraw(ch, a:data."\n")
endfunction

function s:daemon.status(name)
  if !exists('self.job')
    return 'none'
  endif

  let s = job_status(self.job)
  if exists('self.type') && self.type != a:name
    if s == 'run'
      call job_stop(self.job)
    endif
    return 'none'
  endif

  return s
endfunction


function! completor#completefunc(findstart, base)
  if a:findstart
    return completor#utils#get_start_column()
  endif
  return s:completions
endfunction


function! s:consistent()
  return s:status.nr == bufnr('') && s:status.pos == getcurpos() && s:status.ft == &ft
endfunction


function! s:trigger(msg)
  if !s:consistent()
    let s:completions = []
  else
    let s:completions = completor#utils#get_completions(s:status.ft, a:msg, s:status.input)
  endif
  if empty(s:completions) | return | endif

  setlocal completefunc=completor#completefunc
  setlocal completeopt-=longest
  setlocal completeopt+=menuone
  setlocal completeopt-=menu
  if &completeopt !~# 'noinsert\|noselect'
    setlocal completeopt+=noselect
  endif
  if get(g:, "completor_auto_trigger", 1)
    call feedkeys("\<C-x>\<C-u>\<C-p>", 'n')
  endif
endfunction


function! s:daemon_handler(msg)
  call add(s:daemon.msgs, a:msg)

  if completor#utils#message_ended(a:msg)
    call s:trigger(s:daemon.msgs)
    let s:daemon.requested = v:false
  endif
endfunction


function! s:handler(ch)
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


function! s:process_daemon(cmd, name)
  let s:daemon.msgs = []

  if s:daemon.status(a:name) != 'run'
    call s:daemon.respawn(a:cmd, a:name)
  endif

  if s:daemon.requested
    if localtime() - s:daemon.t > 5
      call s:daemon.kill()
    endif
    return
  endif

  let req = completor#utils#daemon_request()
  if empty(req) | return | endif
  call s:daemon.write(req)

  let s:daemon.requested = v:true
  let s:daemon.t = localtime()
endfunction


function! s:complete()
  call s:reset()
  if !s:consistent() | return | endif

  let info = completor#utils#get_completer(s:status.ft, s:status.input)
  if empty(info) | return | endif
  let [cmd, name, daemon, is_sync] = info

  if is_sync
    call s:trigger(s:status.input)
  elseif !empty(cmd)
    if daemon
      call s:process_daemon(cmd, name)
    else
      let s:job = job_start(cmd, {
            \   "close_cb": {c->s:handler(c)},
            \   "in_io": 'null',
            \   "err_io": 'out'
            \ })
    endif
  endif
endfunction


function! s:skip()
  let buftype = &buftype
  let fsize = getfsize(bufname(''))
  let skip = empty(&ft) || buftype == 'nofile' || buftype == 'quickfix'
        \ || fsize == -2 || fsize > g:completor_filesize_limit
        \ || index(g:completor_blacklist, &ft) != -1
  if exists('g:completor_whitelist') && type(g:completor_whitelist) == v:t_list
    let skip = skip || index(g:completor_whitelist, &ft) == -1
  endif
  return skip
endfunction


function! s:on_text_change()
  if s:skip() | return | endif

  if exists('s:timer')
    let info = timer_info(s:timer)
    if !empty(info)
      call timer_stop(s:timer)
    endif
  endif

  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''

  let s:status = {'input': inputted, 'pos': getcurpos(), 'nr': bufnr(''), 'ft': &ft}
  let s:timer = timer_start(50, {t->s:complete()})
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    autocmd TextChangedI * call s:on_text_change()
  augroup END
endfunction


function! completor#disable()
  autocmd! completor
endfunction


function! completor#enable()
  if &diff
    return
  endif

  if get(g:, 'completor_auto_close_doc', 1)
    autocmd! CompleteDone * if pumvisible() == 0 | pclose | endif
  endif

  call s:set_events()
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
