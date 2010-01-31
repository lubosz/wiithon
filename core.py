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
from util import SintaxisInvalida
from wiitdb_schema import Juego, Particion
from preferencias import Preferencias

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiithonCORE:

    def __init__(self, prefs):
        self.prefs = prefs

    def syncronizarJuegos(self , particion):
        comando = "%s -p %s ls" % (config.WBFS_APP, particion.device)
        lineas = util.getSTDOUT_NOERROR_iterador( comando )
        salida = []
        for linea in lineas:
            cachos = linea.strip().split(config.SEPARADOR)
            idgame = util.decode(cachos[0])
            sql = util.decode("idgame=='%s' and idParticion='%s'" % (idgame, particion.idParticion))
            juego = session.query(Juego).filter(sql).first()
            if juego is not None:
                # el juego ya existe, se borra
                session.delete(juego)
                
                # guardan cambios
                session.commit()
                
            try:
                juego = Juego(cachos)
                juego.particion = particion
                session.save(juego)
                salida.append(juego)
                session.commit()

            except SintaxisInvalida:
                continue

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
                if particion is not None:

                    # borrar TODOS los juegos de esta particion
                    query = session.query(Juego)
                    query = query.filter("idParticion = %d" % particion.idParticion)
                    for juego in query:
                        session.delete(juego)
                        
                    # ya borro la particion
                    session.delete(particion)
                    
                    # guardar cambios
                    session.commit()

                try:
                    particion = Particion(cachos)
                    session.save(particion)
                    listaParticiones.append(particion)
                    session.commit()
                    
                except SintaxisInvalida:
                    continue
        
        if len(listaParticiones) > 0:

            # borrar TODOS los juegos que no sean de las particiones encontradas
            query = session.query(Juego)
            for particion in listaParticiones:
                query = query.filter("idParticion <> %d" % particion.idParticion)
            for juego in query:
                session.delete(juego)
            
            # borrar TODAS las particiones que no sean de las particiones encontradas    
            query = session.query(Particion)
            for particion in listaParticiones:
                query = query.filter("idParticion <> %d" % particion.idParticion)
            for particion in query:
                session.delete(particion)
            
            # subimos cambios    
            session.commit()

        return listaParticiones

    def getParticion(self, DEVICE):
        sql = util.decode("device=='%s'" % (DEVICE))
        particion = session.query(Particion).filter(sql).first()
        return particion

    def getJuego(self, DEVICE, IDGAME):
        sql = util.decode("particion.device='%s' and juego.idgame=='%s'" % (DEVICE, IDGAME))
        for juego, particion in session.query(Juego,Particion).filter(sql):
            return juego
        return None

    def new_game_from_HDD(self, DEVICE, IDGAME):
        particion = self.getParticion(DEVICE)
        if particion != None:
            comando = "%s -p %s ls %s" % (config.WBFS_APP, DEVICE, IDGAME)
            linea = util.getSTDOUT( comando )
            cachos = linea.strip().split(config.SEPARADOR)
            juego = Juego(cachos)
            juego.particion = particion
            session.save(juego)
            session.commit()
            return juego
        else:
            return None

    # renombra el ISO de un IDGAME que esta en DEVICE
    def renombrarNOMBRE(self , juego, nuevoNombre):
        comando = '%s -p %s rename "%s" "%s"' % (config.WBFS_APP, juego.particion.device, juego.idgame, nuevoNombre)
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

    # Nos dice si existe la caratula del juego "IDGAME"
    def existeCaratula(self , IDGAME, borrar_si_no_es_png = False, TYPE_COVER = util.COVER_NORMAL):
        ruta = self.getRutaCaratula(IDGAME, TYPE_COVER)
        existe = (os.path.exists( ruta ))
        if existe and borrar_si_no_es_png and not util.esPNG(ruta):
            os.remove(ruta)
            existe = False
        return existe

    def existeDisco(self , IDGAME, borrar_si_no_es_png = False, TYPE_DISC_ART = util.DISC_ORIGINAL):
        ruta = self.getRutaDisco(IDGAME, TYPE_DISC_ART)
        existe = (os.path.exists( ruta ))
        if existe and borrar_si_no_es_png and not util.esPNG(ruta):
            os.remove(ruta)
            existe = False
        return existe

    def getRutaDisco(self , IDGAME, TYPE_DISC_ART = util.DISC_ORIGINAL):
        if TYPE_DISC_ART == util.DISC_CUSTOM:
            return os.path.join(config.HOME_WIITHON_DISCOS_CUSTOM , "%s.png" % (IDGAME))
        else: # if TYPE_DISC_ART == util.DISC_ORIGINAL:
            return os.path.join(config.HOME_WIITHON_DISCOS , "%s.png" % (IDGAME))

    def getRutaCaratula(self , IDGAME, TYPE_COVER = util.COVER_NORMAL):
        if TYPE_COVER == util.COVER_3D:
            return os.path.join(config.HOME_WIITHON_CARATULAS_3D , "%s.png" % (IDGAME))
        if TYPE_COVER == util.COVER_FULL:
            return os.path.join(config.HOME_WIITHON_CARATULAS_TOTAL , "%s.png" % (IDGAME))
        else: # if TYPE_COVER == util.COVER_NORMAL:
            return os.path.join(config.HOME_WIITHON_CARATULAS , "%s.png" % (IDGAME))

    def copiarCaratula(self , juego , destino, TYPE_COVER = util.COVER_NORMAL):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( self.existeCaratula(juego.idgame, False, TYPE_COVER) ):
            try:
                origen = self.getRutaCaratula(juego.idgame, TYPE_COVER)
                if util.esPNG(origen):
                    if config.DEBUG:
                        print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
                    shutil.copyfile(origen, destino)
                return True

            except:
                return False
        else:
            return True

    def copiarDisco(self , juego , destino, TYPE_DISC_ART = util.DISC_ORIGINAL):
        destino = os.path.join( os.path.abspath(destino) , "%s.png" % (juego.idgame) )
        if( self.existeDisco(juego.idgame, False, TYPE_DISC_ART) ):
            try:
                origen = self.getRutaDisco(juego.idgame, TYPE_DISC_ART)
                if util.esPNG(origen):
                    if config.DEBUG:
                        print "%s %s ----> %s ... " % (_("Copiando"), origen , destino)
                    shutil.copyfile(origen, destino)
                return True

            except:
                return False
        else:
            return True

    # borrar disco
    def borrarDisco( self , juego , TYPE_DISC_ART = util.DISC_ORIGINAL):
        if self.existeDisco( juego.idgame , False, TYPE_DISC_ART):
            os.remove( self.getRutaDisco( juego.idgame , TYPE_DISC_ART) )

    def clonarJuego(self, juego , parti_destino ):
        comando = "%s -p %s clonar %s %s" % (config.WBFS_APP , juego.particion.device , juego.idgame , parti_destino.device)
        salida = util.call_out_file(comando)
        return salida
            
    def descargarDisco(self , IDGAME, proveedores, ancho, alto , TYPE_DISC_ART = util.DISC_ORIGINAL):
        destino = self.getRutaDisco(IDGAME, TYPE_DISC_ART)
        descargada = False
        i = util.get_subinterval_type_disc_art(TYPE_DISC_ART)
        while ( not descargada and i<len(proveedores) ):
            if (self.existeDisco(IDGAME, False, TYPE_DISC_ART)):
                raise util.YaEstaDescargado
            else:
                try:
                    origen = proveedores[i] % IDGAME
                    if config.DEBUG:
                        print _("Descargando disco de %s ...") % (("%s (%s)") % (IDGAME, origen))
                    util.descargarImagen(origen, destino)
                    descargada = True
                    comando = 'mogrify -resize %dx%d! "%s"' % (ancho, alto, destino)
                    util.call_out_null(comando)
                except util.ErrorDescargando:
                    i += 1
        return descargada

    # Descarga una caratula de "IDGAME"
    def descargarCaratula(self , IDGAME, proveedores, ancho, alto, TYPE_COVER = util.COVER_NORMAL):
        destino = self.getRutaCaratula(IDGAME, TYPE_COVER)
        descargada = False
        i = util.get_subinterval_type_cover(TYPE_COVER)
        while ( not descargada and i<len(proveedores) ):
            if (self.existeCaratula(IDGAME, False, TYPE_COVER)):
                raise util.YaEstaDescargado
            else:
                try:
                    origen = proveedores[i] % IDGAME
                    if config.DEBUG:
                        print _("Descargando caratula de %s desde %s ...") % (IDGAME, origen)
                    util.descargarImagen(origen, destino)
                    descargada = True
                    if TYPE_COVER != util.COVER_FULL:
                        comando = 'mogrify -resize %dx%d! "%s"' % (ancho, alto, destino)
                        util.call_out_null(comando)
                except util.ErrorDescargando:
                    i += 1
        return descargada

    # borrar caratula
    def borrarCaratula( self, juego , TYPE_COVER = util.COVER_NORMAL):
        if self.existeCaratula( juego.idgame , False, TYPE_COVER):
            os.remove( self.getRutaCaratula( juego.idgame, TYPE_COVER ) )

    # Descarga todos las caratulas de una lista de juegos
    def descargarTodasLasCaratulaYDiscos(self , listaJuegos):
        proveedores_covers = self.prefs.PROVIDER_COVERS
        width_covers = self.prefs.WIDTH_COVERS
        height_covers = self.prefs.HEIGHT_COVERS
        proveedores_discs = self.prefs.PROVIDER_DISCS
        width_discs = self.prefs.WIDTH_DISCS
        height_discs = self.prefs.HEIGHT_DISCS
        ok = True
        for juego in listaJuegos:
            if ( not self.descargarCaratula( juego.idgame, proveedores_covers, width_covers, height_covers ) ):
                ok = False
            if ( not self.descargarDisco( juego.idgame, proveedores_discs, width_discs, height_discs) ):
                ok = False
        return ok

    def getNombreISOenRAR(self , nombreRAR):
        comando = '%s lt "%s"' % (config.UNRAR_APP, nombreRAR)
        lineas = util.getSTDOUT_NOERROR_iterador( comando )
        for linea in lineas:
            linea = linea.strip()
            if(self.getAutodetectarFormato(linea) is not None):
                return linea
        return None

    def unpack(self , nombreRAR , destino, nombreISO, overwrite = True):

        if not os.path.isfile(nombreRAR):
            return False
 
        if not os.path.isdir(destino):
            return False

        rutaISO = os.path.join(destino, nombreISO)
        if os.path.exists(rutaISO):
            if overwrite:        
                os.remove(rutaISO)
            else:
                return False

        if not util.space_for_dvd_iso_wii(destino):
            return False

        if destino == ".":
            destino = os.path.dirname(nombreRAR)

        directorioActual = os.getcwd()
        os.chdir(destino)

        comando = '%s e "%s" "*%s"' % (config.UNRAR_APP, nombreRAR , nombreISO)
        salida = util.call_out_file(comando)

        os.chdir(directorioActual)

        return salida

    def getAutodetectarFormato(self, fichero):

        if( util.getExtension(fichero) == "iso" ):
            return "iso"
        elif( util.getExtension(fichero) == "wbfs" ):
            return "wbfs"
        elif( util.getExtension(fichero) == "wdf" ):
            return "wdf"
        else:
            return None

    def anadirISO(self , ruta_particion , fichero):

        # si pasa el objeto, cogemos el string que nos interesa
        if isinstance(ruta_particion, Particion):
            ruta_particion = ruta_particion.device
            
        formato = self.getAutodetectarFormato(fichero)
        if formato is not None:
            if formato == 'iso':
                comando = '%s -p %s add "%s"' % (config.WBFS_APP, ruta_particion, fichero)
            elif formato == 'wbfs':
                comando = '%s -f %s add_wbfs "%s"' % (config.WBFS_FILE, ruta_particion, fichero)
            elif formato == 'wdf':
                comando = '%s -qP ADD -p %s "%s"' % (config.WWT, ruta_particion, fichero)
            else:
                comando = None

            if comando is not None:
                
                print "-----------------------------"
                print comando
                print "-----------------------------"
                
                salida = util.call_out_file(comando)
                return salida

            else:
                return False
        else:
            return False

    def existeExtraido(self, juego, destino, formato = 'iso'):
        if formato == 'iso':
            fichero = "%s.iso" % juego.title
            fichero = fichero.replace(" ","_")
            fichero = fichero.replace("/","_")
            fichero = fichero.replace(":","_")
            destino = os.path.join(destino , fichero)
            return os.path.exists(destino)

        elif formato == 'wbfs':
            fichero = "%s.wbfs" % (juego.idgame)
            destino = os.path.join(destino , fichero)
            return os.path.exists(destino)
            
        elif formato == 'wdf':
            fichero = "%s [%s].wdf" % (juego.title, juego.idgame)
            destino = os.path.join(destino , fichero)
            return os.path.exists(destino)
            
        else:
            return False

    # extrae el juego a un destino
    def extraerJuego(self ,juego , destino, formato = 'iso'):

        if formato == 'iso':
            comando = "%s -p %s extract %s" % (config.WBFS_APP, juego.particion.device , juego.idgame)
        elif formato == 'wbfs':
            comando = '%s %s extract_wbfs %s .' % (config.WBFS_FILE, juego.particion.device , juego.idgame)
        elif formato == 'wdf':
            comando = "%s EXTRACT -qP -p %s -oW %s" % (config.WWT, juego.particion.device , juego.idgame)
        else:
            comando = None
        
        if comando is not None:
            
            if destino != '':
                trabajoActual = os.getcwd()
                os.chdir( destino )

            salida = util.call_out_file(comando)

            if destino != '':
                os.chdir( trabajoActual )

            return salida

        else:
            return False
        
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

    def convertir(self, formato_origen, formato_destino, origen, salida):
        
        if formato_destino == 'iso':
            if formato_origen == 'wbfs':
                comando = '%s "%s" convert "%s"' % (config.WBFS_FILE, origen, salida)
            elif formato_origen == 'wdf':
                comando = '%s -oP "%s" -d "%s"' % (config.WDF_TO_ISO, origen, os.path.join(salida, '%s.iso' % util.getNombreFichero(os.path.basename(origen))))
            else:
                comando = None
        elif formato_destino == 'wbfs':
            if formato_origen == 'iso':
                comando = '%s "%s" convert "%s"' % (config.WBFS_FILE, origen, salida)
            else:
                comando = None
        elif formato_destino == 'wdf':
            if formato_origen == 'iso':
                comando = '%s -oP "%s" -d "%s"' % (config.ISO_TO_WDF, origen, os.path.join(salida, '%s.wdf' % util.getNombreFichero(os.path.basename(origen))))
            else:
                comando = None
        else:
            comando = None

        if comando is not None:
            ok = util.call_out_file(comando)
        else:
            ok = False
        
        return ok    
