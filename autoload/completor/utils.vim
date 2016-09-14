function! completor#utils#tempname()
  let tmp = escape(tempname(), ' ')
  call writefile(getline(1, '$'), tmp)
  return tmp
endfunction
