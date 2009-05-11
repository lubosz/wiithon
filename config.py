#-*-mode: python; coding: utf-8-*-

import os, sys

HOME = os.environ['HOME']
HOME_WIITHON = os.path.join(HOME , '.wiithon')
HOME_WIITHON_BDD = os.path.join(HOME_WIITHON , 'bdd')
HOME_WIITHON_CARATULAS = os.path.join(HOME_WIITHON , 'caratulas')
HOME_WIITHON_DISCOS = os.path.join(HOME_WIITHON , 'discos')

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)

WBFS_APP = os.path.join(WIITHON_FILES , "wbfs")

# Aunque este no es su sitio
topics = ['error', 'warning', 'info']

# Cuando se descomprime un RAR, definimos si despues se borra la ISO
borrarISODescomprimida = False

# Lineas de pantallazo en consola (esta variable hay que trasladarlo a WiithonCLI)
NUM_LINEAS_PAUSA = 21

