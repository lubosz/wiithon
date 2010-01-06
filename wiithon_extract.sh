#! /bin/bash

LS_APP=/usr/share/wiithon/wiithon_wrapper
ISO_APP=/usr/games/wiithon
WBFS_APP=/usr/share/wiithon/wiithon_wbfs_file
WWT_APP=/usr/share/wiithon/wiithon_wwt
TMPFILE=/tmp/wiithon_filelist.tmp.$$

function error
{
    echo "wiithon_extract.sh: "$1
    echo "Try wiithon_extract.sh -h for more information."
    [[ -e $TMPFILE ]] && rm $TMPFILE
    exit 1
}

function help
{
    echo "wiithon_extract.sh -p <partition> [-l] [-t iso|wbfs|wdf] [-w <work dir>] [-f <filename>] [-h]"
    echo
    echo "-p   set WBFS partition"
    echo "-l   list games from WBFS partition"
    echo "-t   set output file type: ISO, WBFS or WDF"
    echo "-w   set working directory (if not specified is current directory)"
    echo "-f   extract only games in filelist"
    echo "-h   this help page"
    echo
    echo "Example 1: extract ALL games in WBFS format in the current directory"
    echo "wiithon_extract.sh -p /dev/sdb1 -t wbfs"
    echo
    echo "Example 2: create a new games list on file /tmp/filelist.txt"
    echo "wiithon_extract.sh -p /dev/sdb1 -l > /tmp/filelist.txt"
    echo 
    echo "Example 3: extract only games from filelist in ISO format in /tmp"
    echo "wiithon_extract.sh -p /dev/sdb1 -t iso -w /tmp -f /tmp/filelist.txt"
    exit 0
}

function create_filelist
{
    $LS_APP -p $1 ls | cut -d\; -f1,3 | sed -e 's/;/\t/g'
}

function extract_game
{
    IDGAME=$1
    case $TYPE in
        iso)
            echo "extracting $IDGAME to ISO..."
            $ISO_APP -p $PARTITION extract $IDGAME > /dev/null
            ;;
        wbfs)
            echo "extracting $IDGAME to WBFS..."
            $WBFS_APP $PARTITION extract_wbfs $IDGAME . > /dev/null
            ;;
        wdf)
            echo "extracting $IDGAME to WFT..."
            $WWT_APP EXTRACT -p $PARTITION -o -W $IDGAME > /dev/null
            ;;
    esac
}

#########################################################################################
# MAIN
#########################################################################################

while getopts "p:t:w:f:lh" OPT; do
   case $OPT in
      p)   PARTITION=$OPTARG;;
      t)   TYPE=$OPTARG;;
      w)   WORKDIR=$OPTARG;;
      f)   FILELIST=$OPTARG;;
      l)   LIST="true";;
      h)   help;;
      *)   error "option not valid or missed argument.";;
   esac
done

shift $(($OPTIND - 1))

if [ "$LIST" -a ! -z "$PARTITION" ]
then
    create_filelist $PARTITION
    exit 0
fi

if [ -z "$PARTITION" -o -z "$TYPE" ]
then
    error "options p and t are required."
fi

if [ -z "$FILELIST" ]
then
    create_filelist $PARTITION > $TMPFILE
    FILELIST=$TMPFILE
else
    if [ ! -e "$FILELIST" ]
    then
        error "cannot open file $FILELIST."
    fi
fi

OLDPWD=$PWD
if [ ! -z "$WORKDIR" ]
then
        cd $WORKDIR
fi

## extract ###############################################################
while read ID TITLE
do
    extract_game $ID
done < $FILELIST

cd $OLDPWD
[[ -e $TMPFILE ]] && rm $TMPFILE
exit 0
