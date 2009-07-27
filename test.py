#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys

from wiitdb_xml import *

juegos = 0
descripciones = 0
generos = 0
online_features = 0
accesorios = 0
companies = 0

def spinner(cont, total):
    print "< %d%% >" % (cont * 100 / total)

def callback_nuevo_juego(juego):
    global juegos
    juegos += 1
    
def callback_nuevo_descripcion(descripcion):
    global descripciones
    descripciones += 1
    
def callback_nuevo_genero(genero):
    global generos
    generos += 1
    
def callback_nuevo_online_feature(online_feature):
    global online_features
    online_features += 1
    
def callback_nuevo_accesorio(accesorio, obligatorio):
    global accesorios
    accesorios += 1
    
def callback_nuevo_companie(companie):
    global companies
    companies += 1

def callback_error_importando(xml, motivo):
    print "Error grave, se ha detenido la importación: %s" % motivo
    xml.interrumpir()

xml = WiiTDBXML('recursos/wiitdb/wiitdb.xml', spinner, callback_nuevo_juego, callback_nuevo_descripcion,
                                            callback_nuevo_genero, callback_nuevo_online_feature,
                                            callback_nuevo_accesorio,callback_nuevo_companie,
                                            callback_error_importando)
xml.start()
xml.join()

print "Datos añadidos"
print "-------------------------------------"
print "Juegos: %d" % juegos
print "Synopsis: %d" % descripciones
print "Generos: %d" % generos
print "Online features: %d" % online_features
print "Accesorios: %d" % accesorios
print "Compañias: %d" % companies

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

