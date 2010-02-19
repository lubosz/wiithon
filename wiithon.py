#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# 
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/11/20/wiithon-1-1-publicado/
# :: Ver doc/LICENCIA

import sys
import os
import getopt
import gobject
import subprocess

import config
import util
from preferencias import Preferencias
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
        gobject.threads_init()
        
        prefs = Preferencias()
        prefs.cargarPreferenciasPorDefecto()
        util.configurarLenguaje(prefs.APPLICATION_LANGUAGE)
        
        comando = "ps aux | grep /usr/games/wiithon | grep -v grep | wc -l"
        num_wiithonActivo = int(util.getSTDOUT(comando))
        if num_wiithonActivo > 1:
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            window.set_title(_("WARNING:"))
            window.set_position(gtk.WIN_POS_CENTER)
            #window.set_default_size(600,500)
            window.connect("destroy", lambda x: gtk.main_quit())
            window.set_border_width(10)
            
            #button = gtk.Button(_("Cerrar"))
            #button.connect("clicked", lambda x: gtk.main_quit())
            
            etiqueta = gtk.Label()
            etiqueta.set_text("<b>%s.</b>" % _("Ya tienes Wiithon abierto"))
            etiqueta.set_use_markup(True)
            etiqueta.set_alignment(0.5 , 0.5)
            etiqueta.set_padding(40, 40)
            
            #h1 = gtk.VBox()
            #h1.pack_start(etiqueta)
            #h1.pack_start(button)
            #window.add(h1)
            window.add(etiqueta)
            #window.add(button)
            #button.show()
            etiqueta.show()
            window.show()
            gtk.main()
            sys.exit(1)

        if os.path.exists(os.path.join(config.WIITHON_FILES , ".bzr")):
            print _("Instala wiithon, no lo ejecute desde ./wiithon.py")
            sys.exit(1)

        options, arguments = getopt.getopt(sys.argv[1:],
                                'hlferdimvp:g:a:w:',
                                [
                                    'pause',
                                    'work',
                                    'help',
                                    'ls',
                                    'format',
                                    'add',
                                    'extract',
                                    'rename',
                                    'delete',
                                    'install',
                                    'covers',
                                    'discs',
                                    'massive',
                                    'partition',
                                    'game',
                                    'version'
                                ])

        num_parms_cli = 0
        for option, value in options:

            if(util.getExtension(option)=="iso"):
                pass
            elif(util.getExtension(option)=="rar"):
                pass
            elif(util.getExtension(option)=="wbfs"):
                pass
            elif(util.getExtension(option)=="wdf"):
                pass
            elif( os.path.isdir(option) ):
                pass
            else:
                num_parms_cli += 1


        GUI = num_parms_cli == 0
        if GUI:
            loading = subprocess.Popen(config.LOADING_APP , shell=False)
        
        core = WiithonCORE(prefs)
        if GUI:
            interfaz = WiithonGUI(core, loading)
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
