#!/bin/sh

# Borro el actual xml
rm wiitdb.xml

# Descargo la nueva base de datos comprimida
wget http://wiitdb.com/wiitdb.zip

# Descomprime la nueva bdd, generando el nuevo xml
unp wiitdb.zip

# Borro la bdd comprimida recien descargada
rm wiitdb.zip


