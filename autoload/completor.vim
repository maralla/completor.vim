" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:char_inserted = v:false
let s:completions = {'words': [], 'refresh': 'always'}
let s:daemon = {'msgs': [], 'requested': v:false, 't': 0}
let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}

function s:completions.set(comps)
  let self.words = a:comps
endfunction

function s:completions.clear()
  let self.words = []
endfunction

function s:completions.empty()
  return empty(self.words)
endfunction


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
    if s:completions.empty()
      return -3
    endif
    return completor#utils#get_start_column()
  endif

  let completions = copy(s:completions)
  call s:completions.clear()
  return completions
endfunction


function! s:consistent()
  return s:status.nr == bufnr('') && s:status.pos == getcurpos() && s:status.ft == &ft
endfunction


function! s:trigger(msg)
  let is_empty = v:false
  if !s:consistent()
    call s:completions.clear()
    let is_empty = v:true
  else
    call s:completions.set(completor#utils#get_completions(a:msg))
    if s:completions.empty()
      let is_empty = v:true
      call completor#utils#retrigger()
    endif
  endif
  if is_empty | return | endif

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
  call s:completions.clear()
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


function! completor#do_complete(cmd, name, daemon, is_sync)
  if a:is_sync
    call s:trigger(s:status.input)
  elseif !empty(a:cmd)
    if a:daemon
      call s:process_daemon(a:cmd, a:name)
    else
      let s:job = job_start(a:cmd, {
            \   "close_cb": {c->s:handler(c)},
            \   "in_io": 'null',
            \   "err_io": 'out'
            \ })
    endif
  endif
endfunction


function! s:complete()
  call s:reset()
  if !s:consistent() | return | endif

  let info = completor#utils#get_completer(s:status.ft, s:status.input)
  if empty(info) | return | endif
  let [cmd, name, daemon, is_sync] = info
  call completor#do_complete(cmd, name, daemon, is_sync)
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
  return skip || !s:char_inserted
endfunction


function! s:on_text_change()
  if s:skip() | return | endif
  let s:char_inserted = v:false

  if exists('s:timer')
    let info = timer_info(s:timer)
    if !empty(info)
      call timer_stop(s:timer)
    endif
  endif

  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''

  let s:status = {'input': inputted, 'pos': getcurpos(), 'nr': bufnr(''), 'ft': &ft}
  let s:timer = timer_start(g:completor_completion_delay, {t->s:complete()})
endfunction


function s:on_insert_char_pre()
  let s:char_inserted = v:true
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    autocmd TextChangedI * call s:on_text_change()
    autocmd InsertCharPre * call s:on_insert_char_pre()
  augroup END
  call completor#utils#setup_python()
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
