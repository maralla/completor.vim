let s:freezed_status = {'pos': [], 'nr': -1, 'ft': '', 'mode': ''}
let s:action = ''
let s:completions = []

let s:DOC_POSITION = {
      \ 'bottom': 'rightbelow',
      \ 'top': 'topleft',
      \ }


function! s:reset()
  let s:completions = []
  if exists('s:job') && completor#compat#job_status(s:job) ==# 'run'
    call completor#compat#job_stop(s:job)
  endif
endfunction


function! completor#action#_on_complete_done()
  if pumvisible() == 0
    try
      pclose
    catch
    endtry
  endif
endfunction


function! completor#action#_on_insert_enter()
  if completor#support_popup()
    return
  endif
  if !exists('s:cot')
    " Record cot.
    let s:cot = &cot
  endif
  let &cot = get(g:, 'completor_complete_options', &cot)
endfunction


function! completor#action#_on_insert_leave()
  if completor#support_popup()
    call completor#popup#hide()
    return
  endif
  if exists('s:cot')
    " Restore cot.
    let &cot = s:cot
  endif
endfunction


function! s:trigger_complete(completions)
  let s:completions = a:completions
  if empty(s:completions)
    if completor#support_popup()
      call completor#popup#hide()
    endif
    return
  endif
  try
    if completor#support_popup()
      call completor#popup#show(s:completions)
    else
      let startcol = s:completions[0].offset
      try
        call complete(startcol + 1, s:completions)
      catch /E785\|E685/
      endtry
    endif
  finally
    let s:completions = []
  endtry
endfunction


function! s:jump(items, action)
  let tmp = tempname()
  let name = ''
  let content = []
  for item in a:items
    if !has_key(item, 'filename')
      continue
    endif
    if empty(name)
      let name = item.name
    endif
    let spec = printf('call cursor(%d, %d)', item.lnum, item.col)
    let tag = item.name."\t".item.filename."\t".spec
    call add(content, tag)
  endfor
  if empty(name)
    return
  endif

  " Split window if the target is not the current file.
  if item.filename != fnamemodify(expand('%'), ':p')
    if g:completor_def_split ==? 'split'
      split
    elseif g:completor_def_split ==? 'vsplit'
      vsplit
    elseif g:completor_def_split ==? 'tab'
      tab split
    endif
  endif

  call writefile(content, tmp)
  let tags = &tags
  let wildignore = &wildignore

  if len(content) == 1 && a:action ==# 'definition'
    let action = 'tjump'
  else
    let action = 'tselect'
  endif

  try
    set wildignore=
    let &tags = tmp
    try
      exe action . ' ' . escape(name, '"')
    catch /E426/
      return
    endtry
    redraw
  finally
    let &tags = tags
    let &wildignore = wildignore
  endtry
endfunction


function! s:goto_definition(items, action)
  if len(a:items) > 0
    try
      call s:jump(a:items, a:action)
    catch /E37/
      echohl ErrorMsg
      echomsg '`hidden` should be set (set hidden)'
      echohl NONE
      return
    endtry
  endif
endfunction


function! s:call_signatures(items)
  hi def CompletorCallCurrentArg term=bold,underline cterm=bold,underline

  if empty(a:items)
    return
  endif
  let item = a:items[0]
  if !empty(item.params)
    let prefix = item.index == 0 ? [] : item.params[:item.index - 1]
    let suffix = item.params[item.index + 1:]
    let current = item.params[item.index]
  else
    let [prefix, suffix] = [[], []]
    let current = ''
  endif
  echohl Function | echon item.func | echohl None
  echon '(' join(prefix, ', ')
  if !empty(prefix)
    echon ', '
  endif
  echohl CompletorCallCurrentArg | echon current | echohl None
  if !empty(suffix)
    echon ', '
  endif
  echon join(suffix, ', ') ')'
endfunction


function! s:show_doc(items)
  if empty(a:items)
    return
  endif
  let doc = split(a:items[0], "\n")
  if empty(doc)
    return
  endif

  let direction = get(s:DOC_POSITION, g:completor_doc_position, s:DOC_POSITION.bottom)
  let height = min([len(doc), &previewheight])
  silent execute direction.' pedit +resize'.height.' __doc__'

  wincmd P
  setlocal modifiable noreadonly
  silent normal! ggdG
  silent $put=doc
  silent normal! 1Gdd
  setlocal nomodifiable nomodified readonly
  setlocal noswapfile buftype=nofile nobuflisted bufhidden=wipe
  setlocal foldlevel=200
  nnoremap <buffer> q ZQ
  wincmd p
endfunction


function! s:is_status_consistent()
  return s:freezed_status.pos == getcurpos() &&
        \ s:freezed_status.nr == bufnr('') &&
        \ s:freezed_status.ft == &ft &&
        \ s:freezed_status.mode == mode()
endfunction


function! completor#action#callback(msg)
  let items = completor#utils#on_data(s:action, a:msg)
  call completor#action#trigger(items)
endfunction


function! completor#action#trigger(items)
  if !s:is_status_consistent()
    let s:completions = []
    return
  endif
  if s:action ==# 'complete'
    call s:trigger_complete(a:items)
  elseif s:action ==# 'definition' || s:action ==# 'implementation' || s:action ==# 'references'
    call s:goto_definition(a:items, s:action)
  elseif s:action ==# 'signature'
    call s:call_signatures(a:items)
  elseif s:action ==# 'doc'
    call s:show_doc(a:items)
  elseif s:action ==# 'format'
    silent edit!
  elseif s:action ==# 'hover'
    if !empty(a:items)
      if completor#support_popup()
        let p = popup_create(split(a:items[0], "\n"), #{
              \ moved: 'word',
              \ pos: 'botleft',
              \ line: 'cursor-1',
              \ col: 'cursor',
              \ zindex: 9999,
              \ padding: [1, 2, 1, 2],
              \ })
        call win_execute(p, 'set ft=markdown')
      else
        echo a:items[0]
      endif
    endif
  endif
endfunction


function! completor#action#stream(name, msg)
  call completor#utils#on_stream(a:name, s:action, a:msg)
endfunction


" :param info: must contain keys: 'cmd', 'ftype', 'is_sync', 'is_daemon'
function! completor#action#do(action, info, status, args)
  let s:freezed_status = a:status

  if empty(a:info)
    return v:false
  endif

  call s:reset()
  let s:action = a:action
  let options = get(a:info, 'options', {})
  let input_content = get(a:info, 'input_content', '')

  if a:info.is_sync
    call completor#action#callback(a:status.input)
    return v:true
  elseif !empty(a:info.cmd)
    if a:info.is_daemon
      return completor#daemon#process(a:action, a:info.cmd, a:info.ftype, options, a:args)
    endif
    let sending_content = !empty(input_content)
    let s:job = completor#compat#job_start_oneshot(a:info.cmd, options, sending_content)
    if completor#compat#job_status(s:job) ==# 'run'
      if sending_content
        call completor#compat#job_send(s:job, input_content)
      endif
      return v:true
    endif
  endif
  return v:false
endfunction


function! completor#action#current_status()
  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''
  return {
        \ 'pos': getcurpos(),
        \ 'input': inputted,
        \ 'nr': bufnr(''),
        \ 'ft': &ft,
        \ 'mode': mode(),
        \ }
endfunction
