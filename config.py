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

def getHOME():
    'Method to calculate the HOME dirname of the user'
    global HOME, LOCALE, WBFS_APP, WIITHON_FILES_RECURSOS_IMAGENES, ICONO
    ruta = os.path.join(WIITHON_FILES , "HOME.conf")
    if os.path.exists(ruta):
        filedesc = open(ruta , "r")
        HOME = filedesc.read().strip()
        filedesc.close()
        LOCALE = "/usr/share/locale/"
        WBFS_APP = os.path.join(WIITHON_FILES , "wiithon_wrapper")
        ICONO = "/usr/share/pixmaps/wiithon.png"
        return HOME
    else:
        HOME = os.environ['HOME']
        LOCALE = os.path.join(WIITHON_FILES , "po")
        LOCALE = os.path.join(LOCALE , "locale")
        WBFS_APP = "libwbfs_binding/build_wiithon_wrapper/wiithon_wrapper.sh"
        WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , "cargando")
        ICONO = os.path.join(WIITHON_FILES_RECURSOS , "icons")
        ICONO = os.path.join(ICONO , "wiithon.png")
        return HOME

APP = "wiithon"
HOME = getHOME()
HOME_WIITHON = os.path.join(HOME , '.wiithon')
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_CARATULAS = os.path.join(HOME_WIITHON , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(HOME_WIITHON , 'discos')
HOME_WIITHON_LOGS = os.path.join(HOME_WIITHON , 'logs')
HOME_WIITHON_LOGS_PROCESO = os.path.join(HOME_WIITHON_LOGS , "proceso.log")

# crear directorios si no existen
util.try_mkdir( HOME_WIITHON )
util.try_mkdir( HOME_WIITHON_BDD )
util.try_mkdir( HOME_WIITHON_CARATULAS )
util.try_mkdir( HOME_WIITHON_DISCOS )
util.try_mkdir( HOME_WIITHON_LOGS )

GLADE_ALERTA = "alerta"

DETECTOR_WBFS = os.path.join( WIITHON_FILES , "wiithon_autodetectar.sh" )
DETECTOR_WBFS_LECTOR = os.path.join( WIITHON_FILES , "wiithon_autodetectar_lector.sh" )

# Cuando se descomprime un RAR, definimos si despues se borra la ISO
borrarISODescomprimida = False

# Lineas de pantallazo en consola (esta variable hay que trasladarlo
# a WiithonCLI)
NUM_LINEAS_PAUSA = 21

# Definido en libwbfs, longitud maxima de un titulo
TITULO_LONGITUD_MAX = 0x80

# Separador para la interactividad con wiithon_wrapper
SEPARADOR = ";@;"

# Maximos juegos que aparecerán en la lista de copia de disco duro completa
MAX_LISTA_COPIA_1on1 = 15
