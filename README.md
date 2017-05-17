Completor
=========

[![Build Status](https://travis-ci.org/maralla/completor.vim.svg?branch=master)](https://travis-ci.org/maralla/completor.vim)

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
you must have node and either npm or yarn installed. Then run:

```bash
make js
```

The node executable path can be specified using:

```vim
let g:completor_node_binary = '/path/to/node'
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

#### go
Use [gocode](https://github.com/nsf/gocode) to provide omni completions.
To specify the gocode executable path:

```vim
let g:completor_gocode_binary = '/path/to/gocode'
```

#### swift

Use [completor-swift](https://github.com/maralla/completor-swift).

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
inoremap <expr> <cr> pumvisible() ? "\<C-y>\<cr>" : "\<cr>"
```

#### Use Tab to trigger completion (disable auto trigger)

```vim
let g:completor_auto_trigger = 0
inoremap <expr> <Tab> pumvisible() ? "\<C-n>" : "\<C-x>\<C-u>\<C-p>"
```
