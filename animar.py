#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os.path
import time
from threading import Thread

import gobject

import config

class Animador(Thread):

    # pool2 es opcional
    def __init__(self , estadoBatch , poolTrabajo , poolBash, mostrarHBoxProgreso, ocultarHBoxProgreso):
        Thread.__init__(self)
        self.estadoBatch = estadoBatch
        self.poolTrabajo = poolTrabajo
        self.poolBash = poolBash
        self.ocupado = False
        self.interrumpido = False
        self.mostrarHBoxProgreso = mostrarHBoxProgreso
        self.ocultarHBoxProgreso = ocultarHBoxProgreso
        self.ocultado = False
        
    def run(self):
        i = 0
        while not self.interrumpido:
            try:
                #print "self.poolBash.numTrabajos = %d" % self.poolBash.numTrabajos
                #print "self.poolTrabajo.numTrabajos = %d" % self.poolTrabajo.numTrabajos
                if self.poolTrabajo.estaOcupado() or self.poolBash.estaOcupado():
                    destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "busy-icon%d.png" % (i))
                    gobject.idle_add( self.mostrarHBoxProgreso )
                    self.ocultado = False
                    i += 1
                    if i > 14:
                        i = 0
                else:
                    destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")
                    if not self.ocultado:
                        #gobject.timeout_add( 5000, self.ocultarHBoxProgreso )
                        gobject.idle_add( self.ocultarHBoxProgreso )
                        self.ocultado = True

                gobject.idle_add( self.modificarIcono , destinoIcono )
                time.sleep(0.1)
            except:
                pass

    def modificarIcono(self , icono):
        self.estadoBatch.set_from_file( icono )

    def interrumpir(self):
        self.interrumpido = True

