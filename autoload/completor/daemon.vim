let s:daemon = {'msgs': [], 'requested': v:false, 't': 0}


function! s:vim_daemon_handler(msg)
  call add(s:daemon.msgs, a:msg)
  if completor#utils#is_message_end(a:msg)
    let s:daemon.requested = v:false
    call completor#action#callback(s:daemon.msgs)
  endif
endfunction


let s:nvim_last_msg = ''
function! s:nvim_read(data)
  let data = a:data

  if !empty(s:nvim_last_msg) && !empty(data)
    let s:nvim_last_msg .= data[0]
    let data = data[1:]
    if !empty(data)
      call add(s:daemon.msgs, s:nvim_last_msg)
      let s:nvim_last_msg = ''
    endif
  endif

  if !empty(data)
    let s:nvim_last_msg = data[-1]
    call extend(s:daemon.msgs, data[0:-2])
  endif
endfunction


function! s:nvim_daemon_handler(job_id, data, event)
  if a:event ==# 'exit'
    return
  endif

  call s:nvim_read(a:data)

  if empty(s:nvim_last_msg) && !empty(s:daemon.msgs)
    if completor#utils#is_message_end(s:daemon.msgs[-1])
      let s:daemon.requested = v:false
      call completor#action#callback(s:daemon.msgs)
    endif
  endif
endfunction


if has('nvim')
  " neovim
  function! s:job_start_daemon(cmd, cwd)
    return jobstart(a:cmd, {
          \   'on_stdout': function('s:nvim_daemon_handler'),
          \   'on_stderr': function('s:nvim_daemon_handler'),
          \   'on_exit': function('s:nvim_daemon_handler'),
          \   'cwd': a:cwd,
          \ })
  endfunction

  function! s:daemon.write(data)
    let s:nvim_last_msg = ''
    try
      call jobsend(self.job, a:data."\n")
    catch /E900/
    endtry
  endfunction
else
  " vim8
  function! s:job_start_daemon(cmd, cwd)
    return job_start(a:cmd, {
          \   'out_cb': {c,m->s:vim_daemon_handler(m)},
          \   'err_io': 'out',
          \   'mode': 'nl',
          \   'cwd': a:cwd,
          \ })
  endfunction

  function! s:daemon.write(data)
    try
      call ch_sendraw(job_getchannel(self.job), a:data."\n")
    catch /E631/
      call self.kill()
    endtry
  endfunction
endif


function! s:daemon.respawn(cmd, cwd, name)
  if self.status(a:name) == 'run'
    call completor#compat#job_stop(self.job)
  endif
  let self.job = s:job_start_daemon(a:cmd, a:cwd)
  let self.type = a:name
  let self.cmd = a:cmd
  let self.requested = v:false
  let self.t = localtime()
endfunction


function! s:daemon.status(name)
  if !exists('self.job')
    return 'none'
  endif
  let s = completor#compat#job_status(self.job)
  if exists('self.type') && self.type != a:name
    if s ==# 'run'
      call completor#compat#job_stop(self.job)
      let s = completor#compat#job_status(self.job)
    endif
    return 'none'
  endif
  return s
endfunction


function s:daemon.kill()
  if exists('self.job') && completor#compat#job_status(self.job) ==# 'run'
    let self.requested = v:false
    call completor#compat#job_stop(self.job, 'kill')
  endif
endfunction


function! completor#daemon#process(action, cmd, cwd, name)
  let s:daemon.msgs = []

  " Daemon not running
  if s:daemon.status(a:name) != 'run'
    call s:daemon.respawn(a:cmd, a:cwd, a:name)
  endif

  if s:daemon.status(a:name) != 'run'
    return
  endif

  " Already requested
  if s:daemon.requested
    if localtime() - s:daemon.t > 5
      call s:daemon.kill()
    endif
    return
  endif

  let req = completor#utils#prepare_request(a:action)
  if empty(req)
    return
  endif

  call s:daemon.write(req)

  let s:daemon.requested = v:true
  let s:daemon.t = localtime()
endfunction


function! s:check_status()
  if s:daemon.status(s:daemon.type) != 'run'
    echo 'Daemon killed'
  endif
endfunction


function! completor#daemon#kill()
  if has_key(s:daemon, 'type')
    call s:daemon.kill()
    call timer_start(300, {t->s:check_status()})
  else
    echo 'Daemon killed.'
  endif
endfunction
