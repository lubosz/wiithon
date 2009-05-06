#!/usr/bin/python
# vim: set fileencoding=utf8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Jose Luis Segura <josel.segura@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii/
# :: Dependencias : apt-get install nautilus-actions imagemagick wget rar sudo
# :: Ver LICENCIA.txt

import sys

from gui import WiithonGUI
from core import WiithonCORE

######################### MAIN ##############################

try:
	interfaz = WiithonGUI()
	argv = sys.argv[1:]

	options, arguments = getopt.getopt(argv, 'phH', ['trabajo=',
							 'work=',
							 'help',
							 'HELP',
							 'no-gui',
							 ])

	opciones_formateadas = {}
	for option, value in options:
		opciones_formateadas[option] = value

		#if option == '-p':
		#	PAUSA = True
		#
		#elif option in ['-h', '--help']:
		#	self.uso()
		#	sys.exit(0)
		#
		#elif option in ['--trabajo', '--work']:
		#	if os.path.isdir(value):
		#		os.chdir(value)
		#
		#	elif option == '--no-gui':
		#		GUI = False

	core = WiithonCORE()
	interfaz.setCore(core)
	core.setInterfaz(interfaz)
	core.main(opciones_formateadas, arguments)

except getopt.GetoptError:
	interfaz.alert('error', 'Programa ejecutado con las opciones incorrectas')
	sys.exit(1)

except AssertionError, mensaje:
	interfaz.alert('error', mensaje)
	sys.exit(1)

except AttributeError, msj:
	try:
		interfaz.alert("error", str(msj) )
	except:
		print "Error cargando interfaz: " + str(msj)
	sys.exit(1)

#############################################################

