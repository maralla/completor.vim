" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:completions = []
let s:daemon = {}
let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}

function s:nvim_daemon(job_id, data, event)
  if a:event == 'stdout'
    s:trigger(a:data)
  elseif a:event == 'stderr'
    s:trigger(a:data)
  else
    unlet self.job
  endif
endfunction

function s:daemon.respawn(cmd, name)
  if has('nvim')
    if self.status(a:name) == 'run'
      call jobstop(self.job)
    endif

    let self.job = jobstart(a:cmd, {
          \   "on_stdout": function('s:nvim_daemon'),
          \   "on_stderr": function('s:nvim_daemon'),
          \   "on_exit": function('s:nvim_daemon'),
          \ })
    let self.type = a:name
  else
    if self.status(a:name) == 'run'
      call job_stop(self.job)
    endif

    let self.job = job_start(a:cmd, {
          \   "out_cb": {c, m -> s:trigger(m)},
          \   "err_io": 'out',
          \   "mode": 'nl'
          \ })
    let self.type = a:name
  endif
endfunction

function s:daemon.write(data)
  if has('nvim')
    jobsend(self.job, a:data."\n")
  else
    let ch = job_getchannel(self.job)
    call ch_sendraw(ch, a:data."\n")
  endif
endfunction

function s:daemon.status(name)
  if !exists('self.job')
    return 'none'
  endif

  if has('nvim')
    let s = 'run'
  else
    let s = job_status(self.job)
  endif
  if exists('self.type') && self.type != a:name
    if s == 'run'
      if has('nvim')
        call jobstop(self.job)
      else
        call job_stop(self.job)
      endif
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
  call feedkeys("\<C-x>\<C-u>\<C-p>", 'n')
endfunction


function s:nvim_handle(job_id, data, event)
  if a:event == 'stdout'
    s:trigger(a:data)
  elseif a:event == 'stderr'
    s:trigger(a:data)
  else
    unlet s:job
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
  if exists('s:job') && (has('nvim') || job_status(s:job) == 'run')
    if has('nvim')
      call jobstop(s:job)
    else
      call job_stop(s:job)
    endif
  endif
endfunction


function! s:process_daemon(cmd, name)
  if s:daemon.status(a:name) != 'run'
    call s:daemon.respawn(a:cmd, a:name)
  endif
  let filename = expand('%:p')
  let content = join(getline(1, '$'), "\n")
  let req = {
        \   "line": line('.') - 1,
        \   "col": col('.') - 1,
        \   "filename": filename,
        \   "content": content
        \ }
  call s:daemon.write(json_encode(req))
endfunction


function! s:complete(t)
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
      if has('nvim')
        let s:job = jobstart(cmd, {
              \   "on_stdout": function('s:nvim_handle'),
              \   "on_stderr": function('s:nvim_handle'),
              \   "on_exit": function('s:nvim_handle'),
              \ })
      else
        let s:job = job_start(cmd, {
              \   "close_cb": {c -> s:handle(c)},
              \   "in_io": 'null',
              \   "err_io": 'out'
              \ })
      endif
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
    if has('nvim')
      call timer_stop(s:timer)
    else
      let info = timer_info(s:timer)
      if !empty(info)
        call timer_stop(s:timer)
      endif
    endif
  endif

  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''

  let s:status = {'input': inputted, 'pos': getcurpos(), 'nr': bufnr(''), 'ft': &ft}
  let s:timer = timer_start(16, function('s:complete'))
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
