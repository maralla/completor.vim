" The completion popup window id.
let s:popup = -1
let s:current_completions = #{
      \ data: [],
      \ pos: -1,
      \ orig: '',
      \ startcol: -1,
      \ index: -1,
      \ }
let s:visible = v:false
let s:disable_hide = v:false
let s:max_width = 80


func! s:next()
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


func! s:prev()
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


func! s:hi_cursor()
  if s:current_completions.index == 0
    call popup_setoptions(s:popup, #{cursorline: 1})
  endif
endfunc


func! s:filter(id, key)
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


func! s:callback(word)
  let b:completor_current_complete_word = a:word
  doautocmd <nomodeline> completor_event User
endfunc


func! s:reset()
  call setline('.', s:current_completions.orig)
  call cursor(line('.'), s:current_completions.pos + 1)
endfunc


func! s:insert_word(id)
  let line = s:current_completions.index
  let item = s:current_completions.data[line-1]
  let text = s:current_completions.orig
  let startcol = item.offset
  if startcol == 0
    let pre = ''
  else
    let pre = strpart(text, 0, startcol)
  endif
  let pos = s:current_completions.pos
  let new = pre . item.word . strpart(text, pos)
  call setline('.', new)
  let idx = startcol + strlen(item.word)
  call cursor(line('.'), idx + 1)

  call s:callback(item.word)
endfunc


func! s:define_syntax()
  setlocal scrolloff=0
  setlocal scrolljump=1
endfunc


func! s:init_popup()
  let s:popup = popup_create('', #{
        \  zindex: 200,
        \  mapping: 1,
        \  wrap: 0,
        \  maxwidth: s:max_width,
        \  hidden: v:true,
        \  filter: function('s:filter'),
        \ })
  call win_execute(s:popup, "call s:define_syntax()")
endfunc


func! completor#popup#init()
  call s:init_popup()
  augroup completor_popup
    autocmd!
    autocmd TextChangedI * call s:on_text_change()
  augroup END
  hi default CompletionWord gui=bold cterm=bold term=bold
  call prop_type_add('compword', #{highlight: 'CompletionWord'})
endfunc


func! s:on_text_change()
  call completor#popup#hide()
endfunc


func! completor#popup#disable_popup_hide()
  let s:disable_hide = v:true
endfunc


func! completor#popup#enable_popup_hide()
  let s:disable_hide = v:false
endfunc


func! completor#popup#hide()
  if !s:visible || s:disable_hide
    return
  endif
  if exists(':DoMatchParen')
    :DoMatchParen
  endif
  call popup_setoptions(s:popup, #{cursorline: 0})
  call popup_hide(s:popup)
  call win_execute(s:popup, 'call cursor(1, col(".")) | redraw')
  let s:visible = v:false
endfunc


func! completor#popup#safe_hide()
  if completor#support_popup()
    call completor#popup#hide()
  endif
endfunc



func! s:get_word(item)
  let word = a:item.word
  let abbr = get(a:item, 'abbr', '')
  if abbr != ''
    let word = abbr
  endif
  return word
endfunc


func! s:max_word_length(items)
  let c = 0
  for v in a:items
    let width = strdisplaywidth(s:get_word(v))
    if width > c
      let c = width
    endif
  endfor
  return c
endfunc


func! s:format(v, max_length)
  let word = s:get_word(a:v)
  let menu = get(a:v, 'menu', '')
  return ' ' . word . repeat(' ', a:max_length-strdisplaywidth(word)) . menu . ' '
endfunc


func! s:format_items(words)
  let length = s:max_word_length(a:words) + 2
  let ret = []
  let item_length = 0
  for word in a:words
    let item = s:format(word, length)
    let w = strdisplaywidth(item)
    if w > item_length
      let item_length = w
    endif
    call add(ret, item)
  endfor
  return [ret, item_length]
endfunc


func! s:apply_prop(words)
  let nr = winbufnr(s:popup)
  for i in range(1, len(a:words))
    call prop_add(i, 2, #{
          \ length: strlen(s:get_word(a:words[i-1])),
          \ bufnr: nr,
          \ type: 'compword',
          \ })
  endfor
endfunc


func! completor#popup#show(words)
  if empty(a:words)
    return
  endif
  let colpos = col('.') - 1
  let text = getline('.')

  let s:current_completions.data = a:words
  let s:current_completions.pos = colpos
  let s:current_completions.orig = text
  let s:current_completions.index = 0

  let startcol = a:words[0].offset
  let base = strpart(text, startcol, colpos-startcol)
  let length = s:max_word_length(a:words) + 2
  let [words, max_length] = s:format_items(a:words)

  let total = &lines
  let current = screenrow()

  let pos = 'topleft'
  let height = min([total - current - 1, 50])
  let line = 'cursor+1'
  if current > total / 2 && (total - current) < len(words)
    let pos = 'botleft'
    let height = min([current - 1, 50])
    let line = 'cursor-1'
  endif

  let width = min([max_length, s:max_width])

  let basewidth = strdisplaywidth(base)
  let col = 'cursor-1'
  if basewidth > 0
    let basewidth += 1
    let col = 'cursor-'.basewidth
  endif

  if winbufnr(s:popup) == -1
    call s:init_popup()
  endif

  call popup_setoptions(s:popup, #{
        \ pos: pos,
        \ maxheight: height,
        \ minwidth: width,
        \ fixed: v:true,
        \ line: line,
        \ col: col,
        \ })
  call popup_settext(s:popup, words)
  call s:apply_prop(a:words)
  call popup_show(s:popup)
  let s:visible = v:true
  if exists(':NoMatchParen')
    :NoMatchParen
  endif
endfunc
