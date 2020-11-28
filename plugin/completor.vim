" vim: et ts=2 sts=2 sw=2

let s:save_cpo = &cpo
set cpo&vim

function! s:restore_cpo()
    let &cpo = s:save_cpo
    unlet s:save_cpo
endfunction

function! s:has_features()
  return (has('pythonx') || has('python3') || has('python')) &&
        \ (has('job') && has('timers') || has('nvim')) &&
        \ has('lambda')
endfunction

if exists('g:loaded_completor_plugin')
    call s:restore_cpo()
    finish
elseif !s:has_features()
    echohl WarningMsg
    echomsg 'Completor requires vim compiled with python or python3 and has features `job`, `timers` and `lambda`'
    echohl None
    call s:restore_cpo()
    finish
endif

let g:loaded_completor_plugin = 1

let s:default_blacklist = ['tagbar', 'qf', 'netrw', 'unite', 'vimwiki']

let s:default_type_map = {
        \ 'c': 'cpp',
        \ 'javascript.jsx': 'javascript',
        \ 'python.django': 'python',
        \ 'typescript.tsx': 'typescript',
        \ 'typescript.jsx': 'typescript',
        \ }

let g:completor_blacklist = get(g:, 'completor_blacklist', s:default_blacklist)
" file size limit in KB
let g:completor_filesize_limit = get(g:, 'completor_filesize_limit', 1024) * 1024
let g:completor_min_chars = get(g:, 'completor_min_chars', 2)
let g:completor_completion_delay = get(g:, 'completor_completion_delay', 80)
let g:completor_refresh_always = get(g:, 'completor_refresh_always', 1)
let g:completor_doc_position = get(g:, 'completor_doc_position', 'bottom')
let g:completor_def_split = get(g:, 'completor_def_split', '')
let g:completor_complete_options = get(g:, 'completor_complete_options', 'menuone,noselect,preview')
let g:completor_filetype_map = extend(s:default_type_map, get(g:, 'completor_filetype_map', {}))
let g:completor_filename_completion_in_only_comment = get(g:, 'completor_filename_completion_in_only_comment', 1)
let g:completor_use_popup_window = get(g:, 'completor_use_popup_window', 0)


func s:init()
  call completor#enable_autocomplete()
  call completor#action#_on_insert_enter()

  augroup completor_event
  augroup END
endfunc


augroup completor
    autocmd!
    autocmd InsertEnter * call s:init()
augroup END


command! CompletorDisable call completor#disable_autocomplete()
command! CompletorEnable call completor#enable_autocomplete()

call s:restore_cpo()
