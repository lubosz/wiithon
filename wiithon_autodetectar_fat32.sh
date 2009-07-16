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

for i in $(cat /proc/partitions | grep -v name | sed '/^$/d' | awk '{print "/dev/" $4}' | egrep '(sd|hd|loop)([a-z])*([0-9]){1,}');
do
	PARTICION=`fdisk -l | grep "W95 FAT32" | grep "$(echo -n $i)" | awk '{print $1}'`;
	NUM_LINEAS=`echo $PARTICION | wc -c`;
	if [ $NUM_LINEAS -gt 1 ]; then
		MAGICO=`head --bytes=4 $PARTICION 2> /dev/null`;
		if [ $MAGICO != "WBFS" ]; then
			USADO_LIBRE_TOTAL=`df -H $PARTICION | grep $PARTICION | awk '{print $3";@;"$4";@;"$2}' 2> /dev/null`
			if [ $hayUDEV -eq 1 ]; then
				NOMBRE=`udevinfo -a -p $(udevinfo -q path -n $i) | egrep 'ATTRS{vendor}|ATTRS{model}' | awk -F== '{print $2}' | sed '3,$d' | sed 's/\"//g' | xargs`;
			else
				NOMBRE=""
			fi
			echo -n $PARTICION
			echo -n $SEPARADOR
			echo -n "fat32"
			echo -n $SEPARADOR
			echo -n $USADO_LIBRE_TOTAL
			echo -n $SEPARADOR
			echo -n $NOMBRE
			echo -n $SEPARADOR
			echo ""
		fi
	fi
done
