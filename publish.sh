#!/bin/sh

VIM COMMIT
make commit
bzr push
make deb

