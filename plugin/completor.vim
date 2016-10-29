" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

function! s:restore_cpo()
    let &cpo = s:save_cpo
    unlet s:save_cpo
endfunction

if exists('g:loaded_completor_plugin')
    call s:restore_cpo()
    finish
elseif !(has('python') || has('python3')) || !(has('job') && has('timers') && has('lambda'))
    echohl WarningMsg
    echomsg 'Completor requires vim compiled with python or python3 and has features `job`, `timers` and `lambda`'
    echohl None
    call s:restore_cpo()
    finish
endif

let g:loaded_completor_plugin = 1


let s:default_blacklist = ['tagbar', 'qf', 'netrw', 'unite', 'vimwiki']
let g:completor_blacklist = extend(get(g:, 'completor_blacklist', []), s:default_blacklist)
" file size limit in KB
let g:completor_filesize_limit = get(g:, 'completor_filesize_limit', 1024) * 1024
let g:completor_min_chars = get(g:, 'completor_min_chars', 2)

if has('python3')
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
    autocmd InsertEnter * call completor#enable()
augroup END


command! CompletorDisable call completor#disable()
command! CompletorEnable call completor#enable()

call s:restore_cpo()
