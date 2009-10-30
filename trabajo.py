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
        
        self.actualizarPreferencias()


    def actualizarPreferencias(self):
        self.PROVIDER_COVERS = self.core.prefs.PROVIDER_COVERS
        self.WIDTH_COVERS = self.core.prefs.WIDTH_COVERS
        self.HEIGHT_COVERS = self.core.prefs.HEIGHT_COVERS
        self.ruta_extraer_rar = self.core.prefs.ruta_extraer_rar
        self.WIDTH_DISCS = self.core.prefs.WIDTH_DISCS
        self.HEIGHT_DISCS = self.core.prefs.HEIGHT_DISCS
        self.rar_overwrite_iso = self.core.prefs.rar_overwrite_iso
        self.rar_preguntar_borrar_iso = self.core.prefs.rar_preguntar_borrar_iso
        self.rar_preguntar_borrar_rar = self.core.prefs.rar_preguntar_borrar_rar

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
                self.callback_termina_trabajo_anadir(core, trabajo, fichero, DEVICE, self.rar_preguntar_borrar_iso, self.rar_preguntar_borrar_rar)

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
                self.callback_termina_trabajo_descargar_caratula(trabajo, idgame)

        elif( trabajo.tipo == DESCARGA_DISCO ):
            idgame = trabajo.origen
            trabajo.exito = self.descargarDisco(core , idgame)

            if self.callback_termina_trabajo_descargar_disco:
                self.callback_termina_trabajo_descargar_disco(trabajo, idgame)

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
            trabajo.exito = self.recorrerDirectorioYAnadir(core , trabajo, directorio, particion)

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
        return core.descargarCaratula(idgame, self.PROVIDER_COVERS, self.WIDTH_COVERS, self.HEIGHT_COVERS)

    def descargarDisco(self , core , idgame):
        return core.descargarDisco(idgame, self.WIDTH_DISCS, self.HEIGHT_DISCS)

    def copiarCaratula(self , core , juego, destino):
        return core.copiarCaratula(juego, destino)

    def copiarDisco(self , core , juego, destino):
        return core.copiarDisco(juego, destino)
        
    def recorrerDirectorioYAnadir(self, core, trabajo, directorio, particion):

        exito = False

        if( not os.path.exists(particion.device) ):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device

        elif (not os.path.exists(directorio)):
            trabajo.error = _("El directorio %s: No existe") % directorio

        elif( os.path.isdir( directorio ) ):

            encontradosRAR =  util.rec_glob(directorio, "*.rar")
            hayRAR = len(encontradosRAR) > 0

            encontradosISO =  util.rec_glob(directorio, "*.iso")
            hayISO = len(encontradosISO) > 0

            ########## eliminar rar que tienen iso con el mismo nombre #######
            for ficheroRAR in encontradosRAR:
                nombre = util.getNombreFichero(ficheroRAR)
                i = 0
                encontrado = False
                while not encontrado and i<len(encontradosISO):
                    encontrado = encontradosISO[i].lower() == ("%s.iso" % nombre).lower()
                    if not encontrado:
                        i += 1
                if encontrado:
                    print "eliminar %s" % ficheroRAR
                    encontradosRAR.remove(ficheroRAR)
            ##################################################################

            if hayISO:
                for encontrado in encontradosISO:
                    trabajoAnadir = self.nuevoTrabajoAnadir( encontrado , particion.device)
                    trabajoAnadir.padre = trabajo
                    
            if hayRAR:
                for encontrado in encontradosRAR:
                    trabajoDescomprimirRAR = self.nuevoTrabajoDescomprimirRAR( encontrado , particion)
                    trabajoDescomprimirRAR.padre = trabajo

            if hayRAR or hayISO:
                exito = True
            else:
                trabajo.error = _("No se ha encontrado ningun ISO/RAR en el directorio %s") % directorio

        else:
            trabajo.error = _("%s no es un directorio") % directorio

        return exito

    def descomprimirRARYAnadir(self , core , trabajo , archivoRAR, particion):
        # presuponemos que hay error y no hay exito
        exito = False
        error = True

        nombreISO = core.getNombreISOenRAR(archivoRAR)        
        rutaISO = os.path.join(self.ruta_extraer_rar, nombreISO)

        if( not os.path.exists(particion.device) ):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device
            
        elif (not os.path.exists(archivoRAR)):
            trabajo.error = _("El archivo RAR %s: No existe") % archivoRAR

        elif os.path.exists(rutaISO):
            if not self.rar_overwrite_iso:
                trabajo.error = _("Error al descomprimrir. Ya existe %s. Si desea sobreescribirlo, modifique la opcion en preferencias.") % rutaISO
            else:
                if os.path.exists(rutaISO):
                    os.remove(rutaISO)
                    error = False

        elif( util.getExtension(archivoRAR) != "rar" ):
            trabajo.error = _("%s no es un archivo RAR") % archivoRAR

        elif nombreISO is None:
            trabajo.error = _("Error: El archivo RAR %s no contiene ninguna ISO") % (archivoRAR)

        else:
            error = False
            
        if not util.space_for_dvd_iso_wii(self.ruta_extraer_rar):
            trabajo.error = _("No hay 4.4GB libres para descomprimir el fichero RAR: %s en la ruta %s. Puede cambiar la ruta en preferencias.") % (archivoRAR, self.ruta_extraer_rar)
            error = True
        
        if not error:

            if self.callback_empieza_progreso:
                self.callback_empieza_progreso(trabajo)

            if ( core.unpack(archivoRAR, self.ruta_extraer_rar, nombreISO, self.rar_overwrite_iso) ):
                exito = True
                
                trabajoAnadir = self.nuevoTrabajoAnadir( rutaISO , particion.device)
                trabajoAnadir.padre = trabajo
            else:
                trabajo.error = _("Error al descomrpimir el RAR : %s") % (archivoRAR)
                
            if self.callback_termina_progreso:
                self.callback_termina_progreso(trabajo)

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

            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajos)
            
            return trabajos

        else:
            trabajo = Trabajo(tipo , origenes, destino)
            self.nuevoElemento(trabajo)

            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajo)
                
            return trabajo

    def nuevoTrabajoAnadir(self , ficheros , DEVICE):
        return self.nuevoTrabajo( ANADIR , ficheros , DEVICE )

    def nuevoTrabajoExtraer(self ,juegos ,destino):
        return self.nuevoTrabajo( EXTRAER , juegos, destino )

    def nuevoTrabajoClonar(self , juegos, DEVICE):
        return self.nuevoTrabajo( CLONAR , juegos, DEVICE )

    def nuevoTrabajoDescargaCaratula(self , juegos):
        return self.nuevoTrabajo( DESCARGA_CARATULA , juegos )

    def nuevoTrabajoDescargaDisco(self , juegos):
        return self.nuevoTrabajo( DESCARGA_DISCO , juegos )

    def nuevoTrabajoCopiarCaratula(self , juegos, destino):
        return self.nuevoTrabajo( COPIAR_CARATULA , juegos, destino )

    def nuevoTrabajoCopiarDisco(self , juegos, destino):
        return self.nuevoTrabajo( COPIAR_DISCO , juegos, destino )
        
    def nuevoTrabajoRecorrerDirectorio(self , directorio, particion):
        return self.nuevoTrabajo( RECORRER_DIRECTORIO , directorio, particion )

    def nuevoTrabajoDescomprimirRAR(self , archivoRAR, particion):
        return self.nuevoTrabajo( DESCOMPRIMIR_RAR , archivoRAR, particion )

    def nuevoTrabajoActualizarWiiTDB(self , url):
        return self.nuevoTrabajo( ACTUALIZAR_WIITDB , url )

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
padre:
    Trabajo que le ha generado, None para trabajos raices.
error:
    En caso fallido, mensaje de error
'''

class Trabajo:
    def __init__(self, tipo , origen , destino=None):
        self.tipo = tipo
        self.origen = origen
        self.destino = destino
        self.terminado = False
        self.exito = False
        self.padre = None
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
