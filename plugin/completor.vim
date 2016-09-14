" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

function! s:restore_cpo()
    let &cpo = s:save_cpo
    unlet s:save_cpo
endfunction

if exists("g:loaded_completor_plugin")
    call s:restore_cpo()
    finish
elseif !(has('python') || has('python3')) || !(has('job') && has('timers') && has('lambda'))
    echohl WarningMsg |
                \ echomsg "Completor requires vim compiled with python or python3 and has features `job`, `timers` and `lambda`" |
                \ echohl None
    call s:restore_cpo()
    finish
endif


let g:loaded_completor_plugin = 1

if has("python3")
    command! -nargs=1 Py py3 <args>
    function! Pyeval(arg)
        return py3eval(a:arg)
    endfunction
else
    command! -nargs=1 Py py <args>
    function! Pyeval(arg)
        return pyeval(a:arg)
    endfunction
endif

augroup completor
    autocmd!
    autocmd VimEnter * call completor#enable()
augroup END


call s:restore_cpo()
