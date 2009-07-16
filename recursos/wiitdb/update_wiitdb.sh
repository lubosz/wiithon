#!/bin/sh

if [ $# -gt 0 ]; then
	PWD=`pwd`
	cd $1
fi

# Borro el actual xml
rm wiitdb.xml

# Descargo la nueva base de datos comprimida
wget http://wiitdb.com/wiitdb.zip

# Descomprime la nueva bdd, generando el nuevo xml
unzip wiitdb.zip

# Borro la bdd comprimida recien descargada
rm wiitdb.zip

if [ $# -gt 0 ]; then
	cd $PWD
fi

