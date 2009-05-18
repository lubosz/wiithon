#!/usr/bin/python
# vim: set fileencoding=utf-8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Jose Luis Segura <josel.segura@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii/
# :: Dependencias : apt-get install nautilus-actions imagemagick wget rar sudo python-sqlalchemy
# :: Ver LICENCIA.txt

import sys, os
import getopt

from cli import WiithonCLI
from gui import WiithonGUI
from core import WiithonCORE
import config


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
except:
    print "You need to install pyGTK or GTKv2 or set your PYTHONPATH correctly"
    sys.exit(1)

import gettext


APP="wiithon"

# Esto permite traducir los textos escritos en el .py (no en glade)
gettext.textdomain(APP)
gettext.bindtextdomain(APP)#, DIR)

# Y las siguientes 2 lineas permiten traducir los textos del Glade
gtk.glade.textdomain(APP)
gtk.glade.bindtextdomain(APP)#, DIR)

# Y con esto podemos marcar las cadenas a traducir de la forma _("cadena")
_ = gettext.gettext



def informarAcuerdo(pregunton):
	res = pregunton('''El equipo de Wiithon no se hace responsable de la aplicacion ni de la perdida de datos.
No obstante, la particion NO va ha ser formateada.
Esta aplicación añade, borra y lista juegos explicamente mediante la ayuda de %s.
Esta información no volverá a aparecer si acepta el acuerdo.
¿Está de acuerdo?''' % ( os.path.basename(config.WBFS_APP) ) )

	assert res == 1, "No puedes usar esta aplicacion si no estas de acuerdo"

	os.mkdir( config.HOME_WIITHON )
	os.mkdir( config.HOME_WIITHON_BDD )
	os.mkdir( config.HOME_WIITHON_CARATULAS )
	os.mkdir( config.HOME_WIITHON_DISCOS )
	os.mkdir( config.HOME_WIITHON_LOGS )

def App():
	try:
		options, arguments = getopt.getopt(sys.argv[1:], 'phH', ['trabajo=',
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
			elif option == '--no-gui':
				glade_gui = False
			else:
				opciones_formateadas[option] = value

		core = WiithonCORE()

		if glade_gui:
			interfaz = WiithonGUI(core)

			# solo pregunta el acuerdo por GUI
			if not os.path.exists(config.HOME_WIITHON):
				informarAcuerdo(interfaz.question)

			gtk.gdk.threads_enter()
			gtk.main()
			gtk.gdk.threads_leave()

		else:
			interfaz = WiithonCLI(core)
			interfaz.main(opciones_formateadas, arguments)

	except getopt.GetoptError:
		raise AssertionError, "Programa ejecutado con las opciones incorrectas."
	except AssertionError, mensaje:
		try:
			interfaz.alert("error", str(mensaje) )
		except:
			print str(mensaje)
		
	if PAUSA:
		raw_input("Pulse cualquier tecla para continuar ...\n")
	sys.exit(0)

if __name__ == '__main__':
	App()

