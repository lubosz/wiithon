#!/bin/sh

if [ $# -gt 0 ]; then
	PWD=`pwd`
	cd $1
fi

# Borro el actual xml
rm wiitdb.xml

# Descargo la nueva base de datos comprimida
# wget http://wiitdb.com/wiitdb.zip
# wget http://wiitdb.com/wiitdb.zip?LANG=ES?ID=MGP,ENP -O wiitdb.zip
wget http://wiitdb.com/wiitdb.zip?LANG=ES -O wiitdb.zip

# Descomprime la nueva bdd, generando el nuevo xml
unzip wiitdb.zip

# Borro la bdd comprimida recien descargada
rm wiitdb.zip

if [ $# -gt 0 ]; then
	cd $PWD
fi

