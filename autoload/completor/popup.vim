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
  setlocal scrolloff=0
  setlocal scrolljump=1
  setlocal conceallevel=3
  setlocal concealcursor=ncvi
  exec 'syn region CompletionWord matchgroup=indicator start="^" end="' . s:indicator . '" concealends'
  hi link indicator NONE
  hi default CompletionWord gui=bold cterm=bold term=bold
endfunc


func completor#popup#init()
  let s:popup = popup_create('', #{
        \  zindex: 200,
        \  mapping: 1,
        \  wrap: 0,
        \  maxwidth: 80,
        \  hidden: v:true,
        \  filter: {id,key -> s:filter(id, key)},
        \ })
  call win_execute(s:popup, "call s:define_syntax()")
endfunc


func completor#popup#hide()
  call popup_setoptions(s:popup, #{cursorline: 0})
  call popup_hide(s:popup)
  call win_execute(s:popup, 'call cursor(1, col(".")) | redraw')
endfunc


func s:get_word(item)
  let word = a:item.word
  let abbr = get(a:item, 'abbr', '')
  if abbr != ''
    let word = abbr
  endif
  return word
endfunc


func s:max_word_length(items)
  let c = 0
  for v in a:items
    let word = s:get_word(v)
    if len(word) > c
      let c = len(word)
    endif
  endfor
  return c
endfunc


func s:format(v, max_length)
  let word = s:get_word(a:v)
  let menu = get(a:v, 'menu', '')
  return ' ' . word . s:indicator . repeat(' ', a:max_length-len(word)) . menu
endfunc


func s:format_items(words)
  let length = s:max_word_length(a:words) + 2
  let ret = []
  let item_length = 0
  for word in a:words
    let item = s:format(word, length)
    if len(item) > item_length
      let item_length = len(item)
    endif
    call add(ret, item)
  endfor
  return [ret, item_length]
endfunc


func completor#popup#show(startcol, words)
  let text = getline('.')
  let pos = col('.') - 1
  let base = text[a:startcol:pos-1]
  let length = s:max_word_length(a:words) + 2
  let [words, max_length] = s:format_items(a:words)

  let s:current_completions.data = a:words
  let s:current_completions.startcol = a:startcol
  let s:current_completions.base = base
  let s:current_completions.pos = pos
  let s:current_completions.orig = text
  let s:current_completions.index = 0

  let total = &lines
  let current = screenrow()

  let pos = 'topleft'
  let height = min([total - current - 1, 50])
  let line = 'cursor+1'
  if current > total / 2
    let pos = 'botleft'
    let height = min([current - 1, 50])
    let line = 'cursor-1'
  endif

  call popup_setoptions(s:popup, #{
        \ pos: pos,
        \ maxheight: height,
        \ minwidth: min([max_length, 80]),
        \ fixed: v:true,
        \ line: line,
        \ col: 'cursor-'.(strlen(base)+1),
        \ })
  call popup_settext(s:popup, words)
  call popup_show(s:popup)
endfunc
