let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}
let s:action = ''
let s:completions = []


function! s:status.update()
  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''

  let self.pos = getcurpos()
  let self.input = inputted
  let self.nr = bufnr('')
  let self.ft = &ft
endfunction


function! s:status.consistent()
  return self.pos == getcurpos() && self.nr == bufnr('') && self.ft == &ft
endfunction


function! s:reset()
  let s:completions = []
  if exists('s:job') && completor#compat#job_status(s:job) ==# 'run'
    call completor#compat#job_stop(s:job)
  endif
endfunction


function! s:complete(...)
  let info = completor#utils#get_completer(s:status.ft, s:status.input)
  call completor#action#do('complete', info)
endfunction


function! s:trigger_complete(msg)
  let is_empty = v:false
  if !s:status.consistent()
    let s:completions = []
    let is_empty = v:true
  else
    let s:completions = completor#utils#on_data('complete', a:msg)
    if empty(s:completions)
      let is_empty = v:true
      call completor#utils#retrigger()
    endif
  endif
  if is_empty | return | endif

  setlocal completefunc=completor#action#completefunc
  setlocal completeopt-=longest
  if get(g:, 'completor_auto_trigger', 1)
    call feedkeys("\<Plug>CompletorTrigger")
  endif
endfunction


function! s:goto_definition(msg)
  let items = completor#utils#on_data('definition', a:msg)
  if len(items) > 0
    let item = items[0]
    if has_key(item, 'filename')
      if expand('%:p') !=# item['filename']
        exe 'edit '.item['filename']
      endif
      call cursor(item['lnum'], item['col'])
    else
      echo item['text']
    endif
  endif
endfunction


function! completor#action#completefunc(findstart, base)
  if a:findstart
    if empty(s:completions)
      return -2
    endif
    return completor#utils#get_start_column()
  endif
  try
    return {'words': s:completions, 'refresh': 'always'}
  finally
    let s:completions = []
  endtry
endfunction


function! completor#action#callback(msg)
  if s:action ==# 'complete'
    call s:trigger_complete(a:msg)
  elseif s:action ==# 'definition'
    call s:goto_definition(a:msg)
  endif
endfunction


function! completor#action#do(action, info)
  if empty(a:info) || !s:status.consistent() | return | endif
  call s:reset()
  let s:action = a:action
  if a:info.is_sync
    call completor#action#callback(s:status.input)
  elseif !empty(a:info.cmd)
    if a:info.is_daemon
      call completor#daemon#process(a:action, a:info.cmd, a:info.ftype)
    else
      let s:job = completor#compat#job_start_oneshot(a:info.cmd)
    endif
  endif
endfunction


function! completor#action#complete()
  if exists('s:timer')
    call timer_stop(s:timer)
  endif
  call s:status.update()
  let s:timer = timer_start(g:completor_completion_delay, function('s:complete'))
endfunction


function! completor#action#goto_definition()
  call completor#import_python()
  call s:status.update()

  let info = completor#utils#load(&ft, 'definition', s:status.input)
  call completor#action#do('definition', info)
endfunction
