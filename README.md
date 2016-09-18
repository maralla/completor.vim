Completor
=========

Async completion framework for vim8.

Requirements
------------

* vim8,
* compiled with `python` or `python3`

Builtin Completers
------------------

* filename
* rust

To use rust completion [racer](https://github.com/phildawes/racer#installation)
should be installed.

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
