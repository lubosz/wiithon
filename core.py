#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import sys , os , time , fnmatch
import gtk
import commands
import gettext

from util import NonRepeatList
import config
import util

from Queue import Queue
from threading import Thread
import subprocess

class WiithonCORE:

	#globales publicas

	# Lista BIdimensional de particiones
	# indice 0 -> device  (/dev/sda1)
	# indice 1 -> Fabricante  (Maxtor)
	listaParticiones = None

	# indice (fila) de la partición seleccionado
	particionSeleccionada = 0
	
	# Estructura sincrona para comunicacion entre hilos
	mensajes = None

	#constructor
	def __init__(self):
		# cola sincronizada (productor-consumidor)
		self.mensajes = Queue()
		
	def getMensajes(self):
		return self.mensajes

	def nuevoMensaje(self , mensaje):
		self.mensajes.put(mensaje)

	# Dumpea la ISO de un BACKUP y lo mete a la partición WBFS
	def instalarJuego(self , DEVICE):

		salida = ""
		print "Buscando un Disco de Wii ..."
		
		salida = util.getSTDOUT( config.DETECTOR_WBFS_LECTOR )

		# Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
		listaParticiones = NonRepeatList()
		if (salida <> ""):
			listaParticiones = salida[:-1].split("\n")

		numListaParticiones = len(listaParticiones)
		if(numListaParticiones<=0):
			print gettext.gettext("No se ha encontrado ningún disco de la Wii")
		elif(numListaParticiones > 1):
			print "Hay más de un juego de la Wii, deja solo 1 para eliminar la ambigüedad"
		else:# 1 juego de wii
			try:
				cachos = listaParticiones[0].split(":")
				LECTOR_DVD = cachos[0]
				FABRICANTE_DVD = cachos[1]
				MAGIC_DVD = util.getMagicISO(LECTOR_DVD)
				SALIDA = os.getcwd()+"/"+MAGIC_DVD+".iso"
				reemplazada = False
				if (os.path.exists(SALIDA)):
					print "Ya hay una ISO en : " + SALIDA
					respuesta = raw_input("Desea reemplazarla (S/N) : ")
					if(respuesta.lower() == "s" or respuesta.lower() == "si"):
						reemplazada = False
					else:
						reemplazada = True
				print FABRICANTE_DVD + " a un ISO temporal de 4.4GB en = " + MAGIC_DVD+".iso ..."
				if( reemplazada or (os.system("dd if="+LECTOR_DVD+" of="+SALIDA+" bs=1M")==0) ):
					if ( self.anadirISO(DEVICE , SALIDA)):
						if( self.descargarCaratula(MAGIC_DVD) ):
							print "Caratula descargada como "+os.getcwd()+"/"+MAGIC_DVD+".png"
						else:
							print "No se ha encontrado caratula para el juego " + MAGIC_DVD
					else:
						print "Error al pasar la ISO al disco duro"
					print "wiithon no borra la ISO temporal, puedes borrarla si no la necesitas"
				else:
					print "Error al dumpear la ISO"
			except KeyboardInterrupt:
				print "Interrumpido por el usuario"

	# Obtiene un list de juegos en una tabla de 3 columnas:
	# index 0 -> IDGAME o identificador único del juego
	# index 1 -> Nombre del juego
	# index 2 -> Tamaño en GB redondeado a 2 cifras
	def getListaJuegos(self , DEVICE):
		def ordenarPorNombre(juego1 , juego2):
			return cmp( juego1[1].lower() , juego2[1].lower() )


		'''
		subProceso = util.getPopen( config.WBFS_APP+" -p "+DEVICE+" ls" )
		subProceso.wait()
		'''
		lineas = util.getSTDOUT_iterador( config.WBFS_APP+" -p "+DEVICE+" ls" )

		salida = []
		for linea in lineas:
			cachos = linea.strip().split(";")
			if(len(cachos)==3):
				salida.append( [ cachos[0] , cachos[1] , cachos[2] ] )
		salida.sort(ordenarPorNombre)
		return salida
		
	def verificarJuego(self , DEVICE , IDGAME):
		comando = config.WBFS_APP+" -p "+DEVICE+" check "+IDGAME
		salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
		return ( salida == 0 )

	# Dada una lista de juegos, verifica su estado
	# Hay que separar la lógica de la presentación
	def verificarTodosLosJuegos(self , DEVICE , listaJuegos):
		listaCorruptos = []
		numJuegos = len(listaJuegos)
		if(numJuegos > 0):
			print "--------------------------------------------------------------------------------"
			print "%6s\t%-40s\t%s" % ("IDGAME","TITULO" , "¿Corrupto?")
			print "--------------------------------------------------------------------------------"
			for juego in listaJuegos:
				if( self.verificarJuego( DEVICE , juego[0] ) ):
					corrupto = "NO ESTA CORRUPTO"
				else:
					corrupto = "¡¡ ESTA CORRUPTO !!"
					listaCorruptos.append(juego)
				print "%s\t%-40s\t%s" % ( juego[0] , juego[1] , corrupto)
		numCorruptos = len(listaCorruptos)
		if (numCorruptos > 0):
			print "--------------------------------------------------------------------------------"
			print "Lista de juegos corruptos"
			print "--------------------------------------------------------------------------------"
			for juego in listaCorruptos:
				print "%s\t%-40s" % ( juego[0] , juego[1] )
			print "--------------------------------------------------------------------------------"
			print "Hay *"+str(numCorruptos)+"* juegos corruptos se recomienda que los desinstale"
			print "--------------------------------------------------------------------------------"
			respuesta = raw_input("¿Quieres desinstalarlos? (S/N) ")
			if(respuesta.lower() == "s" or respuesta.lower() == "si"):
				for juego in listaCorruptos:
					if (borrarJuego(DEVICE , juego[0])):
						print juego[0] + " borrado correctamente"
					else:
						print "ERROR : " + juego[0] + " NO se ha borrado correctamente"
			else:
				print "Saliendo. No se ha desinstalado nada"


	# Esta forma parte del GUI, es una forma del CLI de seleccionar 1 juego
	def get_IDJUEGO_de_Lista(self , DEVICE , listaJuegos):
		numJuegos = len(listaJuegos)
		if(numJuegos > 0):
			print "--------------------------------------------------------------------------------"
			print "%3s\t%6s\t%-40s\t%7s\t%6s" % ("NUM","IDGAME","TITULO","TAMAÑO" , "¿Car.?")
			print "--------------------------------------------------------------------------------"
			i = 1
			for juego in listaJuegos:
				ocupado = float(juego[2])
				if (self.existeCaratula(juego[0])):
					caratula = "SI"
				else:
					caratula = "NO"
				print "%3s\t%s\t%-40s\t%.2f GB\t%6s" % ( i , juego[0] , juego[1] , ocupado , caratula)
				if ( (i % config.NUM_LINEAS_PAUSA) == 0 ):
					raw_input("Presiona cualquier tecla para mostrar "+str(config.NUM_LINEAS_PAUSA)+" lineas más")
				i = i + 1
			print "--------------------------------------------------------------------------------"

			try:
				numJuego = int( raw_input("¿Indique el NUM del juego? : ") )
				# 1 <= numJuego <= numJuegos
				if ((1 <= numJuego) and (numJuego <= numJuegos)):
					try:
						return listaJuegos[numJuego-1][0]
					except IndexError:
						print "Numero fuera de rango"
			except ValueError:
				print "El numero dado es incorrecto"
		return "DESCONOCIDO"

	# añade un *ISO* a un *DEVICE*
	# durante el proceso va actualizando PORCENTUAL
	# Actualmente no esta bien desarrollada, por problemas con el "read"
	def anadirISO(self , DEVICE , ISO , ficheroSalida=None):
		try:
			comando = config.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\""
			salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
			return salida == 0
		except KeyboardInterrupt:
			return False

	# renombra el ISO de un IDGAME que esta en DEVICE
	def renombrarISO(self , DEVICE , IDGAME , NUEVO_NOMBRE):
		try:
			comando = config.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\""
			salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
			return salida == 0
		except KeyboardInterrupt:
			return False

	# borra el juego IDGAME
	def borrarJuego(self , DEVICE , IDGAME):
		try:
			comando = config.WBFS_APP+" -p "+DEVICE+" rm "+IDGAME
			salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
			return salida == 0
		except KeyboardInterrupt:
			return False
		except TypeError:
			return False

	# extrae el juego IDGAME
	def extraerJuego(self , DEVICE , IDGAME):
		try:
			comando = config.WBFS_APP+" -p "+DEVICE+" extract "+IDGAME
			salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
			return salida == 0
		except KeyboardInterrupt:
			return False

	# Devuelve una lista de directorios del directorio "path"
	# http://newspiritcompany.infogami.com/recursive_glob_py
	def glob_get_dirs(self , path):
		d = []
		try:
			for i in os.listdir(path):
				if os.path.isdir(path+i):
					d.append(os.path.basename(i))

		except NameError, ne:
			print "NameError thrown=", ne
		except:
			pass
		return d

	# Devuelve la lista de resultados que cumplen la Exp.Reg.
	# Recorre a partir de "path" y recursivamente.
	def rec_glob(self , path , mask):
		l = []

		if path[-1] != '/':
			path = path + '/'

		for i in self.glob_get_dirs(path):
			res = self.rec_glob(path + i, mask)
			l = l + res

		try:
			for i in os.listdir(path):
				ii = i
				i = path + i
				if os.path.isfile(i):
					if fnmatch.fnmatch( ii.lower() , mask.lower() ):
						l.append(i)
		except NameError, ne:
			print "NameError=", ne
		except:
			pass
		return l

	def existeDisco(self , IDGAME):
		destino = os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")
		return (os.path.exists(destino))

	def descargarDisco(self , IDGAME):
		if (self.existeDisco(IDGAME)):
			return True
		else:
			origen = 'http://www.theotherzone.com/wii/diskart/160/160/' + IDGAME + '.png'
			salida = os.system("wget --no-cache --directory-prefix=\""+config.HOME_WIITHON_DISCOS+"\" " + origen)
			descargada = (salida == 0)
			if descargada:
				destino = os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")
				os.system("mogrify -resize 160x160 " + destino)
			return descargada

	# Nos dice si existe la caratula del juego "IDGAME"
	def existeCaratula(self , IDGAME):
		destino = os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")
		return (os.path.exists(destino))

	# Descarga una caratula de "IDGAME"
	def descargarCaratula(self , IDGAME, panoramica = False):
		if (self.existeCaratula(IDGAME)):
			return True
		else:
			'''
			diskart/160/160/
			3d/160/225/
			widescreen/
			'''
			origen = 'http://www.theotherzone.com/wii/'
			regiones = ['pal' , 'ntsc' , 'ntscj']
			if(panoramica):
				origen = origen + "widescreen/"
			descargada = False
			i = 0
			while ( not descargada and i<len(regiones)  ):
				origenGen = origen + regiones[i] + "/" + IDGAME + ".png"
				salida = os.system("wget --no-cache --directory-prefix=\""+config.HOME_WIITHON_CARATULAS+"\" " + origenGen)
				descargada = (salida == 0)
				if descargada:
					destino = os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")
					os.system("mogrify -resize 160x225 " + destino)
				i = i + 1
			return descargada

	# Descarga todos las caratulas de una lista de juegos
	def descargarTodasLasCaratulaYDiscos(self , DEVICE , listaJuegos , panoramica = False):
		ok = True
		for juego in listaJuegos:
			if ( not self.descargarCaratula( juego[0] , panoramica ) ):
				ok = False
			if ( not self.descargarDisco( juego[0] ) ):
				ok = False
		return ok

	# Devuelve la lista de particiones
	def getListaParticiones(self):
		self.refrescarParticionWBFS()
		return self.listaParticiones

	# Procedimiento que refresca la lista de particiones
	def refrescarParticionWBFS(self):
		salida = util.getSTDOUT( config.DETECTOR_WBFS , False)

		self.listaParticiones = []

		for part in salida[:-1].split("\n"):
			if part.find("/dev/") != -1:
				self.listaParticiones.append(part)

	# Devuelve el nombre del ISO que hay dentro de un RAR
	def getNombreISOenRAR(self , nombreRAR):
		comando = "rar lt -c- '"+nombreRAR+"' | grep -i '.iso' | awk -F'.iso'  '{print $1}' | awk -F' ' '{print $0\".iso\"}' | sed 's/^ *//' | sed 's/ *$//'"
		tuberia = os.popen(comando)
		salida_estandar = tuberia.readlines()
		tuberia.close()
		for linea in salida_estandar:
			# Quitar el salto de linea
			linea = linea[:-1]
			if( util.getExtension(linea)=="iso" ):
				return linea
		return ""

	# Descomprime todos los ISO de un RAR (FIXME: se espera que solo haya 1)
	def descomprimirRARconISODentro(self , nombreRAR ):
		try:
			comando = "rar e -o- \""+nombreRAR+"\" \"*.iso\""
			salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open("/dev/null","w"))
			return (salida == 0)
		except KeyboardInterrupt:
			return False

	# Se pasa como parametro ej: /dev/sdb2
	def redimensionarParticionWBFS(self , particion):
		# 57 42 46 53 00 0b 85 30
		# 57 42 46 53 00 29 ea eb

		comando = "fdisk -lu | grep -v 'MB' | grep '"+particion+"' | awk '{print $3-$2+1}'"
		entrada, salida = os.popen2(comando)
		salida = salida.read()

		offset = 0x4
		valor = int(salida)

		print "Se va escribir en la particion %s : %x:%x" % ( particion , offset , valor )
		respuesta = raw_input("¿Seguir? (S/N)\n")

		if (respuesta.lower() == 's'):
			byte1 = (valor & 0xFF000000) >> 8*3
			byte2 = (valor & 0x00FF0000) >> 8*2
			byte3 = (valor & 0x0000FF00) >> 8
			byte4 = (valor & 0x000000FF)

			f = open(particion , "wb")
			f.seek(offset , os.SEEK_SET)
			f.write('%c%c%c%c' % ( byte1 , byte2 , byte3 , byte4 ) )
			f.close()
			print "4 bytes escritos."
		else:
			print "sin cambios."

	def setParticionSeleccionada(self , particionSeleccionada):
		self.particionSeleccionada = particionSeleccionada

	def getDeviceSeleccionado(self):
		try:
			return self.listaParticiones[self.particionSeleccionada].split(":")[0]
		except IndexError:
			raise AssertionError, "Error obteniendo información del dispositivo"

	def getFabricanteSeleccionado(self):
		try:
			return self.listaParticiones[self.particionSeleccionada].split(":")[1]
		except IndexError:
			# Repasar que pasa cuando no hay fabricante
			raise AssertionError, "Error obteniendo información del fabricante"

	def setInterfaz(self , interfaz):
		self.interfaz = interfaz

class HiloDescargarTodasLasCaratulaYDiscos(Thread):
	def __init__( self , core , listaJuegos):
		Thread.__init__(self)
		self.core = core
		self.DEVICE = core.getDeviceSeleccionado()
		self.listaJuegos = listaJuegos
		self.interrumpido = False

	def run( self ):
		i = 0
		while not self.interrumpido and i<len(self.listaJuegos):
			juego = self.listaJuegos[i]
			self.core.descargarCaratula( juego[0] )
			self.core.descargarDisco( juego[0] )
			i = i + 1

	def interrumpir(self):
		self.interrumpido = True

