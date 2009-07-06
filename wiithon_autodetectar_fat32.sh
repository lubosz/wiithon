#!/bin/bash

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
	PARTICION=`fdisk -l | grep "W95 FAT32" | grep "$(echo $i)" | awk '{print $1}'`;
	NUM_LINEAS=`echo $PARTICION | wc -l`;
	if [ $NUM_LINEAS -eq 1 ]; then
		if [ $hayUDEV -eq 1 ]; then
			NOMBRE=`udevinfo -a -p $(udevinfo -q path -n $i) | egrep 'ATTRS{vendor}|ATTRS{model}' | awk -F== '{print $2}' | sed '3,$d' | sed 's/\"//g' | xargs`;
			echo $PARTICION":"$NOMBRE"";
		else
			echo $PARTICION":";
		fi
	fi
done
