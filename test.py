#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import libxml2
from wiitdb_companies import Companie, session
from wiitdb_juego import JuegoWIITDB
from juego import Juego

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''

for juego in session.query(Juego).join('wiitdb_juegos').filter('wiitdb_juegos.wifi_players > 4'):
    print juego

def leerAtributo(nodo, atributo):
    valor = ""
    attr = nodo.get_properties()
    while attr != None:
        if attr.name == atributo:
            valor = attr.content
        attr = attr.next    
    return valor

fichXML = 'recursos/wiitdb/wiitdb.xml'
xmldoc = libxml2.parseFile(fichXML)
ctxt = xmldoc.xpathNewContext()
nodo = ctxt.xpathEval("//*[name() = 'datafile']")[0]
while nodo != None:

    if nodo.type == "element":

        if nodo.name == "datafile":
            nodo = nodo.children

        elif nodo.name == "WiiTDB":
            version = leerAtributo(nodo, 'version')
            print "Version: %s" % version

        elif nodo.name == "game":
            while (nodo.next != None):
                if nodo.type == "element":
                    if nodo.name == "game":
                        idgame = ""
                        name = ""
                        region = ""
                        title_EN = ""
                        synopsis_EN = ""
                        title_ES = ""
                        synopsis_ES = ""
                        title_PT = ""
                        synopsis_PT = ""
                        developer = ""
                        publisher = ""
                        anio = 0
                        mes = 0
                        dia = 0
                        wifi_players = 0
                        input_players = 0

                        name = leerAtributo(nodo, 'name')
                        
                        #adentrarse en game
                        nodo = nodo.children
                        
                        while nodo.next is not None:
                            if nodo.type == "element":
                                if nodo.name == "id":
                                    idgame = nodo.content
                                elif nodo.name == "developer":
                                    developer = nodo.content
                                elif nodo.name == "publisher":
                                    publisher = nodo.content
                                elif nodo.name == "region":
                                    region = nodo.content
                                elif nodo.name == "wi-fi":
                                    wifi_players = leerAtributo(nodo, 'players')
                                elif nodo.name == "input":
                                    input_players = leerAtributo(nodo, 'players')
                                elif nodo.name == "locale":
                                    # leer atributos de locale
                                    lang = leerAtributo(nodo, 'lang')
                                    
                                    #adentrarse en locale
                                    nodo = nodo.children
                                    # FIXME: EN, JA, FR, DE, ES, IT, NL, PT, SV, NN, DA, FI, ZH, KO
                                    i = 0
                                    while nodo.next is not None:
                                        if nodo.type == "element":
                                            if nodo.name == "title":
                                                if lang == "EN":
                                                    title_EN = nodo.content
                                                elif lang == "ES":
                                                    title_ES = nodo.content
                                                elif lang == "PT":
                                                    title_PT = nodo.content
                                            elif nodo.name == "synopsis":
                                                if lang == "EN":
                                                    synopsis_EN = nodo.content
                                                elif lang == "ES":
                                                    synopsis_ES = nodo.content
                                                elif lang == "PT":
                                                    synopsis_PT = nodo.content
                                        nodo = nodo.next
                                        i += 1
                                    #volver a locale
                                    nodo = nodo.parent
                                    
                            # siguiente hijo de game
                            nodo = nodo.next
                            
                        #volver a game
                        nodo = nodo.parent

                        juego = JuegoWIITDB(idgame , name , region,     title_EN, synopsis_EN,
                                                                        title_ES, synopsis_ES,
                                                                        title_PT, synopsis_PT,
                                            developer, publisher, anio, mes, dia, wifi_players, input_players)
                        session.merge(juego)

                        #print juego

                nodo = nodo.next

        elif nodo.name == "companies":

            nodo = nodo.children

            while nodo.next is not None:
                if nodo.type == "element":
                    if nodo.name == "company":
                        code = ""
                        name = ""

                        attr = nodo.get_properties()
                        while attr != None:
                            if attr.name == "code":
                                code = attr.content
                            elif attr.name == "name":
                                name = attr.content
                            attr = attr.next    
                        comp = Companie(code, name)
                        session.merge(comp)

                        #print comp

                nodo = nodo.next

            nodo = nodo.parent

    nodo = nodo.next

# libera el xml
xmldoc.freeDoc()
ctxt.xpathFreeContext()

# hacemos efectivas las transacciones
session.commit()

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

