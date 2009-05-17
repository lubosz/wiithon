#-*-coding: utf-8-*-

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
		while True:
			print "Trabajos = " + str(cola.qsize())
			sys.stdout.flush()
			elemento = cola.get()
			self.ejecutar(idWorker , elemento , *args)
			cola.task_done()

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
			print "fin pool"

	def esLock(self):
		return self.lock

	# metodo para sobreescribir
	def ejecutar(self , idWorker , elemento , *arg):
		#print "Elemento = %s por Hilo = %d" % (elemento,idWorker+1)
		print "Debes sobreescribir el método"
		raise NotImplementedError
		
	def interrumpir(self):
		self.interrumpido = True

class PoolCustomizada(Pool):
	def __init__(self , numHilos):
		Pool.__init__(self , numHilos)

	def ejecutar(self , idWorker , elemento , dato1 , dato2):
		print "Trabajo realizado sobre Elemento = %s por Hilo = %d" % (elemento,idWorker+1)
		print "dato1 = %s" % dato1
		print "dato2 = %s" % dato2
		time.sleep(1)

class HiloPool(threading.Thread):
	def run(self):
		self.pool = PoolCustomizada(2)
		for i in range(30):
			self.pool.nuevoElemento("elemento %d" % i)
		self.pool.empezar(args=("hola","adios"))


