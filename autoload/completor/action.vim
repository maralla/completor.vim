let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}
let s:action = ''
let s:completions = []
let s:cot = ''
let s:freezed_status = {'pos': [], 'nr': -1, 'ft': ''}

let s:DOC_POSITION = {
      \ 'bottom': 'rightbelow',
      \ 'top': 'topleft',
      \ }


function! s:freezed_status.reset()
  let self.pos = []
  let self.nr = -1
  let self.ft = ''
endfunction


function! s:freezed_status.set(status)
  let self.pos = a:status.pos
  let self.nr = a:status.nr
  let self.ft = a:status.ft
endfunction


function! s:freezed_status.consistent()
  return self.pos == getcurpos() &&
        \ self.nr == bufnr('') &&
        \ self.ft == &ft
endfunction


function! s:status.update()
  let e = col('.') - 2
  let inputted = e >= 0 ? getline('.')[:e] : ''

  let self.pos = getcurpos()
  let self.input = inputted
  let self.nr = bufnr('')
  let self.ft = &ft
endfunction


function! s:reset()
  let s:completions = []
  call s:freezed_status.reset()
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
  let s:cot = &cot
  let &cot = get(g:, 'completor_complete_options', &cot)
endfunction


function! completor#action#_on_insert_leave()
  let &cot = s:cot
  let s:cot = ''
endfunction


function! s:trigger_complete(msg)
  let s:completions = completor#utils#on_data('complete', a:msg)
  if empty(s:completions) | return | endif
  let startcol = completor#action#completefunc(1, '')
  let matches = completor#action#completefunc(0, '')
  if startcol >= 0
    try
      call complete(startcol + 1, matches.words)
    catch /E785\|E685/
    endtry
  endif
endfunction


function! s:jump(items)
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
  let action = len(content) == 1 ? 'tjump' : 'tselect'
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


function! s:goto_definition(msg)
  let items = completor#utils#on_data('definition', a:msg)
  if len(items) > 0
    try
      call s:jump(items)
    catch /E37/
      echohl ErrorMsg
      echomsg '`hidden` should be set (set hidden)'
      echohl NONE
      return
    endtry
  endif
endfunction


function! s:call_signatures(msg)
  let items = completor#utils#on_data('signature', a:msg)

  hi def CompletorCallCurrentArg term=bold,underline cterm=bold,underline

  if empty(items)
    return
  endif
  let item = items[0]
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


function! s:open_doc_window()
  let n = bufnr('__doc__')
  let direction = get(s:DOC_POSITION, g:completor_doc_position, s:DOC_POSITION.bottom)
  if n > 0
    let i = index(tabpagebuflist(tabpagenr()), n)
    if i >= 0
      " Just jump to the doc window
      silent execute (i + 1).'wincmd w'
    else
      silent execute direction.' sbuffer '.n
    endif
  else
    silent execute direction.' split __doc__'
  endif
endfunction


function! s:show_doc(msg)
  let items = completor#utils#on_data('doc', a:msg)
  if empty(items)
    return
  endif
  let doc = split(items[0], "\n")
  if empty(doc)
    return
  endif
  call s:open_doc_window()

  setlocal modifiable noswapfile buftype=nofile
  silent normal! ggdG
  silent $put=doc
  silent normal! 1Gdd
  setlocal nomodifiable nomodified foldlevel=200
  nnoremap <buffer> q ZQ
endfunction


function! completor#action#callback(msg)
  if !s:freezed_status.consistent()
    let s:completions = []
    return
  endif
  call s:freezed_status.reset()

  if s:action ==# 'complete'
    call s:trigger_complete(a:msg)
  elseif s:action ==# 'definition'
    call s:goto_definition(a:msg)
  elseif s:action ==# 'signature'
    call s:call_signatures(a:msg)
  elseif s:action ==# 'doc'
    call s:show_doc(a:msg)
  elseif s:action ==# 'format'
    silent edit!
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
    let ret = {'words': s:completions}
    if g:completor_refresh_always
      let ret.refresh = 'always'
    endif
    return ret
  finally
    let s:completions = []
  endtry
endfunction


" :param info: must contain keys: 'cmd', 'ftype', 'is_sync', 'is_daemon'
function! completor#action#do(action, info, status)
  if empty(a:info)
    return
  endif

  call s:reset()
  let s:action = a:action
  let options = get(a:info, 'options', {})
  let input_content = get(a:info, 'input_content', '')

  if a:info.is_sync
    call s:freezed_status.set(a:status)
    call completor#action#callback(s:status.input)
  elseif !empty(a:info.cmd)
    if a:info.is_daemon
      if completor#daemon#process(a:action, a:info.cmd, a:info.ftype, options)
        call s:freezed_status.set(a:status)
      else
        call s:freezed_status.reset()
      endif
    else
      let sending_content = !empty(input_content)
      let s:job = completor#compat#job_start_oneshot(a:info.cmd, options, sending_content)
      if completor#compat#job_status(s:job) ==# 'run'
        call s:freezed_status.set(a:status)
      else
        call s:freezed_status.reset()
      endif
      if sending_content
        call completor#compat#job_send(s:job, input_content)
      endif
    endif
  endif
endfunction


function! completor#action#get_status()
  return s:status
endfunction


function! completor#action#update_status()
  call s:status.update()
endfunction
