#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os.path
import config
import time
import gobject

#import threading , subprocess
from threading import Thread

class Animador(Thread):

    # pool2 es opcional
    def __init__(self , estadoBatch , pool , pool2 = None):
        Thread.__init__(self)
        self.estadoBatch = estadoBatch
        self.pool = pool
        self.pool2 = pool2
        self.interrumpido = False

    def run(self):
        i = 0
        while not self.interrumpido:
            try:
                if (self.pool.numTrabajos > 0) or ( self.pool2 != None and self.pool2.numTrabajos > 0 ):
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