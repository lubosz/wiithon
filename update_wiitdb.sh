#!/bin/sh

# si hay parametro
if [ $# -gt 0 ]; then
	PWD=`pwd`
	cd $1
else
    cd "recursos/wiitdb/"
fi

# Borro el actual xml
rm wiitdb.xml
rm wiitdb.xsd

# Descargo la nueva base de datos comprimida
wget http://wiitdb.com/wiitdb.zip
wget http://wiitdb.com/wiitdb/tmp/wiitdb.xsd
# wget http://wiitdb.com/wiitdb.zip?LANG=ES?ID=MGP,ENP -O wiitdb.zip
# wget http://wiitdb.com/wiitdb.zip?LANG=ES -O wiitdb.zip

# Descomprime la nueva bdd, generando el nuevo xml
unzip wiitdb.zip

# elimino tabuladores verticulas(¿?)
sed 's/\x0b/\x09/g' wiitdb.xml > wiitdb_sed.xml

# Borro la bdd comprimida recien descargada
rm wiitdb.zip
rm wiitdb.xml
mv wiitdb_sed.xml wiitdb.xml


