#!/usr/bin/python
# vim: set fileencoding=utf8 :
#
# :: Mantenedor: Ricardo Marmolejo García <makiolo@gmail.com>
# :: Jose Luis Segura <josel.segura@gmail.com>
# :: Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii/
# :: Dependencias : apt-get install nautilus-actions imagemagick wget rar sudo python-sqlalchemy
# :: Ver LICENCIA.txt

import sys, os
import getopt

from gui import WiithonGUI
from core import WiithonCORE

def uso():
	wiithon = os.path.basename(sys.argv[0])

	print '''Listar juegos. El programa por defecto, sin parametros, hace un listado de los juegos (lanzara el GUI en alguna prox versión):
\t\t%s

Añadir ISO mediante una lista explicita de las ISOS:
\t\t%s "%s/wii/mario.iso" "iso2" "iso3" "isoN"

Añadir ISO con exp. reg. La expresión solo afecta al directorio actual, actualmente no es recursivo:
\t\t%s *.iso

Buscar y Añadir ISO's recursivamente. Busca todos las imagenes isos RECURSIVAMENTE, incluso tambien busca dentro de RAR, a falta de implementar zip), tal vez necesites apt-get install rar.
\t\t%s buscar

Borrar juegos. Especificando el juego mediante un menú:
\t\t%s borrar

Borrar juegos. Podemos borrar con el IDGAME:
\t\t%s borrar IDJUEGO

Borrar juegos. Podemos borrar con el IDGAME obtenido a partir de un ISO local. El archivo ISO local NO es borrado:
\t\t%s borrar "%s/wii/mario.iso"

Renombrar juegos. Especificando el juego mediante un menú:
\t\t%s renombrar

Renombrar juegos, puedes cambiar el nombre de los juegos ya metidos en HD, útil para que nos enteremos cuando estemos con el USB Loader:
\t\t%s renombrar IDGAME "Mario Kart Wii"

Extraer juegos a un archivo ISO. El juego es especificado mediante un menú:
\t\t%s extraer

Extraer juegos a un archivo ISO. OJO! : El archivo ISO de salida pertenecerá a root:
\t\t%s extraer IDJUEGO

Descargar todas las caratulas automaticamente a 160x225. Ojo puede que el servidor te banee, si te ocurre intentalo 5 minutos más tarde:
\t\t%s caratulas

Descargar la caratulas de un juego especificado por su IDGAME, la imagen es bajada a 160x225. El comando es un singular, es "caratula" ya que "caratulas" descarga todas:
\t\t%s caratula IDGAME

Descargar la caratulas de un juego especificado por menú, la imagen es bajada a 160x225. El comando es un singular, es "caratula" ya que "caratulas" descarga todo:
\t\t%s caratula"

Comprobar Integridad de los juegos. Muchos de nuestros juegos pueden estar corruptos sin aún saberlo debido a el bug de borrado de las primeras versiones de WBFS
\t\t%s comprobar

Instar juegos desde el DVD, al estilo del usb loader, pero algo más lento porque dumpea a ISO y cuando termina mete la ISO:
\t\t%s instalar


Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii
''' %(wiithon,
      wiithon, sys.argv[0],
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon, sys.argv[0],
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon,
      wiithon
      )

def App():
	try:
		options, arguments = getopt.getopt(sys.argv[1:], 'phH', ['trabajo=',
								 'work=',
								 'help',
								 'HELP',
								 'no-gui',
								 ])

		glade_gui = True
		opciones_formateadas = {}

		for option, value in options:
			#if option == '-p':
			#	PAUSA = True
			#
			if option in ['-h', '--help']:
				uso()
				sys.exit(0)

			#
			#elif option in ['--trabajo', '--work']:
			#	if os.path.isdir(value):
			#		os.chdir(value)
			#

			elif option == '--no-gui':
				glade_gui = False

			else:
				opciones_formateadas[option] = value

		if glade_gui:
			interfaz = WiithonGUI()

		else:
			# crear interfaz terminal
			pass

		core = WiithonCORE(interfaz)
		interfaz.setCore(core)
		core.main(opciones_formateadas, arguments)

	except getopt.GetoptError:
		try:
			interfaz.alert('error', 'Programa ejecutado con las opciones incorrectas')
		except:
			print "Programa ejecutado con las opciones incorrectas"
		sys.exit(1)

	except AssertionError, mensaje:
		try:
			interfaz.alert("error", str(mensaje) )
		except:
			print str(mensaje)
		sys.exit(1)

# Esto es nuevo. Python mantiene constantemente un diccionario en el
# que almacena el curso de ejecución del script. Si __name__ (el
# diccionario) es igual a main quiere decir que acabamos de iniciar el
# script, entonces creamos una instancia de nuestra clase App y
# llamamos a mainloop

# Ricardo : ¿Para que cojones sirve esto? xD
# J.Luis:   Fácil: prueba a imprimir la variable __name__ en cualquier fichero Python.
#		Si estás, como ahora, en el que se ejecuta, valdrá '__main__'
#               Si estás, por ejemplo, en el módulo "core", valdrá 'core'.
#               Sirve para diferenciar cuando usas un archivo como módulo de "librería"
#               o como ejecutable

if __name__ == '__main__':
	App()

