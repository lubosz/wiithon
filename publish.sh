#!/bin/sh

vim COMMIT
make commit
bzr push
make deb
