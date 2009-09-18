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

for i in $(cat /proc/partitions | grep -v name | sed '/^$/d' | awk '{print "/dev/" $4}' | egrep '(sd|hd|loop)([a-z])*([0-9])*');
do
	MAGICO=`head --bytes=4 $i 2> /dev/null`;
	LEGIBLE=`echo $MAGICO | wc -c`;
	# Si hay 5 caracteres = WBFS\n
	if [ $LEGIBLE -eq 5 ]; then
		if [ $MAGICO == "WBFS" ]; then
			USADO_LIBRE_TOTAL=`/usr/local/share/wiithon/wiithon_wrapper -p $i df 2> /dev/null`
			if [ $hayUDEV -eq 1 ]; then
				NOMBRE=`udevinfo -a -p $(udevinfo -q path -n $i) | egrep 'ATTRS{vendor}|ATTRS{model}' | awk -F== '{print $2}' | sed '3,$d' | sed 's/\"//g' | xargs`;
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
