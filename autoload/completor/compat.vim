function! s:vim_oneshot_handler(ch)
  let msg = []
  while ch_status(a:ch) ==# 'buffered'
    call add(msg, ch_read(a:ch))
  endwhile
  call completor#trigger(msg)
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
    call completor#trigger(s:nvim_oneshot_msg)
  endif
endfunction


if has('nvim')
  " neovim
  function! completor#compat#job_start_oneshot(cmd)
    let s:nvim_oneshot_msg = []
    let s:nvim_last_msg = ''
    return jobstart(a:cmd, {
          \   'on_stdout': function('s:nvim_oneshot_handler'),
          \   'on_stderr': function('s:nvim_oneshot_handler'),
          \   'on_exit': function('s:nvim_oneshot_handler')
          \ })
  endfunction

  function! completor#compat#job_stop(name, ...)
    return jobstop(a:name)
  endfunction

  function! completor#compat#job_status(job)
    try
      call jobpid(a:job)
      return 'run'
    catch /E900/
      return 'dead'
    endtry
  endfunction
else
  " vim8
  function! completor#compat#job_start_oneshot(cmd)
    return job_start(a:cmd, {
          \   'close_cb': function('s:vim_oneshot_handler'),
          \   'in_io': 'null',
          \   'err_io': 'out'
          \ })
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
endif
