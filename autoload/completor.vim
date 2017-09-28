" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

let s:char_inserted = v:false
let s:python_imported = v:false


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
  return skip || !s:char_inserted
endfunction


function! s:complete(...)
  call completor#do('complete')
endfunction


function! s:on_text_change()
  if s:skip() | return | endif
  let s:char_inserted = v:false

  if !get(g:, 'completor_auto_trigger', 1)
    return
  endif

  if exists('s:timer')
    call timer_stop(s:timer)
  endif
  let s:timer = timer_start(g:completor_completion_delay, function('s:complete'))
endfunction


function s:on_insert_char_pre()
  let s:char_inserted = v:true
endfunction


function! s:set_events()
  augroup completor
    autocmd!
    autocmd TextChangedI * call s:on_text_change()
    autocmd InsertCharPre * call s:on_insert_char_pre()
    if get(g:, 'completor_auto_close_doc', 1)
      autocmd! CompleteDone * if pumvisible() == 0 | pclose | endif
    endif
  augroup END
  if get(g:, 'completor_set_options', 1)
    set completeopt-=longest
    set completeopt+=menuone
    set completeopt-=menu
    if &completeopt !~# 'noinsert\|noselect'
      set completeopt+=noselect
    endif
  endif
endfunction


function! completor#disable()
  autocmd! completor
endfunction


function! completor#enable()
  if &diff
    return
  endif
  noremap  <silent> <Plug>CompletorTrigger <nop>
  inoremap <silent> <Plug>CompletorTrigger <c-x><c-u><c-p>
  call s:set_events()
endfunction


function! completor#do(action)
  call s:import_python()
  call completor#action#update_status()

  let status = completor#action#get_status()

  if a:action ==# 'complete'
    let info = completor#utils#get_completer(status.ft, status.input)
  else
    let info = completor#utils#load(status.ft, a:action, status.input)
  endif
  call completor#action#do(a:action, info)
  return ''
endfunction


let &cpo = s:save_cpo
unlet s:save_cpo
