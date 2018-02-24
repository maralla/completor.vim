let s:status = {'pos': [], 'nr': -1, 'input': '', 'ft': ''}
let s:action = ''
let s:completions = []

let s:DOC_POSITION = {
      \ 'bottom': 'rightbelow',
      \ 'top': 'topleft',
      \ }


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


function! s:trigger_complete(msg)
  if !s:status.consistent()
    let s:completions = []
  else
    let s:completions = completor#utils#on_data('complete', a:msg)
  endif
  if empty(s:completions) | return | endif
  setlocal completefunc=completor#action#completefunc
  call feedkeys("\<Plug>CompletorTrigger")
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

  call writefile(content, tmp)
  let tags = &tags
  let wildignore = &wildignore
  let action = len(content) == 1 ? 'tjump' : 'tselect'
  try
    set wildignore=
    let &tags = tmp
    exe action . ' ' . name
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
  if s:action ==# 'complete'
    call s:trigger_complete(a:msg)
  elseif s:action ==# 'definition'
    call s:goto_definition(a:msg)
  elseif s:action ==# 'signature'
    call s:call_signatures(a:msg)
  elseif s:action ==# 'doc'
    call s:show_doc(a:msg)
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


function! completor#action#do(action, info)
  if empty(a:info) || !s:status.consistent() | return | endif
  call s:reset()
  let s:action = a:action
  if a:info.is_sync
    call completor#action#callback(s:status.input)
  elseif !empty(a:info.cmd)
    let l:cwd = get(a:info, 'cwd', getcwd())
    if a:info.is_daemon
      call completor#daemon#process(a:action, a:info.cmd, l:cwd, a:info.ftype)
    else
      let s:job = completor#compat#job_start_oneshot(a:info.cmd, l:cwd)
    endif
  endif
endfunction


function! completor#action#get_status()
  return s:status
endfunction


function! completor#action#update_status()
  call s:status.update()
endfunction
