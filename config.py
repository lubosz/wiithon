#-*-mode: python; coding: utf-8-*-

import os, sys

HOME = os.environ['HOME']
HOME_WIITHON = HOME + '/.wiithon'

WIITHON_PATH = os.path.dirname(sys.argv[0])
WIITHON_FILES = os.path.dirname(__file__)

# FIXME: er alguna librería de python que permita hacer el sudo en código
WBFS_APP = "gksudo " + config.WIITHON_FILES + "/wbfs"

