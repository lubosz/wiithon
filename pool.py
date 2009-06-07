#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import time , sys
import subprocess
import threading
from threading import Thread
from Queue import Queue

class Pool:
	def __init__(self , numHilos):
		self.cola = Queue()
		self.numHilos = numHilos
		self.lock = False
		self.esperandoTrabajo = True
		self.interrumpido = False

	def intentarEmpezarTrabajo(self , cola , idWorker , *args):
		while not self.interrumpido:
			try:
				if (cola.qsize() > 0):
					elemento = cola.get()
					self.ejecutar(idWorker , elemento , *args)
					cola.task_done()
				else:
					# comprueba si hay tareas cada cierto tiempo
					time.sleep(0.5)
			except:
				# posiblemente la cola esta siendo escrito o leida
				# FIXME: mutex ...
				time.sleep(0.5)
				

	def nuevoElemento(self, elemento):
		if not self.esperandoTrabajo:
			self.esperandoTrabajo = False
		self.cola.put(elemento)

	def empezar(self , args=None):
		if not self.lock:
			self.lock = True

			for idWorker in range(self.numHilos):

				lista_args = []
				lista_args.append( self.cola )
				lista_args.append( idWorker )
				if args != None:
					for arg in args:
						lista_args.append( arg )

				worker = Thread(target=self.intentarEmpezarTrabajo, args=lista_args )
				worker.setDaemon(True)
				worker.start()

			# aqui se bloquea hasta que termine
			self.cola.join()

			self.lock = False

	def esLock(self):
		return self.lock

	# metodo para sobreescribir
	def ejecutar(self , idWorker , elemento , *arg):
		print "Debes sobreescribir el método"
		raise NotImplementedError
		
	def interrumpir(self):
		self.interrumpido = True

