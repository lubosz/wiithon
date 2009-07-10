#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import libxml2
from companies import Companie, session

'''
game
id
region
locale
title
synopsis
developer
publisher
date
genre
rating
wi-fi
input
control
rom
'''

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''
'''
def printNode(node, depth=0):
    if node.type == "element":
        #print ' '*depth+str(node.name)+str(node.properties)
        if node.name == "company":
            print node

    child = node.children
    while child is not None:
        printNode(child, depth+1)
        child = child.next
'''

fichXML = 'recursos/wiitdb/wiitdb.xml'
xmldoc = libxml2.parseFile(fichXML)

for nodo in xmldoc.xpathEval('//companies/company'):
    code = ""
    name = ""
    i = 0
    attr = nodo.get_properties()
    while attr != None:
        if attr.name == "code":
            code = attr.content
        elif attr.name == "name":
            name = attr.content
        attr = attr.next    
    # insertar en la bdd
    comp = Companie(code, name)
    session.merge(comp)

for nodo in xmldoc.xpathEval('//game/*'):
    id = ""
    region = ""
    locale = ""
    title = ""
    synopsis = ""
    developer = ""
    publisher = ""
    date = ""
    genre = ""
    rating = ""
    wifi = ""
    input = ""
    control = ""
    rom = ""
    if nodo.name == "id":
        id = nodo.content
    elif nodo.name == "region":
        region = nodo.content
        
    print "%s - %s" % (id, region)


# hacemos efectivas las transacciones
session.commit()

# libera el xml
xmldoc.freeDoc()



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

