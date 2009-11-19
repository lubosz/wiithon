#!/bin/bash

#------------------------------------------------------------------------------

BASE_PATH="@@INSTALL-PATH@@"
BIN_PATH="$BASE_PATH/bin"
LIB_PATH="$BASE_PATH/share/wwt"

BIN_FILES="@@BIN-FILES@@"
LIB_FILES="@@LIB-FILES@@"

CP_FLAGS="-p --no-preserve=ownership"

#------------------------------------------------------------------------------

make=0
if [[ $1 = --make ]]
then
    # it's called from make
    make=1
    shift
fi

#------------------------------------------------------------------------------

mkdir -p "$BIN_PATH" "$LIB_PATH"

echo "*** install binaries to $BIN_PATH"

for f in $BIN_FILES
do
    cp $CP_FLAGS bin/$f "$BIN_PATH/$f.tmp"
    mv "$BIN_PATH/$f.tmp" "$BIN_PATH/$f"
    rm -f "$BIN_PATH/$f.tmp"
done

echo "*** install lib files to $LIB_PATH"

for f in $LIB_FILES
do
    cp $CP_FLAGS lib/$f "$LIB_PATH/$f.tmp"
    mv "$LIB_PATH/$f.tmp" "$LIB_PATH/$f"
    rm -f "$LIB_PATH/$f.tmp"
done

#------------------------------------------------------------------------------

((make)) || ./load-titles.sh
