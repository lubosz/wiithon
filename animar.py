#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os.path
import time
from threading import Thread

import gobject

import config

class Animador(Thread):

    # pool2 es opcional
    def __init__(self , estadoBatch , poolTrabajo , poolBash):
        Thread.__init__(self)
        self.estadoBatch = estadoBatch
        self.poolTrabajo = poolTrabajo
        self.poolBash = poolBash
        self.ocupado = False
        self.interrumpido = False

        destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")
        gobject.idle_add( self.modificarIcono , destinoIcono )

    def run(self):
        i = 0
        while not self.interrumpido:
            try:
                if self.poolTrabajo.estaOcupado() or self.poolBash.estaOcupado():
                    destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "busy-icon%d.png" % (i))
                    i += 1
                    if i > 14:
                        i = 0
                else:
                    destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")

                gobject.idle_add( self.modificarIcono , destinoIcono )
                time.sleep(0.05)
            except:
                pass

    def modificarIcono(self , icono):
        self.estadoBatch.set_from_file( icono )

    def interrumpir(self):
        self.interrumpido = True

