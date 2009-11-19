#!/bin/bash

flag=svn-revision.flag
makefile=Makefile.setup

if [[ -d .svn ]] && which svn >/dev/null 2>&1
then
    revision_next="$(svn info | awk '$1 == "Revision:" {print $2}')"
    if which svnversion >/dev/null 2>&1
    then
	revision="$(svnversion|sed 's/.*://')"
    else
	revision="$revision_next"
    fi
    revision_num="${revision//[!0-9]/}"
    revision_next="${revision_next//[!0-9]/}"
    (( revision_next < revision_num )) && let revision_next=revision_num
    [[ $revision = $revision_next ]] || let revision_next++
elif [[ -f $flag ]]
then
    revision="$(head -n1 $flag|sed 's/[^0-9]//g')"
    [[ $revision = "" ]] && revision=0
    revision_num="$revision"
    revision_next="$revision"
else
    revision=0
    revision_num=0
    revision_next=0
fi

echo $revision_next >$flag

tim=($(date '+%s %Y-%m-%d %T'))

cat <<- ---EOT--- >$makefile
	REVISION	:= $revision
	REVISION_NUM	:= $revision_num
	REVISION_NEXT	:= $revision_next
	BINTIME		:= ${tim[0]}
	DATE		:= ${tim[1]}
	TIME		:= ${tim[2]}
	---EOT---
