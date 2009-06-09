#!/usr/bin/python
# -*- coding: utf-8 -*-
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
        self.interrumpido = False
        self.numTrabajos = 0

    def intentarEmpezarTrabajo(self , cola , idWorker , *args):
        while not self.interrumpido:
            if (self.numTrabajos > 0):
                elemento = cola.get()
                self.ejecutar(idWorker , elemento , *args)
                cola.task_done()
                self.numTrabajos -= 1
            else:
                # comprueba si hay tareas cada cierto tiempo
                time.sleep(0.5)

    def nuevoElemento(self, elemento):
        self.cola.put(elemento)
        self.numTrabajos += 1

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

