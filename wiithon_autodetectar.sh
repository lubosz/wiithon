#!/bin/bash

# = 1 --> SI tienes udevinfo
# = 0 --> NO tienes udevinfo
comprobarTienesUDEV()
{
	return `which udevinfo 2> /dev/null | wc -l`
}

comprobarTienesUDEV
hayUDEV=$?

for i in $(cat /proc/partitions | grep -v name | sed '/^$/d' | awk '{print "/dev/" $4}' | egrep '(s|h)d([a-z])([0-9]){0,}');
do
	MAGICO=`head --bytes=4 $i 2> /dev/null`;
	LEGIBLE=`echo $MAGICO | wc -c`;
	# Si hay 5 caracteres = WBFS\n
	if [ $LEGIBLE -eq 5 ]; then
		if [ $MAGICO == "WBFS" ]; then
			if [ $hayUDEV -eq 1 ]; then
				NOMBRE=`udevinfo -a -p $(udevinfo -q path -n $i) | egrep 'ATTRS{vendor}|ATTRS{model}' | awk -F== '{print $2}' | sed '3,$d' | sed 's/\"//g' | xargs`;
				echo $i":"$NOMBRE"";
			else
				echo $i":";
			fi
		fi
	fi
done
