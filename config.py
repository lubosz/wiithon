#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os, sys

def getHOME():
    global WIITHON_FILES
    ruta = os.path.join(WIITHON_FILES , "HOME.conf")
    f = open(ruta , "r")
    HOME = f.read().strip()
    f.close()
    return HOME

APP="wiithon"
LOCALE="/usr/share/locale/"

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)
WIITHON_FILES_RECURSOS = os.path.join(WIITHON_FILES , "recursos")
WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS , "imagenes")

HOME = getHOME()
HOME_WIITHON = os.path.join(HOME , '.wiithon')
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_CARATULAS = os.path.join(HOME_WIITHON , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(HOME_WIITHON , 'discos')
HOME_WIITHON_LOGS = os.path.join(HOME_WIITHON , 'logs')
HOME_WIITHON_LOGS_PROCESO = os.path.join(HOME_WIITHON_LOGS , "proceso.log")

GLADE_ALERTA = "alerta"

DETECTOR_WBFS = os.path.join( WIITHON_FILES , "wiithon_autodetectar.sh" )
DETECTOR_WBFS_LECTOR = os.path.join( WIITHON_FILES , "wiithon_autodetectar_lector.sh" )

WBFS_APP = os.path.join(WIITHON_FILES , "wbfs")

TOPICS = ['ERROR', 'INFO', 'WARNING' , 'COMANDO']

# Cuando se descomprime un RAR, definimos si despues se borra la ISO
borrarISODescomprimida = False

# Lineas de pantallazo en consola (esta variable hay que trasladarlo a WiithonCLI)
NUM_LINEAS_PAUSA = 21

