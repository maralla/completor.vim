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


function! s:popup_select(items)
  let data = []

  for item in a:items
    let data = add(data, {
          \ 'content': item.name,
          \ 'file': item.filename,
          \ 'line': item.lnum,
          \ 'col': item.col,
          \ 'enable_confirm': v:true,
          \ 'ftype': &ft
          \ })
  endfor

  call completor#popup#select({'options': data})
endfunction


function! s:legacy_select(items, action)
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


function! s:select(items, action)
  if len(a:items) > 0
    try
      if completor#support_popup()
        call s:popup_select(a:items)
      else
        call s:legacy_select(a:items, a:action)
      endif
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



function! s:format(items)
  if empty(a:items) || empty(a:items[0]) || mode() != 'n'
    return
  endif

  pyx << EOF
END = 999999

lines = {}

items = vim.bindeval('a:items')[0]

chunks = []

l = 0
c = 0
for item in items:
  chunks.extend([{
    'start': (l, c),
    'end': (item['range']['start']['line'], item['range']['start']['character']),
    'insert': False
  }, {
    'start': (item['range']['start']['line'], item['range']['start']['character']),
    'end': (item['range']['end']['line'], item['range']['end']['character']),
    'insert': True
  }])

  l = item['range']['end']['line']
  c = item['range']['end']['character']

chunks.append({
  'start': (l, c),
  'end': (END, END),
  'insert': False
})

data = []

i = 0

for chunk in chunks:
  if chunk['insert']:
    data.append(items[i]['newText'].decode())
    i += 1
    continue

  lines = vim.current.buffer[chunk['start'][0]:chunk['end'][0]+1]
  if len(lines) == 1:
    line = lines[0][chunk['start'][1]:chunk['end'][1]]
  elif not lines:
    line = ''
  else:
    if len(lines) < chunk['end'][0] - chunk['start'][0] + 1:
      e = END
      last = ''
    else:
      e = -1
      last = '\n' + lines[-1][:chunk['end'][1]]

    between = lines[1:e]
    if between:
      between = '\n' + '\n'.join(between)
    else:
      between = ''
      # between = '\n'

    line = lines[0][chunk['start'][1]:] + between + last
    # if chunk['end'][1] == END:
    #   line += '\n'
  data.append(line)

pos = vim.current.window.cursor
vim.current.buffer[:] = ''.join(data).split('\n')
vim.current.window.cursor = pos
EOF

  :write
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

  let items = a:items
  let action = s:action
  let ft = 'markdown'
  let do_method = ''

  if type(a:items) == v:t_dict
    let items = a:items.data
    let action = get(a:items, 'action', action)
    let ft = get(a:items, 'ft', ft)
    let do_method = get(a:items, 'method', '')
  endif

  if action ==# 'complete'
    call s:trigger_complete(items)
  elseif action ==# 'select'
    call s:select(items, action)
  elseif action ==# 'definition' || action ==# 'implementation' || action ==# 'references'
    call s:select(items, action)
  elseif action ==# 'signature'
    call s:call_signatures(items)
  elseif action ==# 'doc'
    call s:show_doc(items)
  elseif action ==# 'rename'
    silent edit!
  elseif action ==# 'format'
    call s:format(items)
  elseif action ==# 'menu'
    if !empty(items)
      if completor#support_popup()
        call completor#popup#menu(s:action, items)
      else
        echo "popup window not supported"
      endif
    endif
  elseif action ==# 'view'
    if !empty(items)
      if completor#support_popup()
        call completor#popup#view(split(items[0], "\n"), ft)
      else
        echo "popup window not supported"
      endif
    endif
  elseif action ==# 'do'
    if empty(do_method)
      return
    endif
    let arg = ''
    if !empty(items)
      let arg = items[0]
    endif
    call completor#do(do_method, arg)
  elseif action ==# 'hover'
    if !empty(items)
      if completor#support_popup()
        call completor#popup#markdown_preview(split(items[0], "\n"))
      else
        echo items[0]
      endif
    endif
  endif

  let opt = get(a:items, 'opt', {})
  if !empty(opt) && has_key(opt, "after") && !empty(opt.after)
    call completor#do(opt.after)
  endif
endfunction


function! completor#action#stream(name, msg)
  call completor#utils#on_stream(a:name, s:action, a:msg)
endfunction


let s:popup_init = v:false

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

  if !s:popup_init && completor#support_popup()
    call completor#popup#init()
  endif

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
