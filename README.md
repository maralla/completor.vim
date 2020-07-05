Completor
=========

[![Test Status](https://github.com/maralla/completor.vim/workflows/unit%20test/badge.svg)](https://github.com/maralla/completor.vim/actions)

Completor is an asynchronous code completion framework for vim8. New features
of vim8 are used to implement the fast completion engine with low overhead.
For using semantic completion, external completion tools should be installed.

![Demo](http://i.imgur.com/f5EoiA6.gif)

Requirements
------------

* vim8,
* compiled with `python` or `python3`


Install
-------

* vim8 builtin package manager:

```bash
$ mkdir -p ~/.vim/pack/completor/start
$ cd ~/.vim/pack/completor/start
$ git clone https://github.com/maralla/completor.vim.git
```

* [pack](https://github.com/maralla/pack)

```bash
$ pack install maralla/completor.vim
```

* [vim-plug](https://github.com/junegunn/vim-plug)

```vim
Plug 'maralla/completor.vim'
```

Completers
----------

#### Filename
When the input matches a file path pattern the file name will be automatically
completed.

#### Buffer
This is the fallback completer. When no semantic completer found the buffer
completer will be used and will complete based on the current buffers.

#### Ultisnips and neosnippet

Ultisnips is supported by default. If [ultisnips](https://github.com/SirVer/ultisnips) is installed,
the snips candidates will show on the completion popup menu.

Use this plugin [completor-neosnippet](https://github.com/maralla/completor-neosnippet) for neosnippet support.

#### Neoinclude

Neoinclude is supported by default. If [neoinclude](https://github.com/Shougo/neoinclude.vim) is installed,
the include candidates will show on the completion popup menu.

#### dictionary

Dictionary completion is supported by [completor-dictionary](https://github.com/masawada/completor-dictionary).

#### shell

You can add some complete functions with shell command by [completor-shell](https://github.com/tokorom/completor-shell).

#### tmux

Completion from words in tmux panes is supported by [completor-tmux](https://github.com/ferreum/completor-tmux).

#### Python
Use [jedi](https://github.com/davidhalter/jedi) for completion. jedi should be
installed for semantic completion.  Install jedi to global environment or in virtualenv:

```bash
pip install jedi
```

The python executable can be specified using:

```vim
let g:completor_python_binary = '/path/to/python/with/jedi/installed'
```

#### Rust
Use racer for completion. [Install racer](https://github.com/phildawes/racer#installation)
first. To specify the racer executable path:

```vim
let g:completor_racer_binary = '/path/to/racer'
```

#### Javascript
Use [tern](https://github.com/ternjs/tern) for completion. To install tern
you must have node and either npm or yarn installed. Then go to the `completor.vim` directory and run:

```bash
make js
```

The node executable path can be specified using:

```vim
let g:completor_node_binary = '/path/to/node'
```

If you're using vim-plug, you can just use post install hook to do this for you.

```
Plug 'ternjs/tern_for_vim', { 'do': 'npm install' }
Plug 'maralla/completor.vim', { 'do': 'make js' }
```

#### c/c++
Use clang for completion. Clang should be installed first. To specify clang path:

```vim
let g:completor_clang_binary = '/path/to/clang'
```

To pass extra clang arguments, you can create a file named *.clang_complete*
under the project root directory or any parent directories. Every argument
should be in a single line in the file. This is an example file:
```
-std=c++11
-I/Users/maralla/Workspace/src/dji-sdk/Onboard-SDK/lib/inc
-I/Users/maralla/Workspace/src/dji-sdk/Onboard-SDK/sample/Linux/inc
```

The key mapping `<Plug>CompletorCppJumpToPlaceholder` can be defined
to jump to placeholders:

```vim
map <tab> <Plug>CompletorCppJumpToPlaceholder
imap <tab> <Plug>CompletorCppJumpToPlaceholder
```

#### go
Use [gocode](https://github.com/nsf/gocode) to provide omni completions.
To specify the gocode executable path:

```vim
let g:completor_gocode_binary = '/path/to/gocode'
```

#### swift

Use [completor-swift](https://github.com/maralla/completor-swift).

#### Elixir

Use [alchemist.vim](https://github.com/slashmili/alchemist.vim).

#### vim script

Use [completor-necovim](https://github.com/kyouryuukunn/completor-necovim).

#### type script

Use [completor-typescript](https://github.com/maralla/completor-typescript).

#### other languages

For other omni completions completor not natively implemented, auto completion
can still be used if an omni function is defined for the file type. But an option
should be defined to specify the trigger for triggering auto completion. The
option name pattern:

```vim
let g:completor_{filetype}_omni_trigger = '<python regex>'
```

For example to use css omnifunc:
```vim
let g:completor_css_omni_trigger = '([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$'
```

Tips
----

#### Config tern for javascript completion

This is simple *.tern-project* file:
```json
{
  "plugins": {
    "node": {},
    "es_modules": {}
  },
  "libs": [
    "ecma5",
    "ecma6"
  ],
  "ecmaVersion": 6
}
```

#### Use Tab to select completion

```vim
inoremap <expr> <Tab> pumvisible() ? "\<C-n>" : "\<Tab>"
inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<S-Tab>"
inoremap <expr> <cr> pumvisible() ? "\<C-y>" : "\<cr>"
```

#### Use Tab to trigger completion (disable auto trigger)

```vim
let g:completor_auto_trigger = 0
inoremap <expr> <Tab> pumvisible() ? "<C-N>" : "<C-R>=completor#do('complete')<CR>"
```

A better way:

```vim
" Use TAB to complete when typing words, else inserts TABs as usual.  Uses
" dictionary, source files, and completor to find matching words to complete.

" Note: usual completion is on <C-n> but more trouble to press all the time.
" Never type the same word twice and maybe learn a new spellings!
" Use the Linux dictionary when spelling is in doubt.
function! Tab_Or_Complete() abort
  " If completor is already open the `tab` cycles through suggested completions.
  if pumvisible()
    return "\<C-N>"
  " If completor is not open and we are in the middle of typing a word then
  " `tab` opens completor menu.
  elseif col('.')>1 && strpart( getline('.'), col('.')-2, 3 ) =~ '^[[:keyword:][:ident:]]'
    return "\<C-R>=completor#do('complete')\<CR>"
  else
    " If we aren't typing a word and we press `tab` simply do the normal `tab`
    " action.
    return "\<Tab>"
  endif
endfunction

" Use `tab` key to select completions.  Default is arrow keys.
inoremap <expr> <Tab> pumvisible() ? "\<C-n>" : "\<Tab>"
inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<S-Tab>"

" Use tab to trigger auto completion.  Default suggests completions as you type.
let g:completor_auto_trigger = 0
inoremap <expr> <Tab> Tab_Or_Complete()
```


#### Complete Options (completeopt)

Completor try its best to not overwrite the config `completeopt`, so the config
`g:completor_complete_options` is introduced to be the complete option when completor
is triggered.

```vim
let g:completor_complete_options = 'menuone,noselect,preview'
```

If you explicitly set `completeopt` completor will **not** use this value for complete
options.

#### Completor Actions

* Jump to definition `completor#do('definition')`
* Show documentation `completor#do('doc')`
* Format code `completor#do('format')`
* Hover info (lsp hover) `completor#do('hover')`

```vim
noremap <silent> <leader>d :call completor#do('definition')<CR>
noremap <silent> <leader>c :call completor#do('doc')<CR>
noremap <silent> <leader>f :call completor#do('format')<CR>
noremap <silent> <leader>s :call completor#do('hover')<CR>
```

#### Golang practices (without using lsp)

Use *guru* for jumping to definition:

```vim
let g:completor_go_guru_binary = 'guru'
```

Use *goimports* to format code:

```vim
let g:completor_go_gofmt_binary = 'goimports'
```

Format file after write to buffer:

```vim
autocmd BufWritePost *.go :call completor#do('format')
```

#### c/c++ practices (without using lsp)

Jump to completion placeholder:

```vim
map <c-\> <Plug>CompletorCppJumpToPlaceholder
imap <c-\> <Plug>CompletorCppJumpToPlaceholder
```

Disable completion placeholder:

```vim
let g:completor_clang_disable_placeholders = 1
```

#### Enable LSP

```vim
let g:completor_filetype_map = {}
" Enable lsp for go by using gopls
let g:completor_filetype_map.go = {'ft': 'lsp', 'cmd': 'gopls'}
" Enable lsp for rust by using rls
let g:completor_filetype_map.rust = {'ft': 'lsp', 'cmd': 'rls'}
" Enable lsp for c by using clangd
let g:completor_filetype_map.c = {'ft': 'lsp', 'cmd': 'clangd-7'}
```
