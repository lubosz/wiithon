#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys

from wiitdb_xml import *
from core import WiithonCORE

if False:
    core = WiithonCORE()

    print "Empieza a descomprimir"
    exito = core.unpack("/media/datos/wiithon_pruebas/descomprimir/play.rar","/media/datos/wiithon_pruebas/descomprimir/")
    if exito:
        print "Descomprimido OK"
    else:
        print "Error al descomprimir"
    sys.exit(0)

if True:
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

print "YA ha terminado!"
'''
'''
p = subprocess.Popen("sudo /usr/local/share/wiithon/wbfs -p /dev/sdb1 add /home/makiolo/descargas/Resident\ Evil\ 4\ Wii\ Edition.iso" , shell=True , stdout=subprocess.PIPE)
out = p.stdout.readlines()
for linea in out:
    print "---------------"
    print linea.strip()
'''
