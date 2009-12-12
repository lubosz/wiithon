#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

'''On that file are the configurable parameters of the program.
Some variable names are generated from some os functions
'''

import os
import sys

import util
import logging

try:
    if (os.environ['WIITHON_DEBUG'] == 'True'):
        DEBUG = True
        SUPERDEBUG = True
    else:
        raise util.CauseException
except:
    DEBUG = False
    SUPERDEBUG = False

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)
WIITHON_FILES_RECURSOS = os.path.join(WIITHON_FILES , "recursos")
WIITHON_FILES_RECURSOS_GLADE = os.path.join(WIITHON_FILES_RECURSOS , "glade")
WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS , "imagenes")
WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , "accesorio")

HOME_WIITHON_CARATULAS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES , 'discos')
# new!
HOME_WIITHON_CARATULAS_3D = os.path.join(HOME_WIITHON_CARATULAS , '3d')
HOME_WIITHON_CARATULAS_TOTAL = os.path.join(HOME_WIITHON_CARATULAS , 'total')
HOME_WIITHON_DISCOS_CUSTOM = os.path.join(HOME_WIITHON_DISCOS , 'custom')

LOCALE = "/usr/share/locale/"
ICONO = "/usr/share/pixmaps/wiithon.xpm"
WBFS_APP = os.path.join(WIITHON_FILES , "wiithon_wrapper")
UNRAR_APP = os.path.join(WIITHON_FILES , "wiithon_unrar")
LOADING_APP = os.path.join(WIITHON_FILES , "loading.py")

APP = "wiithon"
try:
    VER, REV = util.getVersionRevision()
except:
    VER, REV = "?", "?"
VERS_BDD = [1,2,3,4] # last is active
HOME = os.environ['HOME']
HOME_WIITHON = os.path.join(HOME , '.%s' % APP)
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_LOGS = os.path.join(HOME_WIITHON , 'logs')
HOME_WIITHON_LOGS_PROCESO = os.path.join(HOME_WIITHON_LOGS , "proceso.log")
i = 0
NEW_BDD_VERSION = False
for ver in VERS_BDD:
    HOME_WIITHON_BDD_BDD = os.path.join(HOME_WIITHON_BDD, '%s_db_ver-%d.db' % (APP, ver))
    i += 1
    if i != len(VERS_BDD):
        if os.path.exists(HOME_WIITHON_BDD_BDD):
            os.remove(HOME_WIITHON_BDD_BDD)
            NEW_BDD_VERSION = True

URI_ENGINE = 'sqlite:///%s' % HOME_WIITHON_BDD_BDD

try:
    # crear directorios si no existen
    util.try_mkdir( HOME_WIITHON )
    util.try_mkdir( HOME_WIITHON_BDD )
    util.try_mkdir( HOME_WIITHON_LOGS )
except AttributeError:
    pass

DETECTOR_WBFS = os.path.join( WIITHON_FILES , "wiithon_autodetectar.sh" )
DETECTOR_WBFS_LECTOR = os.path.join( WIITHON_FILES , "wiithon_autodetectar_lector.sh" )
DETECTOR_WBFS_FAT32 = os.path.join( WIITHON_FILES , "wiithon_autodetectar_fat32.sh" )
WBFS_FILE = os.path.join( WIITHON_FILES , "wiithon_wbfs_file" )
WDF_TO_ISO = os.path.join( WIITHON_FILES , "wiithon_wdf2iso" )
ISO_TO_WDF = os.path.join( WIITHON_FILES , "wiithon_iso2wdf" )
WWT = os.path.join( WIITHON_FILES , "wiithon_wwt" )

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

# ALTO de las imagenes de los accesorios
SIZE_IMAGE_ACCESORIOS = 80

#URL BUGS
URL_BUGS = "https://bugs.launchpad.net/wiithon/+filebug"

# URL WIITDB
URL_WIITDB = "wiitdb.com"

# LANGUAGE IF DONT AUTODETECT
LANGUAGE_WIITHON_DEFAULT = 'en'

# LANGUAGE FOR SEARCH
LANGUAGE_FOR_SEARCH = 'EN'

if DEBUG and SUPERDEBUG:
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.orm.unitofwork').setLevel(logging.DEBUG)
