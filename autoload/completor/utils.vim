let s:py = has('python3') ? 'py3' : 'py'
let s:pyeval = function(has('python3') ? 'py3eval' : 'pyeval')

let s:slash = (exists('+shellslash') && !&shellslash) ? '\' : '/'
let s:tempname = ''


function! completor#utils#tempname()
  if empty(s:tempname)
    let s:tempname = tempname()
    call mkdir(s:tempname)
  endif

  let ext = expand('%:p:e')
  let ext_part = empty(ext) ? '' : '.'.ext
  let fname = 'completor__temp'.ext_part
  let path = s:tempname . s:slash . fname
  call writefile(getline(1, '$'), path)
  return path
endfunction


function! completor#utils#in_comment_or_string()
  let syn_group = synIDattr(synIDtrans(synID(line('.'), col('.') - 1, 1)), 'name')
  if stridx(syn_group, 'Comment') > -1
    return 1
  endif
  if stridx(syn_group, 'String') > -1
    return 2
  endif
  if stridx(syn_group, 'Constant') > -1
    return 3
  endif
  return 0
endfunction


function! completor#utils#setup_python()
  exe s:py 'from completor import api as completor_api'
endfunction


function! completor#utils#get_completer(ft, inputted)
  exe s:py 'res = completor_api.get_completer()'
  return s:pyeval('res')
endfunction


function! completor#utils#load(ft, action, inputted, meta)
  exe s:py 'res = completor_api.load()'
  return s:pyeval('res')
endfunction


function! completor#utils#on_data(action, msg)
  exe s:py 'res = completor_api.on_data()'
  return s:pyeval('res')
endfunction


function! completor#utils#get_start_column()
  exe s:py 'res = completor_api.get_start_column()'
  return s:pyeval('res')
endfunction


function! completor#utils#gen_request(action, args)
  exe s:py 'res = completor_api.gen_request()'
  return s:pyeval('res')
endfunction


function! completor#utils#is_message_end(msg)
  exe s:py 'res = completor_api.is_message_end()'
  return s:pyeval('res')
endfunction


function! completor#utils#reset()
  exe s:py 'completor_api.reset()'
endfunction


function! completor#utils#on_stream(name, action, msg)
  exe s:py 'completor_api.on_stream()'
endfunction


function! completor#utils#on_exit()
  exe s:py 'completor_api.on_exit()'
endfunction

function! completor#utils#add_offset(items, offset)
  for item in a:items
    let item.offset = a:offset
  endfor
  return a:items
endfunction
