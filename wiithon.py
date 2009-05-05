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
	core = WiithonCORE()
	interfaz.setCore(core)
	core.setInterfaz(interfaz)	
	core.main()

except AttributeError, msj:
	try:
		interfaz.alert("error", str(msj) )
	except:
		print "Error cargando interfaz: " + str(msj)
	sys.exit(1)

#############################################################

