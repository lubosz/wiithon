#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import threading , subprocess
from threading import Thread, Semaphore

import config
import util
from pool import Pool
from wiitdb_schema import Juego
from wiitdb_xml import *
from util import ErrorDescargando

# pseudo-enumerado
(ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,
DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO,
RECORRER_DIRECTORIO,DESCOMPRIMIR_RAR,
ACTUALIZAR_WIITDB)=([ "%d" % i for i in range(10) ])

'''
Herencia Multiple, Es un Pool (implementado en pool.py) y un Thread

Para poner un Trabajo llamamos al metodo nuevoTrabajo( x )
    Su unico parametro es un objeto de tipo trabajo
'''
class PoolTrabajo(Pool , Thread):
    def __init__(
                                        self , core , numHilos , 
                                        callback_empieza_trabajo,
                                        callback_termina_trabajo,
                                        callback_nuevo_trabajo,
                                        callback_empieza_trabajo_anadir,
                                        callback_termina_trabajo_anadir,
                                        callback_empieza_progreso,
                                        callback_termina_progreso,
                                        callback_empieza_trabajo_extraer,
                                        callback_termina_trabajo_extraer,
                                        callback_empieza_trabajo_copiar,
                                        callback_termina_trabajo_copiar,
                                        callback_termina_trabajo_descargar_caratula,
                                        callback_termina_trabajo_descargar_disco,
                                        callback_spinner, 
                                        callback_nuevo_juego,
                                        callback_nuevo_descripcion,
                                        callback_nuevo_genero, 
                                        callback_nuevo_online_feature,
                                        callback_nuevo_accesorio, 
                                        callback_nuevo_companie,
                                        callback_error_importando,
                                        callback_empieza_descarga,
                                        callback_empieza_descomprimir,
                                        callback_empieza_importar,
                                        callback_termina_importar
                                        ):
        Pool.__init__(self , numHilos)
        Thread.__init__(self)
        self.core = core
        self.numHilos = int(numHilos)
        #self.listaTrabajos = []
        self.callback_empieza_trabajo = callback_empieza_trabajo
        self.callback_termina_trabajo = callback_termina_trabajo
        self.callback_nuevo_trabajo = callback_nuevo_trabajo
        self.callback_empieza_trabajo_anadir = callback_empieza_trabajo_anadir
        self.callback_termina_trabajo_anadir = callback_termina_trabajo_anadir
        self.callback_empieza_progreso = callback_empieza_progreso
        self.callback_termina_progreso = callback_termina_progreso
        self.callback_empieza_trabajo_extraer = callback_empieza_trabajo_extraer
        self.callback_termina_trabajo_extraer = callback_termina_trabajo_extraer
        self.callback_empieza_trabajo_copiar = callback_empieza_trabajo_copiar
        self.callback_termina_trabajo_copiar = callback_termina_trabajo_copiar
        self.callback_termina_trabajo_descargar_caratula = callback_termina_trabajo_descargar_caratula
        self.callback_termina_trabajo_descargar_disco = callback_termina_trabajo_descargar_disco
        self.callback_spinner = callback_spinner
        self.callback_nuevo_juego = callback_nuevo_juego
        self.callback_nuevo_descripcion = callback_nuevo_descripcion
        self.callback_nuevo_genero = callback_nuevo_genero
        self.callback_nuevo_online_feature = callback_nuevo_online_feature
        self.callback_nuevo_accesorio = callback_nuevo_accesorio
        self.callback_nuevo_companie = callback_nuevo_companie
        self.callback_error_importando = callback_error_importando
        self.callback_empieza_descarga = callback_empieza_descarga
        self.callback_empieza_descomprimir = callback_empieza_descomprimir
        self.callback_empieza_importar = callback_empieza_importar
        self.callback_termina_importar = callback_termina_importar

    def run(self):
        self.empezar( args=(self.core,) )

    def ejecutar(self , numHilo , trabajo , core):
        
        if self.callback_empieza_trabajo:
            self.callback_empieza_trabajo(trabajo)

        if (trabajo.tipo == ANADIR):

            if self.callback_empieza_trabajo_anadir:
                self.callback_empieza_trabajo_anadir(trabajo)
            
            fichero = trabajo.origen
            DEVICE = trabajo.destino
            trabajo.exito = self.anadir(core ,trabajo , fichero , DEVICE)
            
            if self.callback_termina_trabajo_anadir:
                self.callback_termina_trabajo_anadir(trabajo, fichero, DEVICE)

        elif( trabajo.tipo == EXTRAER):

            if self.callback_empieza_trabajo_extraer:
                self.callback_empieza_trabajo_extraer(trabajo)

            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.extraer(core ,trabajo, juego , destino)

            if self.callback_termina_trabajo_extraer:
                self.callback_termina_trabajo_extraer(trabajo)

        elif( trabajo.tipo == CLONAR ):

            if self.callback_empieza_trabajo_copiar:
                self.callback_empieza_trabajo_copiar(trabajo)

            juego = trabajo.origen
            particion = trabajo.destino
            trabajo.exito = self.clonar(core ,trabajo, juego , particion)

            if self.callback_termina_trabajo_copiar:
                self.callback_termina_trabajo_copiar(trabajo, juego, particion)

        elif( trabajo.tipo == DESCARGA_CARATULA ):
            idgame = trabajo.origen
            trabajo.exito = self.descargarCaratula(core , idgame)

            if self.callback_termina_trabajo_descargar_caratula:
                self.callback_termina_trabajo_descargar_caratula(trabajo, juego)

        elif( trabajo.tipo == DESCARGA_DISCO ):
            idgame = trabajo.origen
            trabajo.exito = self.descargarDisco(core , idgame)

            if self.callback_termina_trabajo_descargar_disco:
                self.callback_termina_trabajo_descargar_disco(trabajo, juego)

        elif( trabajo.tipo == COPIAR_CARATULA ):
            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.copiarCaratula(core , juego, destino)

        elif( trabajo.tipo == COPIAR_DISCO ):
            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.copiarDisco(core , juego , destino)

        elif( trabajo.tipo == RECORRER_DIRECTORIO ):
            directorio = trabajo.origen
            particion = trabajo.destino
            trabajo.exito = self.recorrerDirectorioYAnadir(core , directorio, particion)

        elif( trabajo.tipo == DESCOMPRIMIR_RAR ):
            archivoRAR = trabajo.origen
            particion = trabajo.destino
            trabajo.exito = self.descomprimirRARYAnadir(core , trabajo , archivoRAR, particion)

        elif( trabajo.tipo == ACTUALIZAR_WIITDB ):
            url = trabajo.origen
            trabajo.exito = self.actualizarWiiTDB(url)

        trabajo.terminado = True

        # termina un trabajo genérico
        if self.callback_termina_trabajo:
            self.callback_termina_trabajo(trabajo)

    def anadir(self , core ,trabajo , fichero , DEVICE):
        exito = False

        if (  not os.path.exists(DEVICE)):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device
            
        elif( not os.path.exists(fichero) ):
            trabajo.error = _("El archivo ISO %s: No existe") % fichero

        elif( util.getExtension(fichero) == "iso" ):
            
            if self.callback_empieza_progreso:
                self.callback_empieza_progreso(trabajo)
            
            exito = core.anadirISO(DEVICE , fichero)

            if self.callback_termina_progreso:
                self.callback_termina_progreso(trabajo)
        else:
            trabajo.error = _("%s no es un ningun juego de Wii") % (os.path.basename(fichero))

        return exito

    def extraer(self , core , trabajo , juego , destino):
        
        exito = False
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)
        else:
            print "no hay progreso que empezar"
        
        exito = core.extraerJuego(juego, destino)
        
        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)
        else:
            print "no hay progreso que terminar"
        
        return exito

    def clonar(self, core , trabajo , juego , particion):

        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.clonarJuego(juego , particion)

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    def descargarCaratula(self , core , idgame):
        return core.descargarCaratula(idgame)

    def descargarDisco(self , core , idgame):
        return core.descargarDisco(idgame)

    def copiarCaratula(self , core , juego, destino):
        return core.copiarCaratula(juego, destino)

    def copiarDisco(self , core , juego, destino):
        return core.copiarDisco(juego, destino)
        
    def recorrerDirectorioYAnadir(self , core , directorio, particion):

        exito = False

        if( not os.path.exists(particion.device) ):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device

        elif (not os.path.exists(directorio)):
            trabajo.error = _("El directorio %s: No existe") % directorio

        elif( os.path.isdir( directorio ) ):

            encontrados =  util.rec_glob(directorio, "*.rar")
            hayRAR = len(encontrados) > 0
            if hayRAR:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado , particion.device)

            encontrados =  util.rec_glob(directorio, "*.iso")
            hayISO = len(encontrados) > 0
            if hayISO:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado , particion.device)

            if hayRAR or hayISO:
                exito = True
            else:
                trabajo.error = _("No se ha encontrado ningun ISO/RAR en el directorio %s") % directorio

        else:
            trabajo.error = _("%s no es un directorio") % directorio

        return exito

    def descomprimirRARYAnadir(self , core , trabajo , archivoRAR, particion):
        exito = False
        
        if( not os.path.exists(particion.device) ):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device
            
        elif (not os.path.exists(archivoRAR)):
            trabajo.error = _("El archivo RAR %s: No existe") % archivoRAR
        
        elif( util.getExtension(archivoRAR) == "rar" ):
            carpetaDescomprimido = os.join.abspath(archivoRAR)
            nombreISO = core.getNombreISOenRAR(archivoRAR)
            if (nombreISO != None):
                if( not os.path.exists(nombreISO) ):
                    
                    if self.callback_empieza_progreso:
                        self.callback_empieza_progreso(trabajo)
                    
                    if ( core.unpack(archivoRAR, carpetaDescomprimido, nombreISO) ):
                        exito = True
                        isoExtraida = os.path.join(carpetaDescomprimido, nombreISO)
                        self.nuevoTrabajoAnadir( isoExtraida , particion.device)
                    else:
                        trabajo.error = _("Error al descomrpimir el RAR : %s") % (archivoRAR)
                        
                    if self.callback_termina_progreso:
                        self.callback_termina_progreso(trabajo)
                else:
                    trabajo.error = _("Error: No se puede descomrpimir por que reemplazaria el ISO : %s") % (nombreISO)
            else:
                trabajo.error = _("Error: El archivo RAR %s no contiene ninguna ISO") % (archivoRAR)

        else:
            trabajo.error = _("%s no es un archivo RAR") % archivoRAR
                
        return exito

    # TAREA UNICA EN COLA
    def actualizarWiiTDB(self , url):
        exito = False        
        try:
            xmlWiiTDB = WiiTDBXML(url,'wiitdb.zip','wiitdb.xml',
                                                        self.callback_spinner, 
                                                        self.callback_nuevo_juego,
                                                        self.callback_nuevo_descripcion,
                                                        self.callback_nuevo_genero,
                                                        self.callback_nuevo_online_feature,
                                                        self.callback_nuevo_accesorio,
                                                        self.callback_nuevo_companie,
                                                        self.callback_error_importando,
                                                        self.callback_empieza_descarga,
                                                        self.callback_empieza_descomprimir,
                                                        self.callback_empieza_importar,
                                                        self.callback_termina_importar
                                                        )
            xmlWiiTDB.start()
            xmlWiiTDB.join()
            exito = True

        except ErrorDescargando:
            trabajo.error = _("Error: Al descargar la bdd wiitdb de: %s") % (url)
        except:
            trabajo.error = _("Error: Ocurrio un error al introducir la informacion de juegos de WiiTDB")
        
        return exito

    ######################### INTERFAZ PUBLICO #######################################

    def nuevoTrabajo( self , tipo , origenes , destino=None ):
        if isinstance(origenes, list):
            trabajos = []
            for origen in origenes:
                trabajo = Trabajo(tipo , origen, destino)
                self.nuevoElemento(trabajo)
                trabajos.append(trabajo)
                
            #self.listaTrabajos.extend(trabajos)
            
            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajos)
        else:
            trabajo = Trabajo(tipo , origenes, destino)
            self.nuevoElemento(trabajo)

            #self.listaTrabajos.append(trabajo)
            
            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajo)

    def nuevoTrabajoAnadir(self , ficheros , DEVICE):
        self.nuevoTrabajo( ANADIR , ficheros , DEVICE )

    def nuevoTrabajoExtraer(self ,juegos ,destino):
        self.nuevoTrabajo( EXTRAER , juegos, destino )

    def nuevoTrabajoClonar(self , juegos, DEVICE):
        self.nuevoTrabajo( CLONAR , juegos, DEVICE )

    def nuevoTrabajoDescargaCaratula(self , juegos):
        self.nuevoTrabajo( DESCARGA_CARATULA , juegos )

    def nuevoTrabajoDescargaDisco(self , juegos):
        self.nuevoTrabajo( DESCARGA_DISCO , juegos )

    def nuevoTrabajoCopiarCaratula(self , juegos, destino):
        self.nuevoTrabajo( COPIAR_CARATULA , juegos, destino )

    def nuevoTrabajoCopiarDisco(self , juegos, destino):
        self.nuevoTrabajo( COPIAR_DISCO , juegos, destino )
        
    def nuevoTrabajoRecorrerDirectorio(self , directorio, particion):
        self.nuevoTrabajo( RECORRER_DIRECTORIO , directorio, particion )

    def nuevoTrabajoDescomprimirRAR(self , archivoRAR, particion):
        self.nuevoTrabajo( DESCOMPRIMIR_RAR , archivoRAR, particion )

    def nuevoTrabajoActualizarWiiTDB(self , url):
        self.nuevoTrabajo( ACTUALIZAR_WIITDB , url )

'''
tipo:
    tipo de Trabajo
    (ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO,
    RECORRER_DIRECTORIO,DESCOMPRIMIR_RAR,ACTUALIZAR_WIITDB)
origen y destino:
    Casi todos los trabajos, son de gestión, es decir transacciones que tienen 
    un origen y un destino, en general.
terminado:
    Trabajo hecho o no
exito:
    Exito al finalizar o no
'''

class Trabajo:
    def __init__(self, tipo , origen , destino=None):
        self.tipo = tipo
        self.origen = origen
        self.destino = destino
        self.terminado = False
        self.exito = False
        self.error = _("Error al finalizar la siguiente tarea:\n\n%s") % (self.__repr__())
 
    def __repr__(self):
        if self.tipo == ANADIR:
            return _("Anadir %s a la particion %s") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == EXTRAER and isinstance(self.origen, Juego):
            return _("Extraer %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == CLONAR and isinstance(self.origen, Juego):
            return _("Copiando el juego %s desde %s a la particion %s") % (self.origen.title, self.origen.particion , self.destino)
        elif self.tipo == DESCARGA_CARATULA and isinstance(self.origen, Juego):
            return _("Descargando caratula de %s") % (self.origen.title)
        elif self.tipo == DESCARGA_DISCO and isinstance(self.origen, Juego):
            return _("Descargando disco de %s") % (self.origen.title)
        elif self.tipo == COPIAR_CARATULA and isinstance(self.origen, Juego):
            return _("Copiando la caratula %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == COPIAR_DISCO and isinstance(self.origen, Juego):
            return _("Copiando el disco %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == RECORRER_DIRECTORIO:
            return _("Recorrer directorio %s") % (os.path.basename(self.origen))
        elif self.tipo == DESCOMPRIMIR_RAR:
            return _("Descomprimir RAR %s") % (os.path.basename(self.origen))
        elif self.tipo == ACTUALIZAR_WIITDB:
            return _("Actualizar WiiTDB desde %s") % (self.origen)
