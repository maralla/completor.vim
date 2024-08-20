" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:python_imported = v:false
let s:prev = []
let s:inputted = v:false


function! s:import_python()
  if !s:python_imported
    call completor#utils#setup_python()
    let s:python_imported = v:true
  endif
endfunction


function! s:skip()
  let buftype = &buftype
  let name = bufname('')
  let fsize = getfsize(name)
  let skip = buftype ==? 'quickfix'
        \ || name ==? '[Command Line]'
        \ || fsize == -2
        \ || fsize > g:completor_filesize_limit
        \ || index(g:completor_blacklist, &ft) != -1
        \ || &paste
        \ || mode() !=# 'i'
  if exists('g:completor_whitelist') && type(g:completor_whitelist) == v:t_list
    let skip = skip || index(g:completor_whitelist, &ft) == -1
  endif
  return skip || get(b:, 'completor_disabled', v:false)
endfunction


function! s:key_ignore(pos)
  if a:pos[:1] != s:prev[:1]
    return v:false
  endif
  return !s:inputted
endfunction


function! s:on_text_change()
  let pos = getcurpos()
  if !s:skip() && (completor#support_popup() || !s:key_ignore(pos))
    call completor#do('complete')
  endif
  let s:prev = pos
endfunction


function! s:on_insert_char_pre()
  if pumvisible()
    let pos = getcurpos()
    let s:prev = pos
    let s:prev[2] += 1
  endif
  let s:inputted = v:true
  call timer_start(0, {t->s:clear_inputted()})
endfunction


function! s:clear_inputted()
  let s:inputted = v:false
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    if get(g:, 'completor_auto_trigger', 1)
      autocmd TextChangedI * call s:on_text_change()
      autocmd InsertCharPre * call s:on_insert_char_pre()
    endif
    if get(g:, 'completor_auto_close_doc', 1)
      autocmd! CompleteDone * call completor#action#_on_complete_done()
    endif
    autocmd InsertEnter * call completor#action#_on_insert_enter()
    autocmd InsertLeave * call completor#action#_on_insert_leave()
  augroup END
endfunction


function! completor#disable_autocomplete()
  autocmd! completor
endfunction


func! completor#disable_text_change()
  if completor#support_popup()
    call completor#popup#disable_popup_hide()
  endif
endfunc


func! completor#enable_text_change()
  if completor#support_popup()
    call completor#popup#enable_popup_hide()
  endif
endfunc


function! completor#enable_autocomplete()
  if &diff
    return
  endif
  call s:set_events()
endfunction


func s:do_action(action, meta, status, args)
  try
    call s:import_python()
    if a:action ==# 'complete'
      let info = completor#utils#get_completer(a:status.ft, a:status.input)
    else
      let info = completor#utils#load(a:status.ft, a:action, a:status.input, a:meta)
    endif
    call completor#action#do(a:action, info, a:status, a:args)
  catch /\(E858\|\(py\(thon\|3\|x\)\)\)/
  endtry
endfunction


function! completor#do(action, ...) range
  if exists('s:timer') && !empty(timer_info(s:timer))
    call timer_stop(s:timer)
  endif

  if type(a:action) == v:t_list
    if empty(a:action)
      return
    endif

    let action = a:action[0]
    let args = a:action[1:]
  else
    let action = a:action
    let args = a:000
  endif

  let start_col = 0
  let end_col = 0

  if mode() ==# 'v'
    let start_col = col("'<")
    let end_col = col("'>")
  endif

  if start_col == 0
    let start_col = col('.')
  endif

  if end_col == 0
    let end_col = col('.')
  endif

  let meta = {
        \ 'range': [a:firstline, a:lastline],
        \ 'text_range': {
        \    'start': {'line': a:firstline-1, 'col': start_col-1},
        \    'end':   {'line': a:lastline-1,  'col': end_col-1}
        \  }
        \ }
  let status = completor#action#current_status()

  if !empty(args) && type(args[-1]) == v:t_dict
    let args[-1]['meta'] = meta
  else
    let args = args + [{'meta': meta}]
  endif

  let s:timer = timer_start(g:completor_completion_delay, {t->s:do_action(action, meta, status, args)})
  return ''
endfunction


function! completor#support_popup()
  return g:completor_use_popup_window
        \ && exists('*popup_create')
        \ && has('conceal')
        \ && has('textprop')
endfunction


let &cpo = s:save_cpo
unlet s:save_cpo
