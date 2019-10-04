" The completion popup window id.
let s:popup = -1
let s:current_completions = #{
      \ data: [],
      \ base: '',
      \ pos: -1,
      \ orig: '',
      \ startcol: -1,
      \ index: -1,
      \ }
let s:indicator = '__|-|__'


func s:next()
  let cur = s:current_completions.index
  if len(s:current_completions.data) == cur
    call cursor(1, col('.'))
    let s:current_completions.index = 1
  else
    if s:current_completions.index == 0
      let cur = 0
    endif
    call cursor(cur + 1, col('.'))
    let s:current_completions.index = cur + 1
  endif
  redraw
endfunc


func s:prev()
  let cur = s:current_completions.index
  if cur == 1
    call cursor(len(s:current_completions.data), col('.'))
    let s:current_completions.index = len(s:current_completions.data)
  else
    call cursor(cur - 1, col('.'))
    let s:current_completions.index = cur - 1
  endif
  redraw
endfunc


func s:hi_cursor()
  if s:current_completions.index == 0
    call popup_setoptions(s:popup, #{cursorline: 1})
  endif
endfunc


func s:filter(id, key)
  if a:key == "\<c-n>"
    call s:hi_cursor()
    call win_execute(a:id, "call s:next()")
    call s:insert_word(a:id)
    return 1
  elseif a:key == "\<c-p>"
    call s:hi_cursor()
    call win_execute(a:id, "call s:prev()")
    call s:insert_word(a:id)
    return 1
  elseif a:key == "\<c-e>"
    call s:reset()
    call completor#popup#hide()
    return 1
  elseif a:key == "\<c-y>"
    call completor#popup#hide()
    return 1
  endif
  return 0
endfunc


func s:reset()
  call setline('.', s:current_completions.orig)
  call cursor(line('.'), s:current_completions.pos + 1)
endfunc


func s:insert_word(id)
  let line = s:current_completions.index
  let item = s:current_completions.data[line-1]
  let text = s:current_completions.orig
  let startcol = s:current_completions.startcol
  if startcol == 0
    let pre = ''
  else
    let pre = text[:startcol-1]
  endif
  let pos = s:current_completions.pos
  let new = pre . item.word . text[pos:]
  call setline('.', new)
  call cursor(line('.'), startcol + strlen(item.word) + 1)
endfunc


func s:define_syntax()
  setlocal conceallevel=3
  setlocal concealcursor=ncvi
  exec 'syn region CompletionWord matchgroup=indicator start="^" end="' . s:indicator . '" concealends'
  hi link indicator NONE
  hi default CompletionWord gui=bold cterm=bold term=bold
endfunc


func completor#popup#init()
  let s:popup = popup_create('', #{
        \  zindex: 200,
        \  mapping: 0,
        \  wrap: 0,
        \  maxwidth: 80,
        \  hidden: v:true,
        \  filter: {id,key -> s:filter(id, key)},
        \ })
  call win_execute(s:popup, "call s:define_syntax()")
endfunc


func completor#popup#hide()
  call popup_setoptions(s:popup, #{cursorline: 0})
  call win_execute(s:popup, 'call cursor(1, col(".")) | redraw')
  call popup_hide(s:popup)
endfunc


let s:a = 0

func s:max_length(items)
  let c = 0
  for v in a:items
    if len(v.word) > c
      let c = len(v.word)
    endif
  endfor
  return c
endfunc


func s:format(v, max_word_length)
  return ' ' . a:v.word . s:indicator . repeat(' ', a:max_word_length-len(a:v.word)) . a:v.menu
endfunc


func completor#popup#show(startcol, words)
  let s:a += 1
  let text = getline('.')
  let pos = col('.') - 1
  let base = text[a:startcol:pos-1]
  let length = s:max_length(a:words) + 2
  let words = map(copy(a:words), {k,v -> s:format(v, length)})

  let s:current_completions.data = a:words
  let s:current_completions.startcol = a:startcol
  let s:current_completions.base = base
  let s:current_completions.pos = pos
  let s:current_completions.orig = text
  let s:current_completions.index = 0

  call popup_setoptions(s:popup, #{
        \ maxheight: &lines - line('.') - 5,
        \ line: 'cursor+1',
        \ col: 'cursor-'.(strlen(base)+1),
        \ })
  call popup_settext(s:popup, words)
  call popup_show(s:popup)
endfunc
