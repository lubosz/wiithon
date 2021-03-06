#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

#import sys
#import libxml2

#from wiitdb_xml import *
#from core import WiithonCORE

if False:
    xml_plantilla = """<?xml version="1.0" encoding="UTF-8"?>
    <margenes>
        <letra_azul>
            <grande>
                <subrayado>
                    $titulo
                </subrayado>
            </grande>
        </letra_azul>
        <letra_roja>
            $message
        </letra_roja>
    </margenes>
    """

    def recorrer_nodo(nodo, level):
        while nodo is not None:
            if nodo.type == 'element':
                print "activar %s" % nodo.name
                if nodo.children.next == None:
                    print "escribir %s" % nodo.content.strip()
                recorrer_nodo(nodo.children, level + 1)
                print "desactivar %s" % nodo.name
            nodo = nodo.next

    doc = libxml2.parseDoc(xml_plantilla)
    recorrer_nodo(doc.children, 1)
    doc.freeDoc()


##############################################
if False:
    import gtk

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect("destroy", gtk.mainquit)
    window.set_border_width(0)

    # Set up the text widgets
    table = gtk.TextTagTable()
    buffer = gtk.TextBuffer(table)
    view = gtk.TextView(buffer)

    # Create a green-color tag
    green = buffer.create_tag("green")
    green.set_property("foreground", "green")

    # Apply the green tag to inserted text
    def bufferInsert(widget, event, *args):
        end = widget.get_iter_at_mark(widget.get_insert())
        start = end.copy()
        start.backward_chars(args[1])
        widget.apply_tag(green, start, end)
        view.queue_draw()
        gtk.mainiteration()
        
    buffer.connect_after("insert-text", bufferInsert)

    # Create scrollbars around the TextView.
    scroll_window = gtk.ScrolledWindow()
    scroll_window.add(view)

    # Finish up.
    window.add(scroll_window)
    window.resize(400, 300)
    scroll_window.show()
    view.show()
    window.show()
    gtk.main()


if False:
    core = WiithonCORE()

    print "Empieza a descomprimir"
    exito = core.unpack("/media/datos/wiithon_pruebas/descomprimir/play.rar","/media/datos/wiithon_pruebas/descomprimir/")
    if exito:
        print "Descomprimido OK"
    else:
        print "Error al descomprimir"
    sys.exit(0)

if False:
    from wiitdb_schema import *

    db =        util.getBDD()
    session =   util.getSesionBDD(db)

    i = 0
    #for juego in session.query(Juego).outerjoin(JuegoWIITDB):
    for juego in session.query(Juego):
    #for juego in session.query(JuegoWIITDB).join(Juego):
        print juego.juego_wiitdb
        print "."
        i += 1

    sys.exit(0)

#####################################################


'''
import os
import time
import subprocess
import threading
from threading import Thread

from pool import Pool

import config
from juego import session, Juego

print "cargando "+os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' )

print "Juegos antes de insertar"
for j in session.query(Juego):
    print j

print "Se insertan juegos"
for i in range(10):
    j = Juego("GHX67"+str(i) , "Resident Evil 4" , 2008 , 1 , 5)
    existe = session.query(Juego).filter( "idgame==:idgame" ).params(idgame=j.idgame).count() > 0
    if existe:
        j.borrarCaratula()
        j.harakiri()
        print "Juego borrado"
    j.crearCaratula()
    session.save(j)
    print "Juego insertado"
session.commit()
print "Commit definitivo"

print "Juegos DESPUES de insertar"
for j in session.query(Juego):
    print j

'''
'''
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
        self.pool = PoolCustomizada(15)
        for i in range(30):
            self.pool.nuevoElemento("elemento %d" % i)
        self.pool.empezar(args=("hola","adios"))

hilo = HiloPool()
hilo.start()

i=0
while hilo.isAlive():
    print "Aún no ha terminado %d" % i
    time.sleep(2)
    i = i + 1
editar_juego
print "YA ha terminado!"
'''
'''
p = subprocess.Popen("sudo /usr/local/share/wiithon/wbfs -p /dev/sdb1 add /home/makiolo/descargas/Resident\ Evil\ 4\ Wii\ Edition.iso" , shell=True , stdout=subprocess.PIPE)
out = p.stdout.readlines()
for linea in out:
    print "---------------"
    print linea.strip()
'''

