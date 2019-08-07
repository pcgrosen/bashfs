# bashfs

## Overview

`bashfs` is a pyfuse3-based filesystem that allows you to interact with your favorite command line applications from the filesystem. For example:

``` shell
/ $ mkdir mnt
/ $ python -m bashfs mnt &
/ $ cd mnt
/mnt $ cat 'ls -a/run'
.
..
bashfs
.git
.gitignore
mnt
README.md
translator.py
/mnt $ cd 'ls -a'
/mnt/ls -a $ cd 'grep t'
/mnt/ls -a/grep t $ cat run
.git
.gitignore
mnt
translator.py
```

## Running other programs

By default, paths are passed to `bash -c` with slashes replaced with pipes. You can change this behavior via command-line options to bashfs:

``` shell
/ $ mkdir mnt
/ $ python -m bashfs mnt --argv-prefix=python --argv-prefix=-c --separator='
' &
/ $ cd mnt
/mnt $ cd 'a = "hello"'
/mnt/a = "hello" $ cd 'print(a)'
/mnt/a = "hello"/print(a) $ cat run
hello
```

## Escaping characters

Certain characters are not allowed in paths; for example, a slash cannot be entered without being interpreted as a path separator. `bashfs` allows you to escape these characters by inserting an exclamation point (`!`) before the desired character XORed with 0x40. For example, to enter a slash, `!o` would be used, because `'o' = 0x6F = 0x2F ^ 0x40 = '/' ^ 0x40`:

``` shell
/ $ mkdir mnt
/ $ python -m bashfs mnt &
/ $ cd mnt
/mnt $ cat '!obin!ols -a/run'
.
..
bashfs
.git
.gitignore
mnt
README.md
translator.py
```

## Installation

`bashfs` requires `pyfuse3`; however, it needs a particular feature which is currently pending upstreaming. See [this pull request](https://github.com/libfuse/pyfuse3/pull/17) for more information.

After a compatible version of `pyfuse3` is installed, no other installation should be necessary; `bashfs` should be runnable from wherever it is cloned.

## "Why?"

Why not?
