#!/bin/bash

NEEDED="wwt wget comm"

BASE_PATH="@@INSTALL-PATH@@"
LIB_PATH="$BASE_PATH/share/wwt"
URI_TITLES=@@URI-TITLES@@
LANGUAGES="@@LANGUAGES@@"

#------------------------------------------------------------------------------

make=0
if [[ $1 = --make ]]
then
    # it's called from make
    make=1
    shift
fi

#------------------------------------------------------------------------------

errtool=
for tool in $NEEDED
do
    which $tool >/dev/null 2>&1 || errtool="$errtool $tool"
done

if [[ $errtool != "" ]]
then
    echo "missing tools in PATH:$errtool" >&2
    exit 2
fi

#------------------------------------------------------------------------------

mkdir -p "$LIB_PATH" lib

echo "***    load titles.txt from $URI_TITLES"
wget -q -O- $URI_TITLES | wwt titles / - >lib/titles.tmp \
	&& test -s lib/titles.tmp \
	&& mv lib/titles.tmp lib/titles.txt
rm -f lib/titles.tmp

# load language specifig title files

for lang in $LANGUAGES
do
    LANG="$( echo $lang | awk '{print toupper($0)}' )"
    echo "***    load titles-$lang.txt from $URI_TITLES?LANG=$LANG"
    wget -q -O- "$URI_TITLES?LANG=$LANG" | wwt titles / - >lib/titles-$lang.tmp \
	&& test -s lib/titles-$lang.tmp \
	&& comm -13 lib/titles.txt lib/titles-$lang.tmp >lib/titles-$lang.txt
    rm -f lib/titles-$lang.tmp
done

if ((!make))
then
    echo "*** install titles to $LIB_PATH"
    mkdir -p "$LIB_PATH"
    cp -p lib/titles*.txt "$LIB_PATH"
fi

