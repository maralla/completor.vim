let s:inited = v:false

func s:init_props()
  hi default completorPromptCursorPosition guibg=#3A484C ctermbg=238
  hi default completorPrompt guibg=NONE ctermbg=NONE
  hi default completorPromptBorder guifg=#404D4F guibg=NONE ctermfg=238 ctermbg=NONE

  call prop_type_add('completor_prompt_cursor', #{highlight: 'completorPromptCursorPosition'})
  call prop_type_add('completor_prompt_word', #{highlight: 'Search'})
endfunc


let s:prompt_popup_pos = 1
func s:prompt_popup_forward(max)
  if s:prompt_popup_pos < a:max
    let s:prompt_popup_pos += 1
  endif
endfunc

func s:prompt_popup_backward(n)
  if s:prompt_popup_pos > a:n
    let s:prompt_popup_pos -= a:n
  endif
endfunc

func s:prompt_popup_insert(text, key)
  let end = s:prompt_popup_pos - 2
  if end < 0
    let prefix = ''
  else
    let prefix = a:text[:end]
  endif
  return prefix . a:key . a:text[s:prompt_popup_pos-1:]
endfunc

func s:prompt_popup_delete(text)
  let p = s:prompt_popup_pos - 2
  if p < 0
    return a:text
  endif
  if p == 0
    let prefix = ''
  else
    let prefix = a:text[:p-1]
  endif
  return prefix . a:text[p+1:]
endfunc


func s:prompt_popup_delete_word(text)
  let p = s:prompt_popup_pos - 2
  if p < 0
    return [a:text, 0]
  endif

  let text = a:text[:p]

  let parts = split(text)
  if len(parts) <= 1
    let prefix = ''
    let backs = s:prompt_popup_pos - 1
  else
    let backs = strlen(parts[-1])

    let prefix = text[:-backs-1]
  endif

  return [prefix . a:text[p+1:], backs]
endfunc


func s:prompt_filter(id, key, opt)
  let nr = winbufnr(a:id)
  let content = getbufline(nr, 1)
  if len(content) <= 0
    let text = ''
  else
    let text = content[0]
  endif
  let move = v:false
  if a:key == "\<BS>"
    let text = s:prompt_popup_delete(text)
    call s:prompt_popup_backward(1)
  elseif a:key == "\<C-w>"
    let [text, backs] = s:prompt_popup_delete_word(text)
    call s:prompt_popup_backward(backs)
  elseif a:key == "\x80PS" || a:key == "\x80PE"
    " Remove bracketed-paste characters. :h t_PE
    return 1
  elseif a:key == "\<ESC>"
    call s:prompt_popup_close(a:opt)
    return 1
  elseif a:key == "\<CR>"
    if has_key(a:opt, 'on_commit')
      call a:opt.on_commit(text)
    endif
    if get(a:opt, "close_on_commit", v:false)
      call s:prompt_popup_close(a:opt)
    endif
    return 1
  elseif a:key == "\<LEFT>" || a:key == "\<C-h>"
    call s:prompt_popup_do(a:id, "normal! h")
    call s:prompt_popup_backward(1)
    let move = v:true
  elseif a:key == "\<RIGHT>" || a:key == "\<C-l>"
    call s:prompt_popup_do(a:id, "normal! l")
    call s:prompt_popup_forward(strlen(text))
    let move = v:true
  elseif a:key !~ '\p'
    return 1
  else
    let text = s:prompt_popup_insert(text, a:key)
    call s:prompt_popup_forward(strlen(text))
  endif
  call prop_remove(#{id: s:prop_id_cursor, bufnr: nr, all: v:true}, 1)
  if !move
    call setbufline(nr, 1, text)
  endif
  call prop_add(1, s:prompt_popup_pos, #{
        \ length: 1,
        \ bufnr: nr,
        \ id: s:prop_id_cursor,
        \ type: 'completor_prompt_cursor'
        \ })
  return 1
endfunc

func s:prompt_popup_close(opt)
  if s:prompt_popup != -1
    call popup_close(s:prompt_popup)
    let s:prompt_popup = -1
  endif
  set cursorline
  exe 'set t_ve='.s:t_ve

  if has_key(a:opt, "on_close")
    call a:opt.on_close(a:opt)
  endif
endfunc


func s:prompt_popup_do(id, cmd)
  call win_execute(a:id, a:cmd)
endfunc


let s:prop_id_cursor = 1
let s:prop_id_rename_word_highlight = 2

let s:t_ve = &t_ve

let s:last_winnr = -1
let s:prompt_popup = -1
let s:inited = v:false
func completor#prompt#create(opt)
  if !s:inited
    call s:init_props()
    let s:inited = v:true
  endif
  let s:last_winnr = winnr()
  " set nocursorline
  set t_ve=
  let s:prompt_popup = popup_create(' ', #{
        \ line: 'cursor+1',
        \ col: 'cursor',
        \ padding: [0, 1, 0, 1],
        \ minheight: 1,
        \ maxheight: 1,
        \ minwidth: 14,
        \ mapping: v:false,
        \ highlight: 'completorPrompt',
        \ border: [1, 1, 1, 1],
        \ borderchars: ['─', '│', '─', '│', '┌', '┐', '┘', '└'],
        \ borderhighlight: ['completorPromptBorder'],
        \ filter: {id, key -> s:prompt_filter(id, key, a:opt)},
        \ callback: {id, result -> s:prompt_callback(id, result, a:opt)}
        \ })

  let nr = winbufnr(s:prompt_popup)
  let s:prompt_popup_pos = 1
  call prop_add(1, s:prompt_popup_pos, #{
        \ length: 1,
        \ bufnr: nr,
        \ id: s:prop_id_cursor,
        \ type: 'completor_prompt_cursor',
        \ })

  if has_key(a:opt, 'on_start')
    call a:opt.on_start(a:opt)
  endif
endfunc


func s:prompt_callback(id, result, opt)
  if a:result == -1
    call s:prompt_popup_close(a:opt)
  endif
endfunc


func s:on_rename_start(opt)
  let word = a:opt.word
  let start = a:opt.start

  call prop_add(a:opt.line, start, #{
        \ length: strlen(word),
        \ id: s:prop_id_rename_word_highlight,
        \ bufnr: a:opt.bufnr,
        \ type: 'completor_prompt_word',
        \ })
endfunc


func s:on_rename_close(opt)
  call prop_remove(#{id: s:prop_id_rename_word_highlight, bufnr: a:opt.bufnr, all: v:true})
endfunc


func s:on_rename_commit(text)
  call completor#do('rename', trim(a:text))
endfunc


func completor#prompt#rename()
  let word = expand('<cword>')
  if empty(word)
    return
  endif

  let start = strridx(getline('.'), word, col('.') - 1)+1
  if start <= 0
    return
  endif

  call completor#prompt#create(#{
        \ on_start: function('s:on_rename_start'),
        \ on_close: function('s:on_rename_close'),
        \ on_commit: function('s:on_rename_commit'),
        \ line: line('.'),
        \ word: word,
        \ start: start,
        \ bufnr: bufnr(''),
        \ close_on_commit: v:true,
        \ })
endfunc
