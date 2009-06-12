#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys
import os
import time
import commands
from Queue import Queue
from threading import Thread
import subprocess

import gtk
import gettext
import shutil

import util
from util import NonRepeatList
import config

class WiithonCORE:

    #globales publicas

    # Lista BIdimensional de particiones
    # indice 0 -> device  (/dev/sda1)
    # indice 1 -> Fabricante  (Maxtor)
    listaParticiones = None

    # indice (fila) de la partición seleccionado
    particionSeleccionada = 0

    # Estructura sincrona para comunicacion entre hilos
    mensajes = None

    # Destino por defecto para el destino de las caratulas
    destinoCopiarCaratula = config.HOME

    # Destino por defecto para el destino de los discos
    destinoCopiarDisco = config.HOME

    # Destino por defecto para extraer un ISO
    destinoExtraer = config.HOME

    #constructor
    def __init__(self):
        # cola sincronizada (productor-consumidor)
        self.mensajes = Queue()

    def getMensajes(self):
        return self.mensajes

    def nuevoMensaje(self , mensaje):
        self.mensajes.put(mensaje)

    # Obtiene un list de juegos en una tabla de 3 columnas:
    # index 0 -> IDGAME o identificador único del juego
    # index 1 -> Nombre del juego
    # index 2 -> Tamaño en GB redondeado a 2 cifras
    def getListaJuegos(self , DEVICE):
        def ordenarPorNombre(juego1 , juego2):
            return cmp( juego1[1].lower() , juego2[1].lower() )

        lineas = util.getSTDOUT_iterador( config.WBFS_APP+" -p "+DEVICE+" ls" )

        salida = []
        for linea in lineas:
            cachos = linea.strip().split(";")
            if(len(cachos)==3):
                salida.append( [ cachos[0] , cachos[1] , cachos[2] ] )
        salida.sort(ordenarPorNombre)
        return salida

    # añade un *ISO* a un *DEVICE*
    def anadirISO(self , DEVICE , ISO , ficheroSalida=None):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarISO(self , DEVICE , IDGAME , NUEVO_NOMBRE):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # getEspacioLibre obtiene una tupla [uso , libre , total]
    def getEspacioLibre(self , DEVICE):
        salida = util.getSTDOUT( config.WBFS_APP+" -p "+DEVICE+" df" )
        cachos = salida.split(";")
        if(len(cachos) == 3):
            try:
                return [ float(cachos[0]) , float(cachos[1]) , float(cachos[2]) ]
            except:
                pass
        # en caso de algun error, devuelve una tupla de 3 de float a 0
        return [ 0.0 , 0.0 , 0.0 ]

    # borra el juego IDGAME
    def borrarJuego(self , DEVICE , IDGAME):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rm "+IDGAME
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False
        except TypeError:
            return False

    # extrae el juego IDGAME
    def extraerJuego(self , DEVICE , IDGAME):
        try:
            trabajoActual = os.getcwd()
            # cambiamos de directorio de trabajo
            os.chdir( self.destinoExtraer )
            comando = config.WBFS_APP+" -p "+DEVICE+" extract "+IDGAME
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            # volvemos al directorio original
            os.chdir( trabajoActual )
            return salida == 0
        except KeyboardInterrupt:
            return False

    def existeDisco(self , IDGAME):
        return (os.path.exists( self.getRutaDisco(IDGAME) ))

    def descargarDisco(self , IDGAME):
        if (self.existeDisco(IDGAME)):
            return True
        else:
            print _("***************** DESCARGAR DISCO %s ********************" % (IDGAME))
            origen = 'http://www.theotherzone.com/wii/diskart/160/160/' + IDGAME + '.png'
            salida = os.system("wget --no-cache --directory-prefix=\""+config.HOME_WIITHON_DISCOS+"\" " + origen)
            descargada = (salida == 0)
            if descargada:
                destino = os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")
                os.system("mogrify -resize 160x160! " + destino)
            return descargada

    def getRutaDisco(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")

    def getRutaCaratula(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")

    def getDestinoExtraer(self):
        return self.destinoExtraer

    def setDestinoExtraer(self, destino):
        if type(destino) == list:
            destino = destino[0]
        self.destinoExtraer = destino

    def getDestinoCopiarDisco(self):
        return self.destinoCopiarDisco

    def setDestinoCopiarDisco(self, destino):
        if type(destino) == list:
            destino = destino[0]
        self.destinoCopiarDisco = destino

    def getDestinoCopiarCaratula(self):
        return self.destinoCopiarCaratula

    def setDestinoCopiarCaratula(self, destino):
        if type(destino) == list:
            destino = destino[0]
        self.destinoCopiarCaratula = destino

    def copiarCaratula(self , IDGAME ):
        destino = self.getDestinoCopiarCaratula()
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (IDGAME) )
        if( not os.path.exists( destino ) and self.existeDisco(IDGAME) ):
            origen = self.getRutaCaratula(IDGAME)
            print "Copiando %s ----> %s ... " % (origen , destino)
            shutil.copy(origen, destino)
            return os.path.exists(destino)
        else:
            print "Ya tienes la caratula %s" % (IDGAME)
            return True

    def copiarDisco(self , IDGAME ):
        destino = self.getDestinoCopiarDisco()
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (IDGAME) )
        if( not os.path.exists( destino ) and self.existeCaratula(IDGAME) ):
            origen = self.getRutaDisco(IDGAME)
            print "Copiando %s ----> %s ... " % (origen , destino),
            shutil.copy(origen, destino)
            print "OK"
            return os.path.exists(destino)
        else:
            print "Ya tienes el disco %s" % (IDGAME)
            return True

    # Nos dice si existe la caratula del juego "IDGAME"
    def existeCaratula(self , IDGAME):
        return (os.path.exists( self.getRutaCaratula(IDGAME) ))

    # Descarga una caratula de "IDGAME"
    # el Tipo puede ser : normal|panoramica|3d
    def descargarCaratula(self , IDGAME, tipo = "normal"):
        if (self.existeCaratula(IDGAME)):
            return True
        else:
            origen = 'http://www.theotherzone.com/wii/'
            regiones = ['pal/' , 'ntsc/' , 'ntscj/']
            if(tipo == "panoramica"):
                origen = origen + "widescreen/"
            elif(tipo == "3d"):
                origen = origen + "3d/160/225/"
                regiones = ['']
            descargada = False
            i = 0
            print _("***************** DESCARGAR CARATULA %s ********************" % (IDGAME))
            while ( not descargada and i<len(regiones)  ):
                origenGen = origen + regiones[i] + IDGAME + ".png"
                salida = os.system("wget --no-cache --directory-prefix=\""+config.HOME_WIITHON_CARATULAS+"\" " + origenGen)
                descargada = (salida == 0)
                if descargada:
                    destino = os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")
                    os.system("mogrify -resize 160x224! " + destino)
                i = i + 1
            return descargada

    # Descarga todos las caratulas de una lista de juegos
    def descargarTodasLasCaratulaYDiscos(self , DEVICE , listaJuegos , tipo = "normal"):
        ok = True
        for juego in listaJuegos:
            if ( not self.descargarCaratula( juego[0] , tipo ) ):
                ok = False
            if ( not self.descargarDisco( juego[0] ) ):
                ok = False
        return ok

    # Devuelve la lista de particiones
    def getListaParticiones(self):
        self.refrescarParticionWBFS()
        return self.listaParticiones

    # Procedimiento que refresca la lista de particiones
    def refrescarParticionWBFS(self):
        salida = util.getSTDOUT_NOERROR_iterador( config.DETECTOR_WBFS)

        self.listaParticiones = []

        for part in salida:
            if part.find("/dev/") != -1:
                self.listaParticiones.append(part.strip())

    # Devuelve el nombre del ISO que hay dentro de un RAR
    def getNombreISOenRAR(self , nombreRAR):
        comando = "rar lt -c- '"+nombreRAR+"' | grep -i '.iso' | awk -F'.iso'  '{print $1}' | awk -F' ' '{print $0\".iso\"}' | sed 's/^ *//' | sed 's/ *$//'"
        tuberia = os.popen(comando)
        salida_estandar = tuberia.readlines()
        tuberia.close()
        for linea in salida_estandar:
            # Quitar el salto de linea
            linea = linea[:-1]
            if( util.getExtension(linea)=="iso" ):
                return linea
        return ""

    # Descomprime todos los ISO de un RAR (FIXME: se espera que solo haya 1)
    def descomprimirRARconISODentro(self , nombreRAR ):
        try:
            comando = 'rar e -o- "%s" "%s"' % (nombreRAR , "*.iso")
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open("/dev/null","w"))
            return (salida == 0)
        except KeyboardInterrupt:
            return False

    # FUNCIÓN de PRUEBAS, no es usado actualmente
    # Se pasa como parametro ej: /dev/sdb2
    def redimensionarParticionWBFS(self , particion):
        # 57 42 46 53 00 0b 85 30
        # 57 42 46 53 00 29 ea eb

        comando = "fdisk -lu | grep -v 'MB' | grep '"+particion+"' | awk '{print $3-$2+1}'"
        entrada, salida = os.popen2(comando)
        salida = salida.read()

        offset = 0x4
        valor = int(salida)

        print "Se va escribir en la particion %s : %x:%x" % ( particion , offset , valor )
        respuesta = raw_input("¿Seguir? (S/N)\n")

        if (respuesta.lower() == 's'):
            byte1 = (valor & 0xFF000000) >> 8*3
            byte2 = (valor & 0x00FF0000) >> 8*2
            byte3 = (valor & 0x0000FF00) >> 8
            byte4 = (valor & 0x000000FF)

            f = open(particion , "wb")
            f.seek(offset , os.SEEK_SET)
            f.write('%c%c%c%c' % ( byte1 , byte2 , byte3 , byte4 ) )
            f.close()
            print "4 bytes escritos."
        else:
            print "sin cambios."

    def setParticionSeleccionada(self , particionSeleccionada):
        self.particionSeleccionada = particionSeleccionada

    def getDeviceSeleccionado(self):
        try:
            retorno = self.listaParticiones[self.particionSeleccionada].split(":")[0]
            return retorno
        except IndexError:
            return "%"

    def getFabricanteSeleccionado(self):
        try:
            retorno = self.listaParticiones[self.particionSeleccionada].split(":")[1]
            return retorno
        except IndexError:
            return "?"

    def setInterfaz(self , interfaz):
        self.interfaz = interfaz

