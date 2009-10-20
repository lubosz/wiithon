#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys
import os
import time
import commands
from Queue import Queue
from threading import Thread

import gtk
import gettext
import shutil

import util
import config
from util import NonRepeatList, SintaxisInvalida
from wiitdb_schema import Juego, Particion
from preferencias import Preferencias

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiithonCORE:
    
    prefs = Preferencias()

    def syncronizarJuegos(self , particion):
        comando = "%s -p %s ls" % (config.WBFS_APP, particion.device)
        lineas = util.getSTDOUT_NOERROR_iterador( comando )
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
                '''
            else:
                session.update(juego)
                '''

                juego.particion = particion

            salida.append(juego)

        session.commit()

        return salida


    # Devuelve la lista de particiones
    def sincronizarParticiones(self, detector = config.DETECTOR_WBFS):

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
                    '''
                else:
                    session.update(particion)
                    '''
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
    
    '''
    def getJuego(self, DEVICE, IDGAME):
        sql = util.decode("particion.device='%s' and juego.idgame=='%s'" % (DEVICE, IDGAME))
        juego = session.query(Juego,Particion).filter(sql).first()        
        if juego != None:
            juego = juego[0]
        return juego
    '''

    def getInfoJuego(self, DEVICE, IDGAME):
        particion = self.getParticion(DEVICE)
        print particion
        if particion != None:
            comando = "%s -p %s ls %s" % (config.WBFS_APP, DEVICE, IDGAME)
            linea = util.getSTDOUT( comando )
            cachos = linea.strip().split(config.SEPARADOR)
            print cachos
            juego = Juego(cachos)
            juego.particion = particion
            session.save(juego)
            print session
            print juego
            session.commit()
            return juego
        else:
            return None

    '''
    def getJuego(self, particion, IDGAME):
        sql = util.decode("particion.idParticion='%d' and juego.idgame=='%s'" % (particion.idParticion, IDGAME))
        juego = session.query(Juego,Particion).filter(sql).first()        
        if juego != None:
            juego = juego[0]
        return juego
    
    def getInfoJuego(self, DEVICE, IDGAME):
        particion = self.getParticion(DEVICE)
        print particion
        if particion != None:
            #juego = self.getJuego(particion, IDGAME)
            #print juego
            #if juego == None:
            comando = "%s -p %s ls %s" % (config.WBFS_APP, DEVICE, IDGAME)
            linea = util.getSTDOUT(comando)
            cachos = linea.split(config.SEPARADOR)
            juego = Juego(cachos)
            session.save(juego)
            juego.particion = particion
            session.commit()
            return juego
        else:
            return None
    '''

    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarNOMBRE(self , juego, nuevoNombre):
        comando = '%s -p %s rename "%s" "%s"' % (config.WBFS_APP, juego.particion.device, juego.idgame, nuevoNombre)
        print comando
        salida = util.call_out_screen(comando)
        return salida

    def renombrarIDGAME(self , juego , nuevoIDGAME):
        comando = '%s -p %s rename_idgame "%s" "%s"' % (config.WBFS_APP, juego.particion.device, juego.idgame, nuevoIDGAME)
        salida = util.call_out_screen(comando)
        return salida

    # borra el juego IDGAME
    def borrarJuego(self , juego):
        comando = "%s -p %s rm %s" % (config.WBFS_APP, juego.particion.device, juego.idgame)
        salida = util.call_out_screen(comando)
        return salida

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

    def clonarJuego(self, juego , parti_destino ):
        comando = "%s -p %s clonar %s %s" % (config.WBFS_APP , juego.particion.device , juego.idgame , parti_destino.device)
        salida = util.call_out_file(comando)
        return salida

    # Nos dice si existe la caratula del juego "IDGAME"
    def existeCaratula(self , IDGAME):
        ruta = self.getRutaCaratula(IDGAME)
        existe = (os.path.exists( ruta ))
        if existe and not util.esPNG(ruta):
            os.remove(ruta)
            existe = False
        return existe

    def descargarDisco(self , IDGAME):
        if (self.existeDisco(IDGAME)):
            return True
        else:
            print _("***************** DESCARGAR DISCO %s ********************") % (IDGAME)
            try:
                origen = "http://www.wiiboxart.com/diskart/160/160/%.3s.png" % (IDGAME)
                destino = self.getRutaDisco(IDGAME)
                util.descargarImagen(origen, destino)
                comando = 'mogrify -resize %dx%d! "%s"' % (self.prefs.WIDTH_DISCS, self.prefs.HEIGHT_DISCS, destino)
                util.call_out_null(comando)
                return True
            except util.ErrorDescargando:
                return False

    # Descarga una caratula de "IDGAME"
    def descargarCaratula(self , IDGAME):
        if (self.existeCaratula(IDGAME)):
            return True
        else:
            destino = self.getRutaCaratula(IDGAME)
            descargada = False
            i = 0
            proveedores = self.prefs.PROVIDER_COVERS
            print proveedores
            while ( not descargada and i<len(proveedores) ):
                try:
                    print _("Descargando caratula de %s desde %s ...") % (IDGAME, proveedores[i] % IDGAME)
                    util.descargarImagen(proveedores[i] % IDGAME, destino)
                    comando = 'mogrify -resize %dx%d! "%s"' % (self.prefs.WIDTH_COVERS, self.prefs.HEIGHT_COVERS, destino)
                    util.call_out_null(comando)
                except util.ErrorDescargando:
                    i += 1
                if (self.existeCaratula(IDGAME)):
                    descargada = True
            return descargada

    # borrar caratula
    def borrarCaratula( self, juego ):
        if self.existeCaratula( juego.idgame ):
            os.remove( self.getRutaCaratula( juego.idgame ) )

    # Descarga todos las caratulas de una lista de juegos
    def descargarTodasLasCaratulaYDiscos(self , listaJuegos):
        ok = True
        for juego in listaJuegos:
            if ( not self.descargarCaratula( juego.idgame ) ):
                ok = False
            if ( not self.descargarDisco( juego.idgame ) ):
                ok = False
        return ok

    def getNombreISOenRAR(self , nombreRAR):
        comando = '%s lt "%s"' % (config.UNRAR_APP, nombreRAR)
        lineas = util.getSTDOUT_NOERROR_iterador( comando )
        for linea in lineas:
            linea = linea.strip()
            if( util.getExtension(linea)=="iso" ):
                return linea
        return None

    def unpack(self , nombreRAR , destino, nombreISO):
        if os.path.isfile(nombreRAR) and os.path.isdir(destino):
            rutaISO = os.path.join(destino, nombreISO)
            if os.path.exists(rutaISO):
                os.remove(rutaISO)
            directorioActual = os.getcwd()
            os.chdir(destino)
            comando = '%s e "%s" "%s"' % (config.UNRAR_APP, nombreRAR , nombreISO)
            salida = util.call_out_file(comando)
            os.chdir(directorioActual)
            return salida
        else:
            return False

    def anadirISO(self , DEVICE , ISO):
        
        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(DEVICE, Particion):
            DEVICE = DEVICE.device

        comando = '%s -p %s add "%s"' % (config.WBFS_APP, DEVICE, ISO)
        salida = util.call_out_file(comando)
        return salida

    def existeExtraido(self, juego, destino):
        fichero = "%s.iso" % juego.title
        fichero = fichero.replace(" ","_")
        fichero = fichero.replace("/","_")
        fichero = fichero.replace(":","_")
        destino = os.path.join(destino , fichero)
        return os.path.exists(destino)

    # extrae el juego a un destino
    def extraerJuego(self ,juego , destino = ''):
        if destino != '':
            trabajoActual = os.getcwd()
            os.chdir( destino )

        comando = "%s -p %s extract %s" % (config.WBFS_APP, juego.particion.device , juego.idgame)
        salida = util.call_out_file(comando)

        if destino != '':
            os.chdir( trabajoActual )
        return salida
        
    def getEspacioLibreUsado(self, particion):
        comando = "%s -p %s df" % (config.WBFS_APP, particion.device)
        salida = util.getSTDOUT(comando)
        cachos = salida.split(config.SEPARADOR)
        if(len(cachos) == 3):
            return [float(cachos[0]), float(cachos[1]), float(cachos[2])]
        else:
            return [0.0, 0.0 ,0.0]

    def formatearWBFS(self, particion):
        if particion.tipo == "fat32":
            comando = "%s -p %s formatear" % (config.WBFS_APP, particion.device)
            salida = util.call_out_screen(comando)
            return salida
        else:
            return False

