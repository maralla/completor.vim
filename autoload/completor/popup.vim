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


let s:t_ve = &t_ve

let s:selector = -1
let s:selector_items = []
func completor#popup#select(items)
  if empty(a:items.options)
    return
  endif

  if len(a:items.options) == 1
    let item = a:items.options[0]
    if get(item, 'enable_confirm', v:false)
      call s:select_edit_file(item)
      return
    endif
  endif

  let s:selector_items = a:items

  let max = 0

  for item in a:items.options
    if len(item.content) > max
      let max = len(item.content)
    endif
  endfor

  let text = map(copy(a:items.options), {i, v -> s:gen_select_item(i, v, max)})

  set t_ve=

  if s:selector == -1
    hi default link CompletorSelect PmenuSel
    call prop_type_add('selecthi', #{highlight: 'CompletorSelect'})
    let s:selector = popup_create(text, #{
          \ zindex: 99999,
          \ mapping: v:false,
          \ filter: function('s:select_filter'),
          \ line: &lines,
          \ maxheight: 5,
          \ minheight: 5,
          \ minwidth: &columns - 10,
          \ maxwidth: &columns - 10,
          \ padding: [1, 1, 1, 1],
          \ border: [1, 1, 1, 1],
          \ borderchars: ['─', '│', '─', '│', '╭', '┐', '┘', '└'],
          \ scrollbar: 0,
          \ cursorline: 1,
          \ })
  else
    call popup_settext(s:selector, text)
    call popup_show(s:selector)
  endif

  call win_execute(s:selector, "normal! gg")
  let s:selector_current = 0

  call timer_start(0, {t -> feedkeys('a')})

  if has_key(s:selector_items, 'callback')
    call s:selector_items.callback(s:selector, "select", a:items.options[0])
  endif
endfunc


func s:gen_select_item(i, v, size)
  let item = (a:i+1) .. "\t" .. a:v.content .. repeat(' ', a:size - len(a:v.content))
  if has_key(a:v, 'file')
    let item ..= "\t" .. a:v.file .. ":" .. a:v.line
  endif
  return item
endfunc


func s:select_filter(id, key)
  if a:key == "\<DOWN>" || a:key == "\<C-j>"
    call win_execute(a:id, "normal! j")
    if s:selector_current + 1 < len(s:selector_items.options)
      let s:selector_current += 1
    endif

    let item = s:selector_items.options[s:selector_current]

    if has_key(s:selector_items, 'callback')
      call s:selector_items.callback(a:id, "select", item)
    endif
  elseif a:key == "\<UP>" || a:key == "\<C-k>"
    call win_execute(a:id, "normal! k")
    if s:selector_current - 1 >= 0
      let s:selector_current -= 1
    endif

    let item = s:selector_items.options[s:selector_current]

    if has_key(s:selector_items, 'callback')
      call s:selector_items.callback(a:id, "select", item)
    endif
  elseif a:key == "\<ESC>" || a:key == "q"
    call popup_hide(a:id)

    exe 'set t_ve='.s:t_ve

    if has_key(s:selector_items, 'callback')
      call s:selector_items.callback(a:id, "quit", {})
    endif
  elseif a:key == "\<CR>"
    let item = s:selector_items.options[s:selector_current]
    if has_key(s:selector_items, 'callback')
      call s:selector_items.callback(a:id, "confirm", item)
    endif
  endif

  return 1
endfunc


let s:selector_content = -1
func completor#popup#select_callback(id, type, item)
  if a:type == "select"
    if s:selector_content == -1
      let s:selector_content = popup_create('', #{
            \ zindex: 99999,
            \ mapping: 0,
            \ scrollbar: 0,
            \ line: 1,
            \ maxheight: &lines - 15,
            \ minheight: &lines - 15,
            \ minwidth: &columns - 10,
            \ maxwidth: &columns - 10,
            \ padding: [1, 1, 1, 1],
            \ border: [1, 1, 1, 1],
            \ borderchars: ['─', '│', '─', '│', '╭', '┐', '┘', '└'],
            \ })
    else
      call popup_show(s:selector_content)
    endif

    if has_key(a:item, 'file')
      let content = readfile(a:item.file)
      call popup_settext(s:selector_content, content)
      call win_execute(s:selector_content, "normal! "..a:item.line .. "Gzz")
      let nr = winbufnr(s:selector_content)

      call prop_add(a:item.line, 1, #{
            \ length: 99999, bufnr: nr, type: 'selecthi'})

      if has_key(a:item, 'ftype')
        call win_execute(s:selector_content, "set ft=" .. a:item.ftype)
      endif
    else
      call popup_settext(s:selector_content, a:item.content)
    endif
  elseif a:type == "confirm"
    if get(a:item, 'enable_confirm', v:false)
      call s:select_filter(s:selector, 'q')
      if has_key(a:item, 'file')
        call s:select_edit_file(a:item)
      endif
    endif
  elseif a:type == "quit"
    call popup_hide(s:selector_content)
  endif
endfunc


func s:select_edit_file(item)
  exe ':edit ' .. a:item.file
  if has_key(a:item, 'line')
    exe ':' .. string(a:item.line)
    exe 'normal! 0' .. string(a:item.col-1) .. 'lzz'
  endif
endfunc


func completor#popup#markdown_preview(content)
  let max = 0

  for item in a:content
    if len(item) > max
      let max = len(item)
    endif
  endfor

  let p = popup_create(a:content, #{
        \ moved: 'word',
        \ mapping: v:false,
        \ minwidth: max,
        \ maxwidth: max,
        \ pos: 'botleft',
        \ line: 'cursor-1',
        \ col: 'cursor',
        \ zindex: 9999,
        \ filter: function('s:scroll_filter'),
        \ padding: [1, 2, 1, 2],
        \ })
  call win_execute(p, 'set ft=markdown')

  call timer_start(0, {t -> feedkeys("\<C-j>")})
endfunc


func s:scroll_filter(id, key)
  if a:key == "\<DOWN>" || a:key == "\<C-j>"
    call win_execute(a:id, "normal! \<C-d>")
    return 1
  elseif a:key == "\<UP>" || a:key == "\<C-k>"
    call win_execute(a:id, "normal! \<C-u>")
    return 1
  elseif a:key == "\<ESC>"
    call popup_close(a:id)
    return 1
  endif

  return 0
endfunc
