function! completor#utils#tempname()
  let tmp = escape(tempname(), ' ')
  let ext = expand('%:p:e')
  let ext = empty(ext) ? '' : '.'.ext
  let tmp .= ext
  call writefile(getline(1, '$'), tmp)
  return tmp
endfunction
