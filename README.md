Completor
=========

Completor is an asynchronous code completion framework for vim8. New features
of vim8 are used to implement the fast completion engine with low overhead.
For using semantic completion, external completion tools should be installed.

[Doc](doc/compeltor.txt)

![Demo](http://i.imgur.com/f5EoiA6.gif)

Requirements
------------

* vim8,
* compiled with `python` or `python3`

Completers
----------

* filename
* Rust. [racer](https://github.com/phildawes/racer#installation) should be installed.
* Python. [jedi](https://github.com/davidhalter/jedi#installation) should be installed.
* Javascript. Use [tern](http://ternjs.net) for completion.
* c/c++. Use clang for completions. `clang` should be installed.

For other omni completions completor not natively implemented, auto completion
can be still used if the file type defined an omni function. But an option
should be define to specify the trigger for triggering auto completion. The
option name pattern:

```vim
let g:completor_{filetype}_omni_trigger = '<python regex>'
```

For example to use css omnifunc:
```vim
let g:completor_css_omni_trigger = '(\w+|@\w*|\w+:\s*\w*)$'
```

Install
-------

* vim8 builtin package manager:

```bash
mkdir -p ~/.vim/pack/completor/start
cd ~/.vim/pack/completor/start
git clone https://github.com/maralla/completor.vim.git
```

* [vim-plug](https://github.com/junegunn/vim-plug)

```vim
Plug 'maralla/completor.vim'
```
