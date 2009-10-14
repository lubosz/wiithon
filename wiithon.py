#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/06/21/wiithon-1-0-liberado/
# :: Ver LICENCIA.txt

import sys
import os
import getopt

import config
import util
from cli import WiithonCLI
from gui import WiithonGUI
from core import WiithonCORE

# Para desactivar algun warning de GTK
import warnings
warnings.filterwarnings('ignore')

# Importamos los módulos necesarios
try:
    import pygtk
    pygtk.require('2.0') # Intenta usar la versión2
except:
    # Algunas distribuciones vienen con GTK2, pero no con pyGTK (o pyGTKv2)
    pass

try:
    import gtk
    import gtk.glade

except ImportError:
    print _("Necesitas tener instalado pyGTK o GTKv2")
    sys.exit(1)
    
def App():
    try:
        util.configurarLenguaje()

        if os.path.exists(os.path.join(config.WIITHON_FILES , ".bzr")):
            print _("Instala wiithon, no lo ejecutar desde ./wiithon.py")
            sys.exit(1)

        options, arguments = getopt.getopt(sys.argv[1:],
                                'pwhlferdi',
                                [
                                    'pause',
                                    'work',
                                    'help',
                                    'ls',
                                    'format',
                                    'extract',
                                    'rename',
                                    'delete',
                                    'install',
                                ])

        num_parms_cli = 0
        for option, value in options:
            if not (util.getExtension(option) == "iso"):
                num_parms_cli += 1
                    
        GUI = num_parms_cli == 0
        core = WiithonCORE()
        if GUI:
            interfaz = WiithonGUI(core)
        else:
            interfaz = WiithonCLI(core)

        interfaz.main(options, arguments)

    except getopt.GetoptError:
        print _("Programa ejecutado con las opciones incorrectas.")
    except AssertionError, mensaje:
        print str(mensaje)
    except KeyboardInterrupt:
        print _("Interrumpido por el usuario")

    sys.exit(0)

if __name__ == '__main__':
    App()
