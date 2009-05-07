#-*-coding: utf-8-*-

import sys , os , subprocess , time , glob , fnmatch
import gtk
import commands

from util import NonRepeatList
import config

class WiithonCORE:

	WBFS_APP = config.WIITHON_FILES + "/wbfs"
	DETECTOR_WBFS = config.WIITHON_FILES + "/wiithon_autodetectar.sh"
	DETECTOR_WBFS_LECTOR = config.WIITHON_FILES + "/wiithon_autodetectar_lector.sh"

	ISO = ""
	COMANDO = ""
	ID_JUEGO = ""
	PAUSA = False
	FABRICANTE = ""
	listaFicheros = NonRepeatList()
	PARAMETROS = NonRepeatList()
	BLACK_LIST = "/\"\'$&|[]"
	GUI = True
	NUM_LINEAS_PAUSA = 21
	borrarISODescomprimida = False

	def __init__(self , interfaz):
		self.interfaz = interfaz
	
		assert os.geteuid() == 0, 'Debes ser usuario privilegiado para que wiithon pueda acceder a su partición WBFS'

		if not self.comprobarExistencia(config.HOME_WIITHON):
			self.informarAcuerdo()

		self.DEVICE = self.buscarParticionWBFS()

		self.listaJuegos = self.getListaJuegos(self.DEVICE)
		self.hayJuegos = len(self.listaJuegos) > 0

	def instalarJuego(self , DEVICE):
		salida = ""
		print "Buscando un Disco de Wii ..."
		subProceso = self.getPopen(self.DETECTOR_WBFS_LECTOR)
		#Espera que acabe
		subProceso.wait()
		for linea in subProceso.stdout:
			salida = salida + linea

		# Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
		listaParticiones = []
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
				MAGIC_DVD = self.getMagicISO(LECTOR_DVD)
				SALIDA = os.getcwd()+"/"+MAGIC_DVD+".iso"
				reemplazada = False
				if (self.comprobarExistencia(SALIDA)):
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

	def comprobarExistencia(self , fichero):
		return os.path.exists(fichero)

	def tieneCaracteresRaros(self , cadena):
		# Nos dice si *cadena* tiene caracteres raros dados por una lista negra global
		for i in range(len(cadena)):
			for j in range(len(self.BLACK_LIST)):
				if (cadena[i]==self.BLACK_LIST[j]):
					return True
		return False

	def eliminarComillas(self , string):
		'''
		Primera letra			[:1]
		Ultima letra			[-1:]
		Todo excepto primera letra	[1:]
		Todo excepto ultima letra	[:-1]
		'''
		if( string[:1]=="'" or string[:1]=="\"" ):
			if( string[-1:]=="'" or string[-1:]=="\"" ):
				string = string[1:]
				string = string[:-1]
		return string

	def getExtension(self , fichero):
		fichero = self.eliminarComillas(fichero)
		posPunto = fichero.rfind(".")
		return fichero[posPunto+1:len(fichero)].lower()

	def getNombreFichero(self , fichero):
		fichero = eliminarComillas(fichero)
		posPunto = fichero.rfind(".")
		return fichero[0:posPunto]

	def getMagicISO(self , imagenISO):
		f = open(imagenISO , "r")
		magic = f.read(6)
		f.close()
		return magic

	def getListaJuegos(self , DEVICE):

		def ordenarPorNombre(juego1 , juego2):
			return cmp( juego1[1].lower() , juego2[1].lower() )

		subProceso = self.getPopen(""+self.WBFS_APP+" -p "+DEVICE+" ls")
		#Espera que acabe
		subProceso.wait()
		salida = []
		for linea in subProceso.stdout:
			cachos = linea.split(";")
			if(len(cachos)==3):
				#Elimina el salto de linea del ultimo cacho
				cachos[2] = cachos[2][:-1].split("\n")[0]
				#Añade el juego a la lista
				salida.append( [ cachos[0] , cachos[1] , cachos[2] ] )
		salida.sort(ordenarPorNombre)
		return salida

	def verificarTodosLosJuegos(self , DEVICE , listaJuegos):
		listaCorruptos = []
		numJuegos = len(listaJuegos)
		if(numJuegos > 0):
			print "--------------------------------------------------------------------------------"
			print "%6s\t%-40s\t%s" % ("IDGAME","TITULO" , "¿Corrupto?")
			print "--------------------------------------------------------------------------------"
			for juego in listaJuegos:
				salida = os.system(""+self.WBFS_APP+" -p "+DEVICE+" check "+juego[0])
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
				print "%s\t%-40s" % ( juego[0] , juego[1])
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
				if ( (i % NUM_LINEAS_PAUSA) == 0 ):
					raw_input("Presiona cualquier tecla para mostrar "+str(NUM_LINEAS_PAUSA)+" lineas más")
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

	def listarISOs(self , DEVICE , listaJuegos):
		numJuegos = len(listaJuegos)
		if(numJuegos > 0):
			print "--------------------------------------------------------------------------------"
			print "%6s\t%-55s\t%7s\t%6s" % ("IDGAME","TITULO","TAMAÑO" , "¿Car.?")
			print "--------------------------------------------------------------------------------"
			i = 1
			for juego in listaJuegos:
				ocupado = float(juego[2])
				if (self.existeCaratula(juego[0])):
					caratula = "SI"
				else:
					caratula = "NO"
				print "%s\t%-55s\t%.2f GB\t%6s" % ( juego[0] , juego[1] , ocupado , caratula)
				if ( (i % NUM_LINEAS_PAUSA) == 0 ):
					raw_input("Presiona cualquier tecla para mostrar "+str(NUM_LINEAS_PAUSA)+" lineas más")
				i = i + 1
			print "--------------------------------------------------------------------------------"
			print "\t\t\t\t\t\t\t%d juegos de WII" % numJuegos
		return numJuegos

	def mostrarEspacioLibre(self , DEVICE):
		subProceso = getPopen(""+self.WBFS_APP+" -p "+DEVICE+" df")
		subProceso.wait()
		salida = ""
		for linea in subProceso.stdout:
			salida = salida + linea
		cachos = salida.split(";")
		if(len(cachos) == 3):
			print "\t\t\t\t\t\t\tUsado : %.2f GB" % float(cachos[0])
			print "\t\t\t\t\t\t\tLibre : %.2f GB" % float(cachos[1])
			print "\t\t\t\t\t\t\tTotal : %.2f GB" % float(cachos[2])
			return True
		else:
			return False

	def anadirISO(self , DEVICE , ISO , progreso = None):
		'''
		try:
			salida = os.system(""+self.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\"")
			return salida == 0
		except KeyboardInterrupt:
			return False
		'''
		comando = ""+self.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\""
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
						if(progreso != None):
							porcentual = porcentaje / 100
							print porcentual
							progreso.set_fraction( porcentual )
					except TypeError:
						pass
					linea = ""
				else:
					salir = True
			linea = linea + letra
		entrada.close()
		salida.close()
		return True

	def renombrarISO(self , DEVICE , IDGAME , NUEVO_NOMBRE):
		try:
			salida = os.system(""+self.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\"")
			return salida == 0
		except KeyboardInterrupt:
			return False

	def borrarJuego(self , DEVICE , ID_JUEGO):
		try:
			salida = os.system(""+self.WBFS_APP+" -p "+DEVICE+" rm "+ID_JUEGO)
			return salida == 0
		except KeyboardInterrupt:
			return False
		except TypeError:
			return False

	def extraerJuego(self , DEVICE , ID_JUEGO):
		try:
			salida = os.system(""+self.WBFS_APP+" -p "+DEVICE+" extract "+ID_JUEGO)
			return salida == 0
		except KeyboardInterrupt:
			return False

	def getPopen(self , comando):
		sp = subprocess
		return sp.Popen(comando.split() , stdout=sp.PIPE ,stderr=sp.STDOUT , close_fds=False , shell=False, universal_newlines= True)

	def glob_get_dirs(self , path):
		'''
		Devuelve una lista de directorios del directorio "path"
		http://newspiritcompany.infogami.com/recursive_glob_py
		'''
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

	def informarAcuerdo(self):
		res = self.interfaz.alert('question',
			       'El equipo de Wiithon no se hace responsable de la aplicacion ni de la perdida de datos.\nNo obstante, la particion NO va ha ser formateada.\nEsta aplicación añade, borra y lista juegos explicamente mediante la ayuda de %s.\nEsta información no volverá a aparecer si acepta el acuerdo.\n¿Está de acuerdo?'
			       %(os.path.basename(self.WBFS_APP))
			       )

		# gtk.RESPONSE_YES ¿que constante es GTK es 1?
		if res == 1:
			os.mkdir( config.HOME_WIITHON )
		else:
			raise AttributeError("No puedes usar esta aplicacion si no estas deacuerdo")

	def existeCaratula(self , IDGAME):
		return (self.comprobarExistencia(IDGAME+".png"))

	def descargarCaratula(self , IDGAME, panoramica = False):
		if (self.existeCaratula(IDGAME)):
			return True
		else:
			origen = 'http://www.theotherzone.com/wii/'
			regiones = ['pal' , 'ntsc' , 'ntscj']
			if(panoramica):
				origen = origen + "widescreen/"
			descargada = False
			i = 0
			while ( not descargada and i<len(regiones)  ):
				origenGen = origen + regiones[i] + "/" + IDGAME + ".png"
				salida = os.system("wget --no-cache " + origenGen)
				descargada = (salida == 0)
				if descargada:
					os.system("mogrify -resize 160x225 "+IDGAME+".png")
				i = i + 1
			return descargada

	def descargarTodasLasCaratula(self , DEVICE , listaJuegos , panoramica):
		ok = True
		for juego in listaJuegos:
			if ( not self.descargarCaratula(juego[0] , panoramica) ):
				ok = False
		return ok

	def buscarParticionWBFS(self):
		DEVICE = ""
		salida = ""
		subProceso = self.getPopen(self.DETECTOR_WBFS)
		#Espera que acabe
		subProceso.wait()
		for linea in subProceso.stdout:
			salida = salida + linea

		# Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
		listaParticiones = []
		if (salida <> ""):
			listaParticiones = salida[:-1].split("\n")

		# Borramos los elementos que no contengan /dev/
		# los que tengan /dev/ se corta por : y se coge el primer cacho
		i = 0
		while ( i  < len(listaParticiones) ):
			if(listaParticiones[i].find("/dev/") == -1):
				del listaParticiones[i]
			else: # es una particion WBFS
				i = i + 1

		if(len(listaParticiones) <= 0):
			raise AttributeError("No se ha encontrado ningun dispositivo con particion WBFS.")
		elif(len(listaParticiones) > 1):
			haElegido = False
			while( not haElegido ):
				try:
					DEVICE = zenity_lista("Lista de particiones autodetectadas : " , listaParticiones)
					try:
						cachos = DEVICE.split(":")
						DEVICE = cachos[0]
						FABRICANTE = cachos[1]
					except:
						raise AttributeError("Error obteniendo información del dispositivo")
					haElegido = True
				except IndexError:
					raise AttributeError("Fuera de rango")
				except ValueError:
					raise AttributeError("Valor incorrecto")
		else: # solo hay 1 partición
			DEVICE = listaParticiones[0]
			try:
				cachos = DEVICE.split(":")
				DEVICE = cachos[0]
				FABRICANTE = cachos[1]
			except:
				raise AttributeError("Error obteniendo información del dispositivo")

		return DEVICE

	def getNombreISOenRAR(self , nombreRAR):
		comando = "rar lt -c- '"+nombreRAR+"' | grep -i '.iso' | awk -F'.iso'  '{print $1}' | awk -F' ' '{print $0\".iso\"}' | sed 's/^ *//' | sed 's/ *$//'"
		tuberia = os.popen(comando)
		salida_estandar = tuberia.readlines()
		tuberia.close()
		for linea in salida_estandar:
			# Quitar el salto de linea
			linea = linea[:-1]
			if( getExtension(linea)=="iso" ):
				return linea
		return ""

	def descomprimirRARconISODentro(self , nombreRAR , nombreISO ):
		try:
			comando = "rar e -o- \""+nombreRAR+"\" \"*.iso\""
			salida = os.system(comando)
			return (salida == 0)
		except KeyboardInterrupt:
			return False

	# En desarrollo
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

	def zenity_lista(self , titulo , listaOpciones):
		comando = "zenity --list --column=\""+titulo+"\""
		for opcion in listaOpciones:
			comando = comando +  " \""+opcion+"\""
		entrada, salida = os.popen2(comando)
		salida = salida.read()
		salida = salida.strip()
		return salida

	############## MAIN ###########################
	def main(self, opciones, argumentos):

		self.PARAMETROS.extend(argumentos)
		self.numParametros = len(self.PARAMETROS)
		self.GUI = self.hayGUI()

		if self.GUI:
			self.interfaz.wg_principal.show()
			gtk.main()

		elif self.PARAMETROS[0].lower() == "listar" or self.PARAMETROS[0].lower() == "ls" :
			if(self.hayJuegos):
				print "Listando juegos de : " + self.DEVICE + " " + self.FABRICANTE
				self.listarISOs(self.DEVICE , self.listaJuegos)
				self.mostrarEspacioLibre(self.DEVICE)
			else:
				print "No tienes instalado ningún juego en " + self.DEVICE + " " + self.FABRICANTE
		elif ( self.PARAMETROS[0].lower() == "instalar" or self.PARAMETROS[0].lower() == "install"):
			try:
				print "Inserte un juego de la Wii en su lector de DVD ..."
				raw_input("Pulse cualquier tecla para continuar ... ")
				self.instalarJuego(DEVICE)
			except KeyboardInterrupt:
				print
		elif ( self.PARAMETROS[0].lower() == "desinstalar" or self.PARAMETROS[0].lower() == "borrar" or self.PARAMETROS[0].lower() == "rm" or self.PARAMETROS[0].lower() == "quitar"):
			if(self.hayJuegos):
				if(self.numParametros >= 2):
					parametro = self.PARAMETROS[1]
					if (self.getExtension(parametro) == "iso"):
						IDGAME = self.getMagicISO(parametro)
					else:
						IDGAME = parametro
				else:
					IDGAME = self.get_IDJUEGO_de_Lista(self.DEVICE , self.listaJuegos)
				print "Borrar juego con ID : " + self.IDGAME + " en particion " + self.DEVICE + " " + self.FABRICANTE
				if( self.borrarJuego(self.DEVICE , self.IDGAME) ):
					print "Juego borrado correctmente. Refrescando lista ..."
					if( self.comprobarExistencia(self.DEVICE) and self.listarISOs(self.DEVICE , self.listaJuegos)>0 and self.mostrarEspacioLibre(self.DEVICE) ):
						print "juego " + IDGAME + " borrado correctamente"
					else:
						print "Error al refrescar o no hay Juegos que listar"
				else:
					print "ERROR borrando el juego " + ID_JUEGO
			else:
				print "No hay Juegos para borrar"

		elif ( self.PARAMETROS[0].lower() == "caratula" or self.PARAMETROS[0].lower() == "cover"):
			if(self.hayJuegos):
				if(self.numParametros >= 2):
					IDGAME = self.PARAMETROS[1]
				else:
					IDGAME = self.get_IDJUEGO_de_Lista(self.DEVICE , self.listaJuegos)
				if(self.descargarCaratula(IDGAME)):
					print "OK, descargado " + IDGAME + ".png"
				else:
					print "ERROR, descargando " + IDGAME + ".png"
			else:
				print "No hay Juegos para descargar una caratula"
		elif ( self.PARAMETROS[0].lower() == "caratulas" or self.PARAMETROS[0].lower() == "covers"):
			if(self.hayJuegos):
				panoramico = False
				if(self.numParametros >= 2): # 3 parametros
					panoramico = self.PARAMETROS[1].lower() == "panoramico" or self.PARAMETROS[1].lower() == "widescreen"
					if (panoramico):
						print "Se descargaran en formato paronámico"
				if(self.descargarTodasLasCaratula(self.DEVICE , self.listaJuegos , panoramico)):
					print "OK, todas las caratulas se han descagado"
				else:
					print "ERROR, descargando alguna caratula"
					print "Vuelvelo a intentar o mira en : http://www.theotherzone.com/wii/"
			else:
				print "No hay Juegos para descargar caratulas"
		elif ( self.PARAMETROS[0].lower() == "renombrar" or self.PARAMETROS[0].lower() == "rename" or self.PARAMETROS[0].lower() == "r"):
			if(self.hayJuegos):
				if(self.numParametros >= 3):
					IDGAME = self.PARAMETROS[1]
					NUEVO_NOMBRE = self.PARAMETROS[2]
				else:
					IDGAME = self.get_IDJUEGO_de_Lista(self.DEVICE , self.listaJuegos)
					NUEVO_NOMBRE = raw_input("Escriba el nuevo nombre : ")
				print "Renombrar juego ID : " + IDGAME + " como " + NUEVO_NOMBRE
				if ( self.renombrarISO( self.DEVICE , IDGAME , NUEVO_NOMBRE ) ):
					print "Refrescando lista ..."
					if( self.comprobarExistencia(self.DEVICE) and self.listarISOs(self.DEVICE , self.listaJuegos)>0 and self.mostrarEspacioLibre(self.DEVICE) ):
						print "ISO renombrada correctamente a \""+NUEVO_NOMBRE+"\""
					else:
						print "Renombrado OK aunque ocurrio un error al refrescar"
				else:
					print "ERROR al renombrar"
			else:
				print "No hay Juegos para renombrar"
		elif ( self.PARAMETROS[0].lower() == "check" or self.PARAMETROS[0].lower() == "comprobar" or self.PARAMETROS[0].lower() == "scandisk"):
			if(self.hayJuegos):
				print "Verificando todos los juegos de la particion " + self.DEVICE + " " + self.FABRICANTE
				self.verificarTodosLosJuegos(self.DEVICE , self.listaJuegos)
			else:
				print "No hay Juegos para verificar"
		elif ( self.PARAMETROS[0].lower() == "extraer" or self.PARAMETROS[0].lower() == "x"):
			if(self.hayJuegos):
				if(self.numParametros >= 2):
					ID_JUEGO = self.PARAMETROS[1]
				else:
					ID_JUEGO = self.get_IDJUEGO_de_Lista(self.DEVICE , self.listaJuegos)
				print "Extraer ISO de juego con ID : " + ID_JUEGO + " en particion " + self.DEVICE + " " + self.FABRICANTE
				if( self.extraerJuego(self.DEVICE , ID_JUEGO) ):
					print "Juego " + ID_JUEGO + " extraido OK"
				else:
					print "ERROR extrayendo la ISO de "+ID_JUEGO
			else:
				print "No hay Juegos para extraer"
		elif ( self.PARAMETROS[0].lower() == "ayuda" or self.PARAMETROS[0].lower() == "h" or self.PARAMETROS[0].lower() == "help" ):
			self.uso()
			sys.exit(1)
		else:
			#Los parametros es una lista de ISOS explicita
			for parametro in self.PARAMETROS:
				if ( os.path.isdir(parametro) or parametro.lower() == "buscar" or parametro.lower() == "meter" or parametro.lower() == "-r" or parametro.lower() == "metertodo" or parametro.lower() == "buscartodo" ):
					if( not os.path.isdir(parametro) ):
						archivo = "."

					print "Buscando en "+os.path.dirname(archivo)+" ficheros RAR ... ",
					self.listaFicheros.extend( rec_glob(archivo, "*.rar") )
					print "OK!"

					print "Buscando en "+os.path.dirname(archivo)+" Imagenes ISO ... ",
					self.listaFicheros.extend( rec_glob(archivo, "*.iso") )
					print "OK!"


				elif	(
						os.path.isfile(parametro) and
						(
							self.getExtension(parametro) == "iso" or
							self.getExtension(parametro) == "rar"
						)
					):
					self.listaFicheros.append( parametro )

				# si tiene caracteres raros -> no es expresión regular
				# porque de otro forma, peta la expresion regular.
				elif( not self.tieneCaracteresRaros(parametro) ):
					self.listaFicheros.extend( glob.glob(parametro) )
				else:
					self.listaFicheros.append( parametro )

			if (len(self.listaFicheros) == 0):
				print "No se ha encontrado ninguna imagen ISO"

		if not self.GUI:
			self.procesar( )

	def hayGUI(self):
		numParametros = len( self.PARAMETROS )
		return self.GUI and (numParametros == 0)

	def uso(self):
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

	def getParametros(self):
		return self.PARAMETROS

	def getListaFicheros(self):
		return self.listaFicheros

	def getFabricante(self):
		return self.FABRICANTE

	def hayPausa(self):
		return self.PAUSA

	def anadirListaFicheros(self , lista):
		self.listaFicheros.extend( lista )

	def setInterfaz(self , interfaz):
		self.interfaz = interfaz

	def procesar(self , progreso1 = None):
		correctos = []
		erroneos = []
		numFicheros = len(self.listaFicheros)
		if(numFicheros>0):

			#Expandir directorios
			# ...

			#Ordenamos la lista
			self.listaFicheros.sort()
			numFicherosProcesados=0
			for fichero in self.listaFicheros:
				numFicherosProcesados = numFicherosProcesados + 1
				print "===================== "+os.path.basename(fichero)+" ("+str(numFicherosProcesados)+"/"+str(numFicheros)+") ===================="
				print "{"
				if( self.comprobarExistencia(self.DEVICE) and self.comprobarExistencia(fichero) ):
					if( self.getExtension(fichero) == "rar" ):
						print "Añadir RAR con ISO dentro : " + os.path.basename(fichero) + " a la particion " + DEVICE + " " + FABRICANTE
						nombreRAR = fichero
						nombreISO = self.getNombreISOenRAR(nombreRAR)
						if (nombreISO != ""):
							if( not self.comprobarExistencia(nombreISO) ):
								# Paso 1 : Descomprimir
								if ( self.descomprimirRARconISODentro(nombreRAR , nombreISO) ):
									print "Descomprimido correctamente"
									# Paso 2 : Añadir la ISO
									if ( self.anadirISO(DEVICE , nombreISO , progreso1) ):
											mensaje = "ISO "+nombreISO+" descomprimida y añadida correctamente"
											print "OK"
											correctos.append(mensaje)
									else:
										mensaje = "ERROR añadiendo la ISO : " + nombreISO + " (comprueba que sea una ISO de WII)"
										print "ERROR"
										erroneos.append(mensaje)

									if borrarISODescomprimida:
										# Paso 3 : Borrar la iso descomprimida
										try:
											print "Se va ha borrar la ISO descomprimida"
											os.remove(nombreISO)
											print "La ISO "+nombreISO+" temporal fue borrada"
										except:
											print "ERROR al borrar la ISO : " + nombreISO
										print "}"
										print
									else:
										print "No se ha borrado la ISO temporal"
								else:
									mensaje = "ERROR al descomrpimir el RAR : " + nombreRAR
									print "ERROR"
									print "}"
									print
									erroneos.append(mensaje)
							else:
								mensaje = "ERROR no se puede descomrpimir por que reemplazaría el ISO : " + nombreISO
								print "ERROR"
								print "}"
								print
								erroneos.append(mensaje)
						else:
							mensaje = "ERROR el RAR " + nombreRAR + " no tenía ninguna ISO"
							print "ERROR"
							print "}"
							print
							erroneos.append(mensaje)
					elif( self.getExtension(fichero) == "iso" ):
						print "Añadir ISO : " + os.path.basename(fichero) + " a la particion " + self.DEVICE + " " + self.FABRICANTE
						if ( self.anadirISO(self.DEVICE , fichero , progreso1) ):
							mensaje = "ISO "+fichero+" añadida correctamente"
							print "OK"
							print "}"
							print
							correctos.append(mensaje)
						else:
							mensaje = "ERROR añadiendo la ISO : " + fichero + " (comprueba que sea una ISO de WII)"
							print "ERROR"
							print "}"
							print
							erroneos.append(mensaje)
					else:
						mensaje = "ERROR "+fichero+" no es un ningún juego de Wii"
						print "ERROR"
						print "}"
						print
						erroneos.append(mensaje)
				else:
					mensaje = "ERROR la ISO o la partición no existe"
					print "ERROR"
					print "}"
					print
					erroneos.append(mensaje)

			print "================= INFORME DE RESULTADOS ========================="
			print "{"

			if(len(correctos) == numFicherosProcesados):
				print "\t{"
				print "\t================= Todo metido en el HD correctamente ==================="
				print "\t}"
				self.interfaz.alert("info","Todo metido en el HD correctamente")
			else:
				if(len(correctos) > 0):
					print "\t================ Juegos correctos ("+str(len(correctos))+"/"+str(numFicherosProcesados)+") =============="
					print "\t{"
					for mensaje in correctos:
						print "\t"+mensaje
					print "\t}"
					self.interfaz.alert("info","Juegos correctos ("+str(len(correctos))+"/"+str(numFicherosProcesados)+")")

			if(len(erroneos) > 0):
				print "\t=================== Juegos erroneos ("+str(len(erroneos))+"/"+str(numFicherosProcesados)+") ================="
				print "\t{"
				for mensaje in erroneos:
					print "\t"+mensaje
				print "\t}"
				self.interfaz.alert("info","Juegos erroneos ("+str(len(erroneos))+"/"+str(numFicherosProcesados)+")")

			print "}"

		if (not self.GUI and self.hayPausa()):
			raw_input("Pulse cualquier tecla para continuar ...\n")

		# vaciamos la listaFicheros a procesar
		while len(self.listaFicheros) > 0:
			self.listaFicheros.remove( self.listaFicheros[0] )

