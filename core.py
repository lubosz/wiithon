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
from util import NonRepeatList, SintaxisInvalida
from wiitdb_schema import Juego, Particion
import config

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiithonCORE:
    # Obtiene un list de juegos en una tabla de 3 columnas:
    # index 0 -> IDGAME o identificador único del juego
    # index 1 -> Nombre del juego
    # index 2 -> Tamaño en GB redondeado a 2 cifras
    def getListaJuegos(self , particion):
        
        comando = "%s -p %s ls" % (config.WBFS_APP, particion.device)
        lineas = util.getSTDOUT_iterador( comando )
        salida = []
        for linea in lineas:
            cachos = linea.strip().split(config.SEPARADOR)

            idgame = util.decode(cachos[0])
            sql = util.decode("juego.idgame=='%s' and particion.device='%s'" % (idgame, particion.device))
            juego = session.query(Juego,Particion).filter(sql).first()        
            if juego == None:
                juego = Juego(cachos)
                session.save(juego)
            else:
                juego = juego[0]
                session.update(juego)

            juego.particion = particion

            salida.append(juego)
        
        session.commit()

        return salida

    # Devuelve la lista de particiones
    def getListaParticiones(self, detector = config.DETECTOR_WBFS):
       
        salida = util.getSTDOUT_NOERROR_iterador(detector)

        listaParticiones = []

        for linea in salida:
            if linea.find("/dev/") != -1:
                cachos = linea.strip().split(config.SEPARADOR)

                device = util.decode(cachos[0])
                sql = util.decode("device=='%s'" % (device))
                particion = session.query(Particion).filter(sql).first()
                
                if particion == None:
                    particion = Particion(cachos)
                    session.save(particion)
                else:
                    session.update(particion)

                listaParticiones.append(particion)
                
        session.commit()

        return listaParticiones


    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarNOMBRE(self , DEVICE , IDGAME , NUEVO_NOMBRE):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rename "+IDGAME+" \""+NUEVO_NOMBRE+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False
            
    def renombrarIDGAME(self , DEVICE , IDGAME , NUEVO_IDGAME):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
        try:
            comando = config.WBFS_APP+" -p "+DEVICE+" rename_idgame "+IDGAME+" \""+NUEVO_IDGAME+"\""
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # getEspacioLibre obtiene una tupla [uso , libre , total]
    def getEspacioLibre(self , DEVICE):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
        comando = "%s -p %s df" % (config.WBFS_APP, DEVICE)
        salida = util.getSTDOUT( comando )
        cachos = salida.split(config.SEPARADOR)
        if(len(cachos) == 3):
            try:
                return [ float(cachos[0]) , float(cachos[1]) , float(cachos[2]) ]
            except:
                pass
        # en caso error, devuelve una tupla de 3 de float a 0
        return [ 0.0 , 0.0 , 0.0 ]

    # borra el juego IDGAME
    def borrarJuego(self , DEVICE , IDGAME):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
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

    def getRutaDisco(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_DISCOS , "%s.png" % (IDGAME))

    def getRutaCaratula(self , IDGAME):
        return os.path.join(config.HOME_WIITHON_CARATULAS , "%s.png" % (IDGAME))

    def copiarCaratula(self , juego , destino):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( self.existeCaratula(juego.idgame) ):
            try:
                origen = self.getRutaCaratula(juego.idgame)
                print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
                shutil.copyfile(origen, destino)
                return True
            except:
                return False
        else:
            return False
        '''
        if( not os.path.exists( destino ) and self.existeDisco(juego.idgame) ):
            origen = self.getRutaCaratula(juego.idgame)
            print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
            shutil.copy(origen, destino)
            return os.path.exists(destino)
        else:
            print _("Ya tienes la caratula %s") % (juego.idgame)
            return True
        '''

    def copiarDisco(self , juego , destino):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( self.existeDisco(juego.idgame) ):
            try:
                origen = self.getRutaDisco(juego.idgame)
                print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
                shutil.copyfile(origen, destino)
                return True
            except:
                return False
        else:
            return False
            
        '''
        if( not os.path.exists( destino ) and self.existeCaratula(juego.idgame) ):
            origen = self.getRutaDisco(juego.idgame)
            print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
            shutil.copy(origen, destino)
            return os.path.exists(destino)
        else:
            print _("Ya tienes el disco-caratula %s") % (juego.idgame)
            return True
        '''

    # borrar disco
    def borrarDisco( self , juego ):
        if self.existeDisco( juego.idgame ):
            os.remove( self.getRutaDisco( juego.idgame ) )

    def clonarJuego(self, juego , DEVICE ):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
        try:
            comando = "%s -p %s clonar %s %s" % (config.WBFS_APP , juego.particion.device , juego.idgame , DEVICE)
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

    def descargarDisco(self , IDGAME, ancho=160, alto=160):
        if (self.existeDisco(IDGAME)):
            return True
        else:
            print _("***************** DESCARGAR DISCO %s ********************") % (IDGAME)
            try:
                origen = "http://www.wiiboxart.com/diskart/160/160/%.3s.png" % (IDGAME)
                destino = self.getRutaDisco(IDGAME)
                util.descargarImagen(origen, destino)
                os.system("mogrify -resize %dx%d! %s" % (ancho, alto, destino))
                return True
            except util.ErrorDescargando:
                return False

    # Descarga una caratula de "IDGAME"
    # el Tipo puede ser : normal|panoramica|3d|full
    def descargarCaratula(self , IDGAME, tipo = "normal", ancho=160, alto=224):
        if (self.existeCaratula(IDGAME)):
            return True
        else:
            origenes = []
            if(tipo == "panoramica"):
                origenes.append("http://www.wiiboxart.com/widescreen/pal/%s.png" % IDGAME)
                origenes.append("http://www.wiiboxart.com/widescreen/ntsc/%s.png" % IDGAME)
                origenes.append("http://www.wiiboxart.com/widescreen/ntscj/%s.png" % IDGAME)
            elif(tipo == "3d"):
                origenes.append("http://www.wiiboxart.com/3d/160/225/%s.png" % IDGAME)
            elif(tipo == "full"):
                origenes.append("http://www.wiiboxart.com/fullcover/%s.png" % IDGAME)
            else:
                origenes.append("http://www.wiiboxart.com/pal/%s.png" % IDGAME)
                origenes.append("http://www.wiiboxart.com/ntsc/%s.png" % IDGAME)
                origenes.append("http://www.wiiboxart.com/ntscj/%s.png" % IDGAME)
            destino = self.getRutaCaratula(IDGAME)
            descargada = False
            i = 0
            print _("***************** DESCARGAR CARATULA %s ********************") % (IDGAME)
            
            while ( not descargada and i<len(origenes) ):
                try:
                    util.descargarImagen(origenes[i], destino)
                    os.system("mogrify -resize %dx%d! %s" % (ancho, alto, destino))
                    descargada = True
                except util.ErrorDescargando:
                    i += 1
            return descargada

    # borrar caratula
    def borrarCaratula( self, juego ):
        if self.existeCaratula( juego.idgame ):
            os.remove( self.getRutaCaratula( juego.idgame ) )

    # Descarga todos las caratulas de una lista de juegos
    # FIXME: DEVICE NO SIRVE PARA NADA
    def descargarTodasLasCaratulaYDiscos(self , DEVICE , listaJuegos , tipo = "normal"):
        ok = True
        for juego in listaJuegos:
            if ( not self.descargarCaratula( juego[0] , tipo ) ):
                ok = False
            if ( not self.descargarDisco( juego[0] ) ):
                ok = False
        return ok

    def getNombreISOenRAR(self , nombreRAR):
        comando = '%s lt "%s"' % (config.UNRAR_APP, nombreRAR)
        lineas = util.getSTDOUT_iterador( comando )
        for linea in lineas:
            linea = linea.strip()
            if( util.getExtension(linea)=="iso" ):
                return linea
        return ""

    def unpack(self , nombreRAR , destino):
        try:
            if os.path.isfile(nombreRAR) and os.path.isdir(destino):
                nombreISO = self.getNombreISOenRAR(nombreRAR)
                if nombreISO != "":
                    rutaISO = os.path.join(destino, nombreISO)
                    if not os.path.exists(rutaISO):
                        directorioActual = os.getcwd()
                        os.chdir(destino)
                        comando = '%s e "%s" "%s"' % (config.UNRAR_APP, nombreRAR , nombreISO)
                        salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT, stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
                        os.chdir(directorioActual)
                        return (salida == 0)
                    else:
                        return False
                else:
                    return False
            else:
                return False
        except KeyboardInterrupt:
            return False

    '''
    # FUNCIÓN de PRUEBAS, no es usado actualmente
    # Se pasa como parametro ej: /dev/sdb2
    def redimensionarParticionWBFS(self , DEVICE):
        # 57 42 46 53 00 0b 85 30
        # 57 42 46 53 00 29 ea eb

        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device

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
    '''

    # añade un *ISO* a un *DEVICE*
    def anadirISO(self , DEVICE , ISO):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device
        
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
            comando = "%s -p %s extract %s" % (config.WBFS_APP, juego.particion.device , juego.idgame)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
            # volvemos al directorio original
            os.chdir( trabajoActual )
            return salida == 0
        except KeyboardInterrupt:
            return False

    def formatearWBFS(self, particion):
        if particion.tipo == "fat32":
            comando = "%s -p %s formatear" % (config.WBFS_APP, particion.device)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        else:
            return False

