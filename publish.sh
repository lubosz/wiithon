#!/bin/sh

ver=`cat doc/VERSION`
rev=`bzr revno`
rev_next=$(($rev+1))

vim COMMIT
make commit
bzr push
#make deb
make ppa-inc
make ppa-upload CHANGES="../wiithon_"$ver"-"$rev_next"_source.changes"
