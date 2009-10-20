#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

'''On that file are the configurable parameters of the program.
Some variable names are generated from some os functions
'''

import os
import sys

import util

DEBUG = False

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)
WIITHON_FILES_RECURSOS = os.path.join(WIITHON_FILES , "recursos")
WIITHON_FILES_RECURSOS_GLADE = os.path.join(WIITHON_FILES_RECURSOS , "glade")
WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS , "imagenes")
WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , "accesorio")

HOME_WIITHON_CARATULAS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'discos')

LOCALE = "/usr/share/locale/"
WBFS_APP = os.path.join(WIITHON_FILES , "wiithon_wrapper")
ICONO = "/usr/share/pixmaps/wiithon.png"
UNRAR_APP = os.path.join(WIITHON_FILES , "unrar")

APP = "wiithon"
VER = "1.1"
HOME = os.environ['HOME']
HOME_WIITHON = os.path.join(HOME , '.%s' % APP)
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_LOGS = os.path.join(HOME_WIITHON , 'logs')
HOME_WIITHON_LOGS_PROCESO = os.path.join(HOME_WIITHON_LOGS , "proceso.log")

URI_ENGINE = 'sqlite:///%s' % os.path.join(HOME_WIITHON_BDD, '%s%s.db' % (APP, VER))

# crear directorios si no existen
util.try_mkdir( HOME_WIITHON )
util.try_mkdir( HOME_WIITHON_BDD )
util.try_mkdir( HOME_WIITHON_LOGS )

DETECTOR_WBFS = os.path.join( WIITHON_FILES , "wiithon_autodetectar.sh" )
DETECTOR_WBFS_LECTOR = os.path.join( WIITHON_FILES , "wiithon_autodetectar_lector.sh" )
DETECTOR_WBFS_FAT32 = os.path.join( WIITHON_FILES , "wiithon_autodetectar_fat32.sh" )

# Definido en libwbfs, longitud maxima de un titulo
TITULO_LONGITUD_MAX = 0x80

# Separador para la interactividad con wiithon_wrapper
# OJO, si se modifica hay que modificar los wiithon_autodetectar*.sh
SEPARADOR = ";@;"

# Maximos juegos que aparecerán en la lista de copia de disco duro completa
MAX_LISTA_COPIA_1on1 = 15

# CLI
# Lineas de pantallazo en consola
NUM_LINEAS_PAUSA = 21
