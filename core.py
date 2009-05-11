#-*-coding: utf-8-*-

import sys , os , time , fnmatch
import gtk
import commands

from util import NonRepeatList
from util import Observable
import config
import util

class WiithonCORE(Observable):

	# rutas constantes
	DETECTOR_WBFS = config.WIITHON_FILES + "/wiithon_autodetectar.sh"
	DETECTOR_WBFS_LECTOR = config.WIITHON_FILES + "/wiithon_autodetectar_lector.sh"

	#globales publicas

	# Lista BIdimensional de particiones
	# indice 0 -> device  (/dev/sda1)
	# indice 1 -> Fabricante  (Maxtor)
	listaParticiones = None

	# indice (fila) de la partición seleccionado
	particionSeleccionada = 0

	# Lista de ficheros pendientes de añadir, estos pueden ser:
	# Tipo 1: Imagenes ISO
	# Tipo 2: Comprimidos RAR
	# Tipo 3: Carpetas
	# La lista de ficheros debería ser una cola mejor que una lista
	listaFicheros = NonRepeatList()

	#globales privadas
	
	# Variable para leer por clases externas de 0 a 1 el progreso de un archivo actual
	PORCENTUAL = 0

	#constructor
	def __init__(self):
		Observable.__init__(self, config.topics)

	# documenta esto
	def setPregunton(self, pregunton):
		self.pregunton = pregunton

	# Dumpea la ISO de un BACKUP y lo mete a la partición WBFS
	def instalarJuego(self , DEVICE):

		salida = ""
		print "Buscando un Disco de Wii ..."
		subProceso = util.getPopen(self.DETECTOR_WBFS_LECTOR)
		#Espera que acabe
		subProceso.wait()
		for linea in subProceso.stdout:
			salida = salida + linea

		# Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
		listaParticiones = NonRepeatList()
		if (salida <> ""):
			listaParticiones = salida[:-1].split("\n")

		numListaParticiones = len(listaParticiones)
		if(numListaParticiones<=0):
			print "No se ha encontrado ningún disco de la Wii"
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

		subProceso = util.getPopen(config.WBFS_APP+" -p "+DEVICE+" ls")
		#Espera que acabe
		returncode = subProceso.wait()

		if returncode == 0:
			salida = []
			for linea in subProceso.stdout:
				cachos = linea.split(";")
				if(len(cachos)==3):
				        #Elimina el salto de linea del ultimo cacho
					cachos[2] = cachos[2][:-1].split("\n")[0]
				        #Añade el juego a la lista
					salida.append( [ cachos[0] , cachos[1] , cachos[2] ] )
			salida.sort(ordenarPorNombre)

		else:
			self.notify('error', 'Debe identificarse como o sudo para acceder a la lista de juegos')

		return salida

	# Dada una lista de juegos, verifica su estado
	# Hay que separar la lógica de la presentación
	def verificarTodosLosJuegos(self , DEVICE , listaJuegos):
		# FIXME: en este método se debe ser root
		listaCorruptos = []
		numJuegos = len(listaJuegos)
		if(numJuegos > 0):
			print "--------------------------------------------------------------------------------"
			print "%6s\t%-40s\t%s" % ("IDGAME","TITULO" , "¿Corrupto?")
			print "--------------------------------------------------------------------------------"
			for juego in listaJuegos:
				salida = os.system(config.WBFS_APP+" -p "+DEVICE+" check "+juego[0])
				if( salida == 0 ):
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
	def anadirISO(self , DEVICE , ISO):
		'''
		try:
			salida = os.system(config.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\"")
			return salida == 0
		except KeyboardInterrupt:
			return False
		'''
		comando = config.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\""
		entrada, salida = os.popen2(comando)
		linea = ""
		salir = False
		while not salir:
			letra = salida.read(1)
			if(letra == '\n'):
				linea = linea.strip()
				if(linea != "FIN_ADD"):
					try:
						cachos = linea.split(";")
						porcentaje = float(cachos[0])
						hora = int(cachos[1])
						minutos = int(cachos[2])
						segundos = int(cachos[3])
						print "LLeva un %.2f%% quedan %d horas, %d minutos, %d segundos" % ( porcentaje , hora , minutos , segundos )
						self.PORCENTUAL = porcentaje / 100
					except TypeError:
						pass
					linea = ""
				else:
					salir = True
			linea = linea + letra
		entrada.close()
		salida.close()
		return True

	# renombra el ISO de un IDGAME que esta en DEVICE
	def renombrarISO(self , DEVICE , IDGAME , NUEVO_NOMBRE):
		# FIXME: debe ser root
		try:
			salida = os.system(config.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\"")
			return salida == 0
		except KeyboardInterrupt:
			return False
	
	# borra el juego IDGAME
	def borrarJuego(self , DEVICE , IDGAME):
		# FIXME: debe ser root
		try:
			salida = os.system(config.WBFS_APP+" -p "+DEVICE+" rm "+IDGAME)
			return salida == 0
		except KeyboardInterrupt:
			return False
		except TypeError:
			return False

	# extrae el juego IDGAME
	def extraerJuego(self , DEVICE , IDGAME):
		# FIXME: debe ser root
		try:
			salida = os.system(config.WBFS_APP+" -p "+DEVICE+" extract "+IDGAME)
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

		for i in glob_get_dirs(path):
			res = rec_glob(path + i, mask)
			l = l + res

		try:
			for i in os.listdir(path):

				ii = i
				i = path + i
				if os.path.isfile(i):
						# Lo parcheo para que no diferencie mayuculas
						#if fnmatch.fnmatch(ii, mask):
						if fnmatch.fnmatch(ii.lower() , mask.lower()):
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
				os.system("mogrify -resize 160x225 " + destino)
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
		return self.listaParticiones

	# Procedimiento que refresca la lista de particiones
	def refrescarParticionWBFS(self):

		salida = ""
		subProceso = util.getPopen(self.DETECTOR_WBFS)
		#Espera que acabe
		subProceso.wait()
		#acumulo todo el stdout
		for linea in subProceso.stdout:
			salida = salida + linea
	
		# Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
		self.listaParticiones = []
		if (salida <> ""):
			self.listaParticiones = salida[:-1].split("\n")

		# Borramos los elementos que no contengan /dev/
		# los que tengan /dev/ serán particiones wbfs en formato DEVICE:FABRICANTE ej. /dev/sda1:Sandisk
		i = 0
		while ( i  < len(self.listaParticiones) ):
			if(self.listaParticiones[i].find("/dev/") == -1):
				del listaParticiones[i]
			else: # es una particion WBFS
				i = i + 1

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
			salida = os.system(comando)
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
			#print self.listaParticiones[self.particionSeleccionada].split(":")[0]
			return self.listaParticiones[self.particionSeleccionada].split(":")[0]
		except IndexError:
			raise AssertionError, "Error obteniendo información del dispositivo"
		
	def getFabricanteSeleccionado(self):
		try:
			#print self.listaParticiones[self.particionSeleccionada].split(":")[1]
			return self.listaParticiones[self.particionSeleccionada].split(":")[1]
		except IndexError:
			# Repasar que pasa cuando no hay fabricante
			raise AssertionError, "Error obteniendo información del fabricante"

	def getListaFicheros(self):
		return self.listaFicheros

	def setInterfaz(self , interfaz):
		self.interfaz = interfaz
		
	def encolar(self , lista):
		self.listaFicheros.extend( lista )
		
	def vaciarLista(self , lista):
		# vaciamos la listaFicheros a procesar
		while len( lista ) > 0:
			lista.remove( lista[0] )

