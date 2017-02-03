let s:py = has('python3') ? 'py3' : 'py'
let s:pyeval = function(has('python3') ? 'py3eval' : 'pyeval')


function! completor#utils#tempname()
  let tmp = escape(tempname(), ' ')
  let ext = expand('%:p:e')
  let ext = empty(ext) ? '' : '.'.ext
  let tmp .= ext
  call writefile(getline(1, '$'), tmp)
  return tmp
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


function! completor#utils#get_completions(msg)
  exe s:py 'res = completor_api.get_completions()'
  return s:pyeval('res')
endfunction


function! completor#utils#get_start_column()
  exe s:py 'res = completor_api.get_start_column()'
  return s:pyeval('res')
endfunction


function! completor#utils#daemon_request()
  exe s:py 'res = completor_api.get_daemon_request()'
  return s:pyeval('res')
endfunction


function! completor#utils#message_ended(msg)
  exe s:py 'res = completor_api.is_message_end()'
  return s:pyeval('res')
endfunction

function! completor#utils#retrigger()
  exe s:py 'res = completor_api.fallback_to_common()'
  let info = s:pyeval('res')
  if empty(info)
    return
  endif

  let [cmd, ft, daemon, is_sync] = info
  call completor#do_complete(cmd, ft, daemon, is_sync)
endfunction
