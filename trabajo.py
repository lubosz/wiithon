#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import config 
import util
from pool import Pool
from pool import HiloPool
import threading , subprocess
from threading import Thread
from mensaje import Mensaje
				
class PoolTrabajo(Pool):
	def __init__(self , numHilos):
		Pool.__init__(self , numHilos)

	def ejecutar(self , idWorker , trabajo , core , pool , DEVICE , FABRICANTE):
	
		if (trabajo.getQueHacer() == "ANADIR"):
			fichero = trabajo.getAQuien()
	
			try:
				os.remove ( config.HOME_WIITHON_LOGS_PROCESO )
			except OSError:
				pass

			core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )

			if( not os.path.exists(DEVICE) or not os.path.exists(fichero) ):
				error = True
				core.nuevoMensaje( Mensaje("ERROR",_("La ISO o la partición no existe")) )
			elif( util.getExtension(fichero) == "rar" ):
				error = True
				core.nuevoMensaje( Mensaje("INFO",_("Buscando ISO dentro del RAR")) )
				nombreRAR = fichero
				nombreISO = core.getNombreISOenRAR(nombreRAR)
				if (nombreISO != ""):
					if( not os.path.exists(nombreISO) ):
						# Paso 1 : Descomprimir
						if ( core.descomprimirRARconISODentro(nombreRAR) ):
							core.nuevoMensaje( Mensaje("INFO",_("ISO Descomprimida")))
							pool.nuevoElemento( nombreISO )
						else:
							core.nuevoMensaje( Mensaje("ERROR",_("Al descomrpimir el RAR : %s") % (nombreRAR)) )
					else:
						core.nuevoMensaje( Mensaje("ERROR",_("No se puede descomrpimir por que reemplazaría el ISO : %s") % (nombreISO)) )
				else:
					core.nuevoMensaje( Mensaje("ERROR",_("El RAR %s no tenía ninguna ISO") % (nombreRAR)) )
			elif( os.path.isdir( fichero ) ):
				error = True
			
				core.nuevoMensaje( Mensaje("INFO",_("Buscando en %s ficheros RAR ... ") % (os.path.dirname(fichero))))
				encontrados =  core.rec_glob(fichero, "*.rar")
				if (len(encontrados) == 0):
					core.nuevoMensaje( Mensaje("INFO",_("No se ha encontrado ningún RAR con ISOS dentro")))
				else:
					for encontrado in encontrados:
						pool.nuevoElemento( encontrado )

				core.nuevoMensaje( Mensaje("INFO",_("Buscando en %s Imagenes ISO ... ") % (os.path.dirname(fichero))))
				encontrados =  core.rec_glob(fichero, "*.iso")
				if (len(encontrados) == 0):
					core.nuevoMensaje( Mensaje(_("INFO",_("No se ha encontrado ningún ISO"))))
				else:
					for encontrado in encontrados:
						pool.nuevoElemento( encontrado )

			elif( util.getExtension(fichero) == "iso" ):
				core.nuevoMensaje( Mensaje("INFO",_("Añadir ISO : %s a la particion %s %s") % (os.path.basename(fichero),DEVICE, FABRICANTE) ) )
				core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA") )
				if ( core.anadirISO(DEVICE , fichero ) ):
					core.nuevoMensaje( Mensaje("INFO",_("ISO %s añadida correctamente") % (fichero)) )
					error = False
				else:
					core.nuevoMensaje( Mensaje("ERROR",_("Añadiendo la ISO : %s (comprueba que sea una ISO de WII)") % (fichero)) )
					error = True
				core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN") )
			else:
				error = True
				core.nuevoMensaje( Mensaje("ERROR",_("%s no es un ningún juego de Wii") % (os.path.basename(fichero)) ) )

			if error:
				core.nuevoMensaje( Mensaje("COMANDO","TERMINA_ERROR") )
			else:
				core.nuevoMensaje( Mensaje("COMANDO","TERMINA_OK") )
			
			# Esperar que todos los mensajes sean atendidos
			core.getMensajes().join()
		elif( trabajo.getQueHacer() == "EXTRAER" ):
			IDGAME = trabajo.getAQuien()
			try:
				os.remove ( config.HOME_WIITHON_LOGS_PROCESO )
			except OSError:
				pass
		
			core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )
			core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA") )
			exito = core.extraerJuego(DEVICE , IDGAME )
			core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN") )
			if exito:
				core.nuevoMensaje( Mensaje("COMANDO","TERMINA_OK") )
			else:
				core.nuevoMensaje( Mensaje("COMANDO","TERMINA_ERROR") )

class HiloPoolTrabajo(Thread):
	def __init__(self , core ):
		Thread.__init__(self)
		self.core = core
		self.DEVICE = core.getDeviceSeleccionado()
		self.FABRICANTE = core.getFabricanteSeleccionado()
		self.listaFicheros = None
		self.pool = PoolTrabajo(1)

	def run(self):
		if (self.pool != None):
			self.pool.empezar(args=(self.core, self.pool , self.DEVICE,self.FABRICANTE))
		
	def interrumpir(self):
		if (self.pool != None):
			self.pool.interrumpir()
		
	def anadir(self , listaFicheros):
		# 1 Hilo se encarga de añadir todo
		for fichero in listaFicheros:
			self.pool.nuevoElemento( Trabajo("ANADIR" , fichero) )
			
	def extraer(self , IDGAME):
		self.pool.nuevoElemento( Trabajo("EXTRAER" , IDGAME) )


class Trabajo:
	def __init__(self, queHacer , aQuien):
		self.queHacer = queHacer
		self.aQuien = aQuien
		
	def getQueHacer(self):
		return self.queHacer
		
	def getAQuien(self):
		return self.aQuien

