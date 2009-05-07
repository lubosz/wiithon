#!/usr/bin/python
# vim: set fileencoding=utf8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Jose Luis Segura <josel.segura@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii/
# :: Dependencias : apt-get install nautilus-actions imagemagick wget rar sudo
# :: Ver LICENCIA.txt

import sys
import getopt
import traceback

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

	core = WiithonCORE(interfaz)
	interfaz.setCore(core)
	core.main(opciones_formateadas, arguments)

except getopt.GetoptError:
	try:
		interfaz.alert('error', 'Programa ejecutado con las opciones incorrectas')
	except:
		print "Programa ejecutado con las opciones incorrectas"
	sys.exit(1)

except (AttributeError, AssertionError), mensaje:
	try:
		interfaz.alert("error", str(mensaje) )
	except:
		print str(mensaje)
	traceback.print_stack()
	sys.exit(1)

#############################################################

