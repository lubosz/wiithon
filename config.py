#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

'''On that file are the configurable parameters of the program.
Some variable names are generated from some os functions
'''

import os
import sys

import util

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)
WIITHON_FILES_RECURSOS = os.path.join(WIITHON_FILES , "recursos")
WIITHON_FILES_RECURSOS_GLADE = os.path.join(WIITHON_FILES_RECURSOS , "glade")
WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS , "imagenes")

HOME_WIITHON_CARATULAS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'discos')

if not os.path.exists(os.path.join(WIITHON_FILES , ".bzr")):
	LOCALE = "/usr/share/locale/"
	WBFS_APP = os.path.join(WIITHON_FILES , "wiithon_wrapper")
	ICONO = "/usr/share/pixmaps/wiithon.png"
else:
	LOCALE = os.path.join(WIITHON_FILES , "po")
	LOCALE = os.path.join(LOCALE , "locale")
	WBFS_APP = "libwbfs_binding/wiithon_wrapper.sh"
	ICONO = os.path.join(WIITHON_FILES_RECURSOS , "icons")
	ICONO = os.path.join(ICONO , "wiithon.png")

APP = "wiithon"
HOME = os.environ['HOME']
HOME_WIITHON = os.path.join(HOME , '.wiithon')
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_LOGS = os.path.join(HOME_WIITHON , 'logs')
HOME_WIITHON_LOGS_PROCESO = os.path.join(HOME_WIITHON_LOGS , "proceso.log")

# crear directorios si no existen
util.try_mkdir( HOME_WIITHON )
util.try_mkdir( HOME_WIITHON_BDD )
util.try_mkdir( HOME_WIITHON_LOGS )

util.try_mkdir( HOME_WIITHON_CARATULAS )
util.try_mkdir( HOME_WIITHON_DISCOS )

GLADE_ALERTA = "alerta"

DETECTOR_WBFS = os.path.join( WIITHON_FILES , "wiithon_autodetectar.sh" )
DETECTOR_WBFS_LECTOR = os.path.join( WIITHON_FILES , "wiithon_autodetectar_lector.sh" )
DETECTOR_WBFS_FAT32 = os.path.join( WIITHON_FILES , "wiithon_autodetectar_fat32.sh" )

# Cuando se descomprime un RAR, definimos si despues se borra la ISO
borrarISODescomprimida = False

# Lineas de pantallazo en consola (esta variable hay que trasladarlo
# a WiithonCLI)
NUM_LINEAS_PAUSA = 21

# Definido en libwbfs, longitud maxima de un titulo
TITULO_LONGITUD_MAX = 0x80

# Separador para la interactividad con wiithon_wrapper
# OJO, si se modifica hay que modificar los wiithon_autodetectar*.sh
SEPARADOR = ";@;"

# Maximos juegos que aparecerán en la lista de copia de disco duro completa
MAX_LISTA_COPIA_1on1 = 15

# Num de descargas simultaneas
NUM_HILOS = 15

# Tipo caratula 3d|normal|panoramica|full
TIPO_CARATULA = "normal"

