#!/usr/bin/python

import os
import gtk
import signal
import time

# !! for avois config depend, avoid connect in db
#import config
WIITHON_FILES = os.path.dirname(__file__)
WIITHON_FILES_RECURSOS = os.path.join(WIITHON_FILES , "recursos")
WIITHON_FILES_RECURSOS_IMAGENES = os.path.join(WIITHON_FILES_RECURSOS , "imagenes")
WIITHON_FILES_RECURSOS_IMAGENES_LOADING = os.path.join(WIITHON_FILES_RECURSOS_IMAGENES, "loading.gif")

class Loading(gtk.Window):
    
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        
        # global
        self.MAX_SEGS_LOADING = 20
        
        # crear VBox
        vbox = gtk.VBox(False, 5)
        self.add(vbox)
        vbox.show()
        
        image = gtk.Image()
        image.set_from_file(WIITHON_FILES_RECURSOS_IMAGENES_LOADING)
        image.show()
        
        # empaquetamos todo
        vbox.pack_start(image, False, True, 0)
        
        # mostrar ventana en el centro
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.show()
        
    def close(self):
        self.salir = True
        return False
        
    def run(self):        
        self.salir = False
        time_inicio = time.time()
        while not self.salir and ((time.time()-time_inicio) < self.MAX_SEGS_LOADING):
            gtk.main_iteration_do(False)
            
        self.destroy()
    
loading = Loading()
        
def salir(*arg):
    loading.close()

def App():
    
    signal.signal(signal.SIGINT, salir)
    loading.run()

if __name__ == '__main__':
    App()

