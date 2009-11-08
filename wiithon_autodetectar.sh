#!/bin/bash

SEPARADOR=";@;"

# = 1 --> SI tienes udevadm
# = 0 --> NO tienes udevadm
function comprobarTienesUDEV()
{
	test -x /sbin/udevadm
	return $?
}

for i in $(awk 'NR>2 {print "/dev/" $4}' /proc/partitions);
do
	MAGICO=`head --bytes=4 $i 2> /dev/null`;
	LEGIBLE=`echo $MAGICO | wc -c`;
	# Si hay 5 caracteres = WBFS\n
	if [ $LEGIBLE -eq 5 ]; then
		if [ $MAGICO == "WBFS" ]; then
			USADO_LIBRE_TOTAL=`/usr/local/share/wiithon/wiithon_wrapper -p $i df 2> /dev/null`
			if [ comprobarTienesUDEV ]; then
				NOMBRE=`/sbin/udevadm info -a -n $i | awk -F "==" 'BEGIN {n=0} $1 ~ /ATTRS{vendor}|ATTRS{model}/ {gsub(/\"/,"",$2);row[n++]=$2} END {print row[0]row[1]}'`
			else
				NOMBRE=""
			fi
			echo -n $i
			echo -n $SEPARADOR
			echo -n "wbfs"
			echo -n $SEPARADOR
			echo -n $USADO_LIBRE_TOTAL
			echo -n $SEPARADOR
			echo -n $NOMBRE
			echo -n $SEPARADOR
			echo ""
		fi
	fi
done
