#!/bin/bash

SEPARADOR=";@;"

# = 1 --> SI tienes udevinfo
# = 0 --> NO tienes udevinfo
comprobarTienesUDEV()
{
	return `which udevinfo 2> /dev/null | wc -l`
}

comprobarTienesUDEV
hayUDEV=$?

sleep 5

for i in $(ls /dev/*cd* -l | grep '^l'  | awk '{print $10}' | uniq | awk '{print "/dev/" $1}');
do
	MAGICO=`head --bytes=6 $i 2> /dev/null`;
	LEGIBLE=`echo $MAGICO | wc -c`;
	# Si hay 7 caracteres = ASDASD\n
	if [ $LEGIBLE -eq 7 ]; then
		RES=`echo $MAGICO | egrep '([A-Z0-9]{6})' | wc -l`;
		if [ $RES -gt 0 ]; then
			USADO_LIBRE_TOTAL="0.0"$SEPARADOR"0.0"$SEPARADOR"0.0"
			if [ $hayUDEV -eq 1 ]; then
				NOMBRE=`udevinfo -a -p $(udevinfo -q path -n $i) | egrep 'ATTRS{vendor}|ATTRS{model}' | awk -F== '{print $2}' | sed '3,$d' | sed 's/\"//g' | xargs`;
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
