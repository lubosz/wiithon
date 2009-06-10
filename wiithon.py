#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Jose Luis Segura <josel.segura@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii/
# :: Ver LICENCIA.txt

import sys
import os
import getopt

import config
import util

from cli import WiithonCLI
from gui import WiithonGUI
from core import WiithonCORE

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

def configurarLenguaje():
    import locale
    import gettext

    locale.setlocale(locale.LC_ALL, '')

    from gettext import gettext as _

    for module in (gettext, gtk.glade):
        module.bindtextdomain(config.APP,config.LOCALE)
        module.textdomain(config.APP)

    gettext.install(config.APP,config.LOCALE, unicode=1)

def App():
    try:
        configurarLenguaje()

        options, arguments = getopt.getopt(sys.argv[1:], 'pch', ['trabajo=',
                                 'work=',
                                 'help',
                                 'HELP',
                                 'no-gui',
                                 ])

        # Por defecto es GUI
        glade_gui = True
        # controla si se ha pasado el parametro "-p"
        PAUSA = False
        opciones_formateadas = {}

        for option, value in options:
            if option == '-p':
                PAUSA = True
                # si pausamos -> es CLI
                glade_gui = False
            elif option in ['--trabajo', '--work']:
                if os.path.isdir(value):
                    os.chdir(value)
            elif option in ['--no-gui', '-c','-h']:
                glade_gui = False
            else:
                opciones_formateadas[option] = value

        core = WiithonCORE()

        if glade_gui:
            interfaz = WiithonGUI(core)
        else:
            interfaz = WiithonCLI(core)

        interfaz.main(opciones_formateadas, arguments)

    except getopt.GetoptError:
        raise AssertionError, _("Programa ejecutado con las opciones incorrectas.")
    except AssertionError, mensaje:
        print str(mensaje)

    if PAUSA:
        raw_input(_("Pulse cualquier tecla para continuar ...\n"))

    sys.exit(0)

if __name__ == '__main__':
    App()
