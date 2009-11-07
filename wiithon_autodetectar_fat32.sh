#!/bin/bash

SEPARADOR=";@;"

# = 1 --> SI tienes udevinfo
# = 0 --> NO tienes udevinfo
function comprobarTienesUDEV()
{
	test -x /sbin/udevadm
        return $?
}

for i in $(awk '$4 ~ /^(sd|hd|loo).[[:digit:]]/ {print "/dev/" $4}' /proc/partitions);
do
	if file -sL $i | grep -q FAT; then
		USADO_LIBRE_TOTAL=`df -P $i | awk -v part=$i'$1 == part {print $3/1048576";@;"$4/1048576";@;"$2/1048576}' 2> /dev/null`
		if [ comprobarTienesUDEV ]; then
			NOMBRE=`/sbin/udevadm info -a -n $i | awk -F "==" 'BEGIN {n=0} $1 ~ /ATTRS{vendor}|ATTRS{model}/ {gsub(/\"/,"",$2);row[n++]=$2} END {print row[0]row[1]}'`
		else
			NOMBRE=""
		fi
		echo -n $i
		echo -n $SEPARADOR
		echo -n "fat32"
		echo -n $SEPARADOR
		echo -n $USADO_LIBRE_TOTAL
		echo -n $SEPARADOR
		echo -n $NOMBRE
		echo -n $SEPARADOR
		echo ""
	fi
done
