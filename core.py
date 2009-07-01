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
    
    # indice (fila) de la partición seleccionado para 1on1
    particionSeleccionada_1on1 = 1

    #constructor
    def __init__(self):
        pass

    # Obtiene un list de juegos en una tabla de 3 columnas:
    # index 0 -> IDGAME o identificador único del juego
    # index 1 -> Nombre del juego
    # index 2 -> Tamaño en GB redondeado a 2 cifras
    def getListaJuegos(self , DEVICE):
        comando = "%s -p %s ls" % (config.WBFS_APP, DEVICE)
        lineas = util.getSTDOUT_iterador( comando )
        salida = []
        for linea in lineas:
            cachos = linea.strip().split(config.SEPARADOR)
            if(len(cachos)==3):
                salida.append( [ cachos[0] , cachos[1] , cachos[2] ] )
        return salida

    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarNOMBRE(self , DEVICE , IDGAME , NUEVO_NOMBRE):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False
            
    def renombrarIDGAME(self , DEVICE , IDGAME , NUEVO_IDGAME):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rename_idgame "+IDGAME+" \""+NUEVO_IDGAME+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # getEspacioLibre obtiene una tupla [uso , libre , total]
    def getEspacioLibre(self , DEVICE):
        salida = util.getSTDOUT( config.WBFS_APP+" -p "+DEVICE+" df" )
        cachos = salida.split(config.SEPARADOR)
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

    def existeDisco(self , IDGAME):
        ruta = self.getRutaDisco(IDGAME)
        existe = (os.path.exists( ruta ))
        if existe and not util.esPNG(ruta):
            os.remove(ruta)
            existe = False
        return existe

    def descargarDisco(self , IDGAME):
        if (self.existeDisco(IDGAME)):
            return True
        else:
            print _("***************** DESCARGAR DISCO %s ********************" % (IDGAME))
            try:
                origen = "www.wiiboxart.com"
                destino = self.getRutaDisco(IDGAME)
                # Solo las 3 primeras letras del disco, la web cambio a ese formato a finales de junio
                origenGen = "diskart/160/160/%s.png" % (IDGAME[:3])
                util.descargarImagen(origen, origenGen, destino)
                os.system("mogrify -resize 160x160! %s" % (destino))
                return True
            except util.ErrorDescargando:
                return False

    def getRutaDisco(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")

    def getRutaCaratula(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")

    def copiarCaratula(self , juego , destino):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( not os.path.exists( destino ) and self.existeDisco(juego.idgame) ):
            origen = self.getRutaCaratula(juego.idgame)
            print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
            shutil.copy(origen, destino)
            return os.path.exists(destino)
        else:
            print _("Ya tienes la caratula %s") % (juego.idgame)
            return True

    def copiarDisco(self , juego , destino):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( not os.path.exists( destino ) and self.existeCaratula(juego.idgame) ):
            origen = self.getRutaDisco(juego.idgame)
            print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
            shutil.copy(origen, destino)
            return os.path.exists(destino)
        else:
            print _("Ya tienes el disco-caratula %s") % (juego.idgame)
            return True

    # borrar disco
    def borrarDisco( self , juego ):
        if self.existeDisco( juego.idgame ):
            os.remove( self.getRutaDisco( juego.idgame ) )

    def clonarJuego(self, juego , DEVICE ):
        try:
            comando = "%s -p %s clonar %s %s" % (config.WBFS_APP , juego.device , juego.idgame , DEVICE)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # Nos dice si existe la caratula del juego "IDGAME"
    def existeCaratula(self , IDGAME):
        ruta = self.getRutaCaratula(IDGAME)
        existe = (os.path.exists( ruta ))
        if existe and not util.esPNG(ruta):
            os.remove(ruta)
            existe = False
        return existe

    # Descarga una caratula de "IDGAME"
    # el Tipo puede ser : normal|panoramica|3d
    def descargarCaratula(self , IDGAME, tipo = "normal"):
        if (self.existeCaratula(IDGAME)):
            return True
        else:
            origen = "www.wiiboxart.com"
            destino = self.getRutaCaratula(IDGAME)
            regiones = ['pal/' , 'ntsc/' , 'ntscj/']
            if(tipo == "panoramica"):
                ruta_imagen = "widescreen/"
            elif(tipo == "3d"):
                ruta_imagen = "3d/160/225/"
                regiones = ['']
            else:
                ruta_imagen = ""
            descargada = False
            i = 0
            print _("***************** DESCARGAR CARATULA %s ********************" % (IDGAME))
            while ( not descargada and i<len(regiones) ):
                origenGen = ruta_imagen + regiones[i] + IDGAME + ".png"
                try:
                    util.descargarImagen(origen, origenGen, destino)
                    os.system("mogrify -resize 160x224! %s" % (destino))
                    descargada = True
                except util.ErrorDescargando:
                    i += 1
            return descargada

    # borrar caratula
    def borrarCaratula( self, juego ):
        if self.existeCaratula( juego.idgame ):
            os.remove( self.getRutaCaratula( juego.idgame ) )

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
        salida = util.getSTDOUT_NOERROR_iterador( config.DETECTOR_WBFS)

        self.listaParticiones = []

        for part in salida:
            if part.find("/dev/") != -1:
                self.listaParticiones.append(part.strip())
        return self.listaParticiones

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
            #directorioActual = os.getcwd()
            #os.chdir('/tmp')
            comando = 'rar e -o- "%s" "%s"' % (nombreRAR , "*.iso")
            salida = subprocess.call( comando , shell=True ,
                    stderr=subprocess.STDOUT , stdout=open(os.devnull,"w"))
            #os.chdir(directorioActual)
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

    def setParticionSeleccionada_1on1(self , particionSeleccionada):
        self.particionSeleccionada_1on1 = particionSeleccionada

    #FIXME: rediseñar todo esto ...
    def getDeviceSeleccionado(self):
        try:
            retorno = self.listaParticiones[self.particionSeleccionada].split(":")[0]
            return retorno
        except IndexError:
            return "%"

    def getDeviceSeleccionado_1on1(self):
        try:
            retorno = self.listaParticiones[self.particionSeleccionada_1on1].split(":")[0]
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


    # añade un *ISO* a un *DEVICE*
    def anadirISO(self , DEVICE , ISO):
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" add \""+ISO+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            return salida == 0
        except KeyboardInterrupt:
            return False

    def existeExtraido(self, juego, destino):
        fichero = "%s.iso" % juego.title
        fichero = fichero.replace(" ","_")
        fichero = fichero.replace("/","_")
        fichero = fichero.replace(":","_")
        destino = os.path.join(destino , fichero)
        return os.path.exists(destino)

    # extrae el juego a un destino
    def extraerJuego(self ,juego , destino):
        try:
            # backup del actual pwd
            trabajoActual = os.getcwd()
            # cambiamos de directorio de trabajo
            os.chdir( destino )
            comando = "%s -p %s extract %s" % (config.WBFS_APP, juego.device , juego.idgame)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            # volvemos al directorio original
            os.chdir( trabajoActual )
            return salida == 0
        except KeyboardInterrupt:
            return False

