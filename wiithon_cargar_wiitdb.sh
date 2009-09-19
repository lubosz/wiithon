#!/bin/sh

echo "DESCARGANDO"
wget -q http://wiitdb.com/wiitdb.zip
echo "DESCOMPRIMIENDO"
unzip -p wiitdb.zip > wiitdb.xml
rm wiitdb.zip
echo "CARGANDO"
./wiithon_cargar_wiitdb.py
rm wiitdb.xml
echo "FIN"
