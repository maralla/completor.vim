let s:pat = '<#[^#]\+#>'

function! s:jump_to_placeholder()
  let range_cmd = ''
  if mode() !=? 'n'
    let range_cmd .= "\<ESC>"
  endif

  let [_, lnum, column, offset] = getpos('.')
  let place = search(s:pat, 'nz', lnum)
  if !place
    call cursor(lnum, 1, offset)
  endif
  let [_, start] = searchpos(s:pat, 'z', lnum)
  if start == 0
    call cursor(lnum, column, offset)
    return ''
  endif
  let [_, end] = searchpos(s:pat, 'enz', lnum)

  let screen_start = virtcol([lnum, start])
  let screen_end = virtcol([lnum, end])

  let range_cmd .= 'v'.lnum.'G'.screen_end.'|o'.lnum.'G'.screen_start."|o\<C-G>"
  call feedkeys(range_cmd)
  return ''
endfunction


inoremap <silent><expr> <Plug>CompletorCppJumpToPlaceholder <SID>jump_to_placeholder()
noremap  <silent><expr> <Plug>CompletorCppJumpToPlaceholder <SID>jump_to_placeholder()
