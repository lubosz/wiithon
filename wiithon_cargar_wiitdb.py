#!/usr/bin/python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys

from wiitdb_xml import *
from util import ErrorDescargando

juegos = 0
descripciones = 0
generos = 0
online_features = 0
accesorios = 0
companies = 0

def spinner(cont, total):
    print "%d" % (cont * 100 / total)

def callback_nuevo_juego(juego):
    global juegos
    juegos += 1
    '''
    print "j ",
    sys.stdout.flush()
    '''

def callback_nuevo_descripcion(descripcion):
    global descripciones
    descripciones += 1
    '''
    print "d ",
    sys.stdout.flush()
    '''

def callback_nuevo_genero(genero):
    global generos
    generos += 1
    '''
    print "g ",
    sys.stdout.flush()
    '''

def callback_nuevo_online_feature(online_feature):
    global online_features
    online_features += 1
    '''
    print "o ",
    sys.stdout.flush()
    '''

def callback_nuevo_accesorio(accesorio, obligatorio):
    global accesorios
    accesorios += 1
    '''
    print "a ",
    sys.stdout.flush()
    '''

def callback_nuevo_companie(companie):
    global companies
    companies += 1
    '''
    print "c ",
    sys.stdout.flush()
    '''

def callback_error_importando(xml, motivo):
    print "Error grave, se ha detenido la importación: %s" % motivo
    
def callback_empieza_descarga(url):
    print "Empieza a descargar desde %s" % url
    
def callback_empieza_descomprimir(zip):
    print "Empieza a descomprimir el zip: %s" % zip

try:
    xml = WiiTDBXML('http://wiitdb.com/wiitdb.zip','wiitdb.zip','wiitdb.xml', spinner, callback_nuevo_juego, callback_nuevo_descripcion,
                                                callback_nuevo_genero, callback_nuevo_online_feature,
                                                callback_nuevo_accesorio,callback_nuevo_companie,
                                                callback_error_importando,
                                                callback_empieza_descarga,
                                                callback_empieza_descomprimir)
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
    
except ErrorDescargando:
    print "Error al descargar"
