#!/bin/bash

SEPARADOR=";@;"

# = 1 --> SI tienes udevadm
# = 0 --> NO tienes udevadm
function comprobarTienesUDEV()
{
        test -x /sbin/udevadm
        return $?
}

sleep 5

for i in $(find /dev -type l -name "*cd*" -printf "/dev/%l\n" | uniq);
do
	MAGICO=`head --bytes=6 $i 2> /dev/null`;
	LEGIBLE=`echo $MAGICO | wc -c`;
	# Si hay 7 caracteres = ASDASD\n
	if [ $LEGIBLE -eq 7 ]; then
		RES=`echo $MAGICO | egrep '([A-Z0-9]{6})' | wc -l`;
		if [ $RES -gt 0 ]; then
			USADO_LIBRE_TOTAL="0.0"$SEPARADOR"0.0"$SEPARADOR"0.0"
			if [ comprobarTienesUDEV ]; then
				NOMBRE=`/sbin/udevadm info -a -n $i | awk -F "==" 'BEGIN {n=0} $1 ~ /ATTRS{vendor}|ATTRS{model}/ {gsub(/\"/,"",$2);row[n++]=$2} END {print row[0]row[1]}'`
			else
				NOMBRE=""
			fi
			echo -n $i
			echo -n $SEPARADOR
			echo -n "dvd"
			echo -n $SEPARADOR
			echo -n $USADO_LIBRE_TOTAL
			echo -n $SEPARADOR
			echo -n $NOMBRE
			echo -n $SEPARADOR
			echo ""
		fi
	fi
done
