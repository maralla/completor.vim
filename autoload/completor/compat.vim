function! s:vim_oneshot_handler(ch)
  let msg = []
  while ch_status(a:ch) ==# 'buffered' && ch_canread(a:ch)
    let chunk = ch_read(a:ch)
    call add(msg, chunk)
  endwhile
  call completor#action#callback(msg)
endfunction


let s:nvim_last_msg = ''
function! s:nvim_read(data)
  let data = a:data

  if !empty(s:nvim_last_msg) && !empty(data)
    let s:nvim_last_msg .= data[0]
    let data = data[1:]
    if !empty(data)
      call add(s:nvim_oneshot_msg, s:nvim_last_msg)
      let s:nvim_last_msg = ''
    endif
  endif

  if !empty(data)
    let s:nvim_last_msg = data[-1]
    call extend(s:nvim_oneshot_msg, data[0:-2])
  endif
endfunction


function! s:nvim_oneshot_handler(job_id, data, event)
  if a:event ==# 'stdout' || a:event ==# 'stderr'
    call s:nvim_read(a:data)
  elseif a:event ==# 'exit'
    call completor#action#callback(s:nvim_oneshot_msg)
  endif
endfunction


if has('nvim')
  " neovim
  function! completor#compat#job_start_oneshot(cmd, options, ...)
    let s:nvim_oneshot_msg = []
    let s:nvim_last_msg = ''
    let conf = {
          \   'on_stdout': function('s:nvim_oneshot_handler'),
          \   'on_stderr': function('s:nvim_oneshot_handler'),
          \   'on_exit': function('s:nvim_oneshot_handler')
          \ }
    call extend(conf, a:options)
    return jobstart(a:cmd, conf)
  endfunction

  function! completor#compat#job_stop(name, ...)
    try
      return jobstop(a:name)
    catch /E900/
      return 0
    endtry
  endfunction

  function! completor#compat#job_status(job)
    try
      call jobpid(a:job)
      return 'run'
    catch /E900/
      return 'dead'
    endtry
  endfunction

  function! completor#compat#job_send(job, data)
    call jobsend(a:job, a:data)
    call jobclose(a:job, 'stdin')
  endfunction
else
  " vim8
  function! completor#compat#job_start_oneshot(cmd, options, use_stdin)
    let conf = {
          \   'close_cb': function('s:vim_oneshot_handler'),
          \   'in_io': a:use_stdin ? 'pipe' : 'null',
          \   'err_io': 'out'
          \ }
    call extend(conf, a:options)
    return job_start(a:cmd, conf)
  endfunction

  function! completor#compat#job_stop(name, ...)
    if empty(a:000)
      return job_stop(a:name)
    else
      return job_stop(a:name, a:000[0])
    endif
  endfunction

  function! completor#compat#job_status(job)
    return job_status(a:job)
  endfunction

  function! completor#compat#job_send(job, data)
    let ch = job_getchannel(a:job)
    if ch_status(ch) ==# 'open'
      call ch_sendraw(ch, a:data)
      call ch_close_in(ch)
    endif
  endfunction
endif
