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

    def syncronizarJuegos(self , particion):

        comando = "%s -p %s ls" % (config.WBFS_APP, particion.device)
        lineas = util.getSTDOUT_iterador( comando )
        salida = []
        for linea in lineas:
            cachos = linea.strip().split(config.SEPARADOR)

            idgame = util.decode(cachos[0])
            sql = util.decode("idgame=='%s' and idParticion='%s'" % (idgame, particion.idParticion))
            juego = session.query(Juego).filter(sql).first()
            if juego == None:
                try:
                    juego = Juego(cachos)
                    session.save(juego)
                except SintaxisInvalida:
                    continue
            else:
                session.update(juego)

            juego.particion = particion

            salida.append(juego)
        
        session.commit()

        return salida
        
        
    # Devuelve la lista de particiones
    def sincronizarParticiones(self, detector = config.DETECTOR_WBFS):

        #session.execute('DELETE FROM rel_particion_juego where idParticion = "%d"' % particion.idParticion)
        #session.execute('DELETE FROM rel_particion_juego')

        salida = util.getSTDOUT_NOERROR_iterador(detector)

        listaParticiones = []

        for linea in salida:
            if linea.find("/dev/") != -1:
                cachos = linea.strip().split(config.SEPARADOR)

                device = util.decode(cachos[0])
                
                particion = self.getParticion(device)
                
                if particion == None:
                    try:
                        particion = Particion(cachos)
                        session.save(particion)
                    except SintaxisInvalida:
                        continue
                else:
                    session.update(particion)

                listaParticiones.append(particion)

        session.commit()
        
        sql = "DELETE FROM juego WHERE "
        for particion in listaParticiones:
            sql += "idParticion <> %d AND " % particion.idParticion
        sql += "1"
        session.execute(sql)
        
        session.commit()

        return listaParticiones
        
        
    def getParticion(self, DEVICE):
        sql = util.decode("device=='%s'" % (DEVICE))
        particion = session.query(Particion).filter(sql).first()
        return particion
        
    def getJuego(self, DEVICE, IDGAME):
        sql = util.decode("particion.device='%s' and juego.idgame=='%s'" % (DEVICE, IDGAME))
        juego = session.query(Juego,Particion).filter(sql).first()        
        if juego != None:
            juego = juego[0]
        return juego
    
    def getInfoJuego(self, DEVICE, IDGAME):
        
        particion = self.getParticion(DEVICE)
        if particion != None:
            
            comando = "%s -p %s ls %s" % (config.WBFS_APP, particion.device, IDGAME)
            linea = util.getSTDOUT( comando )

            cachos = linea.strip().split(config.SEPARADOR)

            juego = self.getJuego(particion.device, IDGAME)
            if juego == None:
                juego = Juego(cachos)
                session.save(juego)
            else:
                session.update(juego)

            juego.particion = particion
            
            session.commit()

            return juego

        else:
            return None


    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarNOMBRE(self , juego, nuevoNombre):
        try:
            comando = '%s -p %s rename "%s" "%s"' % (config.WBFS_APP, juego.particion.device, juego.idgame, nuevoNombre)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False
            
    def renombrarIDGAME(self , juego , nuevoIDGAME):
        try:
            comando = '%s -p %s rename_idgame "%s" "%s"' % (config.WBFS_APP, juego.particion.device, juego.idgame, nuevoIDGAME)
            salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT )
            return salida == 0
        except KeyboardInterrupt:
            return False

    # borra el juego IDGAME
    def borrarJuego(self , juego):
    
        try:
            #comando = config.WBFS_APP+" -p "+DEVICE+" rm "+IDGAME
            comando = "%s -p %s rm %s" % (config.WBFS_APP, juego.particion.device, juego.idgame)
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

    # borrar disco
    def borrarDisco( self , juego ):
        if self.existeDisco( juego.idgame ):
            os.remove( self.getRutaDisco( juego.idgame ) )

    def clonarJuego(self, juego , particion ):

        try:
            comando = "%s -p %s clonar %s %s" % (config.WBFS_APP , juego.particion.device , juego.idgame , particion.device)
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
            print "ya existe %s" % IDGAME
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
    def descargarTodasLasCaratulaYDiscos(self , listaJuegos , tipo = "normal"):
        ok = True
        for juego in listaJuegos:
            if ( not self.descargarCaratula( juego , tipo ) ):
                ok = False
            if ( not self.descargarDisco( juego ) ):
                ok = False
        return ok

    def getNombreISOenRAR(self , nombreRAR):
        comando = '%s lt "%s"' % (config.UNRAR_APP, nombreRAR)
        lineas = util.getSTDOUT_iterador( comando )
        for linea in lineas:
            linea = linea.strip()
            if( util.getExtension(linea)=="iso" ):
                return linea
        return None

    def unpack(self , nombreRAR , destino, nombreISO):
        try:
            if os.path.isfile(nombreRAR) and os.path.isdir(destino):
                rutaISO = os.path.join(destino, nombreISO)
                if os.path.exists(rutaISO):
                    os.remove(rutaISO)
                directorioActual = os.getcwd()
                os.chdir(destino)
                comando = '%s e "%s" "%s"' % (config.UNRAR_APP, nombreRAR , nombreISO)
                salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT, stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
                os.chdir(directorioActual)
                return (salida == 0)
            else:
                return False
        except KeyboardInterrupt:
            return False

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

