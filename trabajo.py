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
from util import ErrorDescargando, SesionWiiTDB

# trabajos en pseudo-enumerado
(ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,
DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO,
RECORRER_DIRECTORIO,DESCOMPRIMIR_RAR,
ACTUALIZAR_WIITDB,EDITAR_JUEGO_WIITDB,
VER_URL,CONVERSION_ISO_WBFS, CONVERSION_ISO_WDF,
CONVERSION_WBFS_ISO,CONVERSION_WDF_ISO)=([ "%d" % i for i in range(16) ])

# prioridades
(ALTA,BAJA)=([ "%d" % i for i in range(2) ])

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
                                        callback_termina_importar,
                                        callback_empieza_progreso_indefinido,
                                        callback_termina_progreso_indefinido
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
        self.callback_empieza_progreso_indefinido = callback_empieza_progreso_indefinido
        self.callback_termina_progreso_indefinido = callback_termina_progreso_indefinido
        
        self.actualizarPreferencias()
        
        # sesion http con wiitdb
        self.sesion_wiitdb = SesionWiiTDB()
        
        # pool ayudante
        self.poolBash = None

    def actualizarPreferencias(self):
        self.PROVIDER_COVERS = self.core.prefs.PROVIDER_COVERS
        self.WIDTH_COVERS = self.core.prefs.WIDTH_COVERS
        self.HEIGHT_COVERS = self.core.prefs.HEIGHT_COVERS
        self.ruta_extraer_rar = self.core.prefs.ruta_extraer_rar
        self.PROVIDER_DISCS = self.core.prefs.PROVIDER_DISCS
        self.WIDTH_DISCS = self.core.prefs.WIDTH_DISCS
        self.HEIGHT_DISCS = self.core.prefs.HEIGHT_DISCS
        self.rar_overwrite_iso = self.core.prefs.rar_overwrite_iso
        self.COMANDO_ABRIR_WEB = self.core.prefs.COMANDO_ABRIR_WEB
        self.rar_preguntar_borrar_iso = self.core.prefs.rar_preguntar_borrar_iso
        self.rar_preguntar_borrar_rar = self.core.prefs.rar_preguntar_borrar_rar
        self.USER_WIITDB = self.core.prefs.USER_WIITDB
        self.PASS_WIITDB = self.core.prefs.PASS_WIITDB
        self.URL_ZIP_WIITDB = self.core.prefs.URL_ZIP_WIITDB
        self.tipo_caratula = self.core.prefs.tipo_caratula
        self.tipo_disc_art = self.core.prefs.tipo_disc_art

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
            tipo_caratula = trabajo.destino

            try:
                trabajo.exito = self.descargarCaratula(core , idgame, tipo_caratula)

                if self.callback_termina_trabajo_descargar_caratula:
                    self.callback_termina_trabajo_descargar_caratula(trabajo, idgame)
            except util.YaEstaDescargado:
                pass

        elif( trabajo.tipo == DESCARGA_DISCO ):

            idgame = trabajo.origen
            tipo_disc_art = trabajo.destino

            try:
                trabajo.exito = self.descargarDisco(core , idgame, tipo_disc_art)

                if self.callback_termina_trabajo_descargar_disco:
                    self.callback_termina_trabajo_descargar_disco(trabajo, idgame)
            except util.YaEstaDescargado:
                pass

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
            trabajo.exito = self.recorrerDirectorioYAnadir(core, trabajo, directorio, particion)

        elif( trabajo.tipo == DESCOMPRIMIR_RAR ):
            archivoRAR = trabajo.origen
            particion = trabajo.destino
            trabajo.exito = self.descomprimirRARYAnadir(core , trabajo , archivoRAR, particion)

        elif( trabajo.tipo == ACTUALIZAR_WIITDB ):
            url = trabajo.origen
            trabajo.exito = self.actualizarWiiTDB(url)
            
        elif( trabajo.tipo == EDITAR_JUEGO_WIITDB):
            IDGAME = trabajo.origen.idgame
            trabajo.exito = self.editarJuegoWiiTDB(trabajo, IDGAME)

        elif( trabajo.tipo == VER_URL ):
            url = trabajo.origen
            trabajo.exito = self.abrirPagina(url)
            
        elif( trabajo.tipo == CONVERSION_ISO_WBFS ):
            origen = trabajo.origen
            directorio_salida = trabajo.destino
            trabajo.exito = self.convertir_ISO_WBFS(core, trabajo, origen, directorio_salida)
            
        elif( trabajo.tipo == CONVERSION_ISO_WDF ):
            origen = trabajo.origen
            directorio_salida = trabajo.destino
            trabajo.exito = self.convertir_ISO_WDF(core, trabajo, origen, directorio_salida)
            
        elif( trabajo.tipo == CONVERSION_WBFS_ISO ):
            origen = trabajo.origen
            directorio_salida = trabajo.destino
            trabajo.exito = self.convertir_WBFS_ISO(core, trabajo, origen, directorio_salida)
            
        elif( trabajo.tipo == CONVERSION_WDF_ISO ):
            origen = trabajo.origen
            directorio_salida = trabajo.destino
            trabajo.exito = self.convertir_WDF_ISO(core, trabajo, origen, directorio_salida)

        trabajo.terminado = True

        # termina un trabajo genérico
        if self.callback_termina_trabajo:
            self.callback_termina_trabajo(trabajo)
            
    ############ METODOS PRIVADOS QUE REALIZAN EL TRABAJO #############################

    def anadir(self , core ,trabajo , fichero , DEVICE):
        exito = False

        formato = core.getAutodetectarFormato(fichero)
        idgame = util.getMagicISO(fichero, formato)

        if (  not os.path.exists(DEVICE)):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device
            
        elif( not os.path.exists(fichero) ):
            trabajo.error = _("El archivo ISO %s: No existe") % fichero
            
        elif formato == "iso" and idgame is None:
            trabajo.error = _("El archivo ISO %s: No es un juego de Wii") % fichero

        elif( formato is not None ):
            
            ########### TAREA AUXILIAR ######################
            
            if  self.poolBash is not None and idgame is not None:

                # vamos descargando info wiitdb
                self.poolBash.nuevoTrabajoActualizarWiiTDB('%s?ID=%s' % (self.URL_ZIP_WIITDB, idgame))

                # vamos descargando caratulas
                if not core.existeCaratula(idgame, False, self.tipo_caratula):
                    self.poolBash.nuevoTrabajoDescargaCaratula( idgame , self.tipo_caratula)

                if not core.existeDisco(idgame, False, self.tipo_disc_art):
                    self.poolBash.nuevoTrabajoDescargaDisco( idgame , self.tipo_disc_art)

            #################################################

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
        
        exito = core.extraerJuego(juego, destino, trabajo.trabajoDesc.formato_extraer)

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)
            
        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)
        
        return exito

    def clonar(self, core , trabajo , juego , particion):

        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.clonarJuego(juego , particion)

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    def descargarCaratula(self , core , idgame, tipo_caratula):
        return core.descargarCaratula(idgame, self.PROVIDER_COVERS, self.WIDTH_COVERS, self.HEIGHT_COVERS, tipo_caratula)

    def descargarDisco(self , core , idgame, tipo_disc_art):
        return core.descargarDisco(idgame, self.PROVIDER_DISCS, self.WIDTH_DISCS, self.HEIGHT_DISCS, tipo_disc_art)

    def copiarCaratula(self , core , juego, destino):
        return core.copiarCaratula(juego, destino, self.tipo_caratula)

    def copiarDisco(self , core , juego, destino):
        return core.copiarDisco(juego, destino, self.tipo_disc_art)
        
    def recorrerDirectorioYAnadir(self, core, trabajo, directorio, particion):

        exito = False

        if( not os.path.exists(particion.device) ):
            trabajo.error = _("La particion %s: Ya no existe") % particion.device

        elif (not os.path.exists(directorio)):
            trabajo.error = _("El directorio %s: No existe") % directorio

        elif( os.path.isdir( directorio ) ):

            listaISO = NonRepeatList()
            listaRAR = NonRepeatList()
            
            encontradosRAR =  util.rec_glob(fichero, "[wii]*.rar")
            hayRAR = len(encontradosRAR) > 0
            if hayRAR:
                listaRAR.extend(encontradosRAR)

            encontradosISO =  util.rec_glob(fichero, "*.iso")
            hayISO = len(encontradosISO) > 0
            if hayISO:
                listaISO.extend(encontradosISO)
                
            encontradosWBFS =  util.rec_glob(fichero, "*.wbfs")
            hayWBFS = len(encontradosWBFS) > 0
            if hayWBFS:
                listaISO.extend(encontradosWBFS)
                
            encontradosWDF =  util.rec_glob(fichero, "*.wdf")
            hayWDF = len(encontradosWDF) > 0
            if hayWDF:
                listaISO.extend(encontradosWDF)

            ########## eliminar rar que tienen iso con el mismo nombre #######
            for ficheroRAR in listaRAR:
                nombre = util.getNombreFichero(ficheroRAR)
                i = 0
                encontrado = False
                while not encontrado and i<len(listaISO):
                    encontrado = listaISO[i].lower() == ("%s.iso" % nombre).lower()
                    if not encontrado:
                        i += 1
                if encontrado:
                    listaRAR.remove(ficheroRAR)
            ##################################################################

            if hayISO:
                for encontrado in listaISO:
                    trabajoAnadir = self.nuevoTrabajoAnadir( encontrado , particion.device)
                    trabajoAnadir.padre = trabajo
                    
            if hayRAR:
                for encontrado in listaRAR:
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

        if self.ruta_extraer_rar == ".":
            destino = os.path.dirname(archivoRAR)
        else:
            destino = self.ruta_extraer_rar

        nombreISO = core.getNombreISOenRAR(archivoRAR)        
        rutaISO = os.path.join(destino, nombreISO)

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
            
        if not util.space_for_dvd_iso_wii(destino):
            trabajo.error = _("No hay 4.4GB libres para descomprimir el fichero RAR: %s en la ruta %s. Puede cambiar la ruta en preferencias.") % (archivoRAR, destino)
            error = True
        
        if not error:

            if self.callback_empieza_progreso:
                self.callback_empieza_progreso(trabajo)
                
            if ( core.unpack(archivoRAR, destino, nombreISO, self.rar_overwrite_iso) ):
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

    def editarJuegoWiiTDB(self, trabajo, IDGAME):
        exito = False
        if self.USER_WIITDB != "" and self.PASS_WIITDB != "":
            try:
                self.sesion_wiitdb.connect_if_need_it(self.USER_WIITDB, self.PASS_WIITDB)
                url = self.sesion_wiitdb.get_url_editar_juego(IDGAME)
                if url is not None:
                    exito = self.abrirPagina(url)
            except:
                trabajo.error = _("Error: Al intentar identificarse en WiiTDB para editar el juego.")
        else:
            trabajo.error = _("Escriba su login y password en las preferencias. Si no dispone de uno, registrese en %s") % (config.URL_WIITDB)
        return exito

    def abrirPagina(self, url):
        util.call_out_null('%s "%s"' % (self.COMANDO_ABRIR_WEB, url))
        return True

    def convertir_ISO_WBFS(self, core, trabajo, origen, directorio_salida):
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.convertir('iso','wbfs',origen, directorio_salida)
        if not exito:
            trabajo.error = _('Error en la conversion de %s a WBFS') % origen

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    def convertir_ISO_WDF(self, core, trabajo, origen, directorio_salida):
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.convertir('iso','wdf',origen, directorio_salida)
        if not exito:
            trabajo.error = _('Error en la conversion de %s a WDF') % origen

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    def convertir_WBFS_ISO(self, core, trabajo, origen, directorio_salida):
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.convertir('wbfs','iso',origen, directorio_salida)
        if not exito:
            trabajo.error = _('Error en la conversion de %s a ISO') % origen

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    def convertir_WDF_ISO(self, core, trabajo, origen, directorio_salida):
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)

        exito = core.convertir('wdf','iso',origen, directorio_salida)
        if not exito:
            trabajo.error = _('Error en la conversion de %s a ISO') % origen

        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)

        return exito

    ######################### INTERFAZ PUBLICO #######################################

    def nuevoTrabajo( self , tipo , origenes , destino=None, trabajoDesc=None ):
        if isinstance(origenes, list):
            trabajos = []
            for origen in origenes:
                trabajo = Trabajo(tipo , origen, destino, trabajoDesc)
                self.nuevoElemento(trabajo)
                trabajos.append(trabajo)

            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajos)
            
            return trabajos

        else:
            trabajo = Trabajo(tipo , origenes, destino, trabajoDesc)
            self.nuevoElemento(trabajo)

            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajo)
                
            return trabajo

    def nuevoTrabajoAnadir(self , ficheros , DEVICE):
        return self.nuevoTrabajo( ANADIR , ficheros , DEVICE )

    def nuevoTrabajoExtraer(self ,juegos ,destino, trabajoDesc):
        return self.nuevoTrabajo( EXTRAER , juegos, destino, trabajoDesc )

    def nuevoTrabajoClonar(self , juegos, DEVICE):
        return self.nuevoTrabajo( CLONAR , juegos, DEVICE )

    def nuevoTrabajoDescargaCaratula(self , juegos, tipo_caratula):
        return self.nuevoTrabajo( DESCARGA_CARATULA , juegos , tipo_caratula)

    def nuevoTrabajoDescargaDisco(self , juegos, tipo_disc_art):
        return self.nuevoTrabajo( DESCARGA_DISCO , juegos , tipo_disc_art)

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

    def nuevoTrabajoEditarJuegoWiiTDB(self , juego):
        return self.nuevoTrabajo( EDITAR_JUEGO_WIITDB , juego )

    def nuevoTrabajoVerPagina(self , url):
        return self.nuevoTrabajo( VER_URL , url )

    def nuevoTrabajoConvertir_ISO_WBFS(self , origen, directorio_salida):
        return self.nuevoTrabajo( CONVERSION_ISO_WBFS , origen, directorio_salida )

    def nuevoTrabajoConvertir_ISO_WDF(self , origen, directorio_salida):
        return self.nuevoTrabajo( CONVERSION_ISO_WDF , origen, directorio_salida )

    def nuevoTrabajoConvertir_WBFS_ISO(self , origen, directorio_salida):
        return self.nuevoTrabajo( CONVERSION_WBFS_ISO , origen, directorio_salida )

    def nuevoTrabajoConvertir_WDF_ISO(self , origen, directorio_salida):
        return self.nuevoTrabajo( CONVERSION_WDF_ISO , origen, directorio_salida )

class TrabajoDesc:
    def __init__(self):
        self.formato_extraer = ''
    
'''
tipo:
    tipo de Trabajo
    (ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO,
    RECORRER_DIRECTORIO,DESCOMPRIMIR_RAR,ACTUALIZAR_WIITDB,EDITAR_JUEGO_WIITDB,VER_URL)
origen y destino:
    Casi todos los trabajos, son de gestión, es decir transacciones que tienen 
    un origen y un destino, en general.
terminado:
    Trabajo hecho o no
prioridad:
    ALTA: Se cuela de todos excepto (trabajo activos o trabajos con proridad alta)
    BAJA: Se proceso por orden de cola
exito:
    Exito al finalizar o no
padre:
    Trabajo que le ha generado, None para trabajos raices.
error:
    En caso fallido, mensaje de error
'''
class Trabajo:
    def __init__(self, tipo , origen , destino=None, trabajoDesc=None):
        self.tipo = tipo
        self.origen = origen
        self.destino = destino
        self.terminado = False
        self.prioridad = BAJA
        self.exito = False
        self.padre = None
        self.avisar = (tipo is not DESCARGA_CARATULA) and (tipo is not DESCARGA_DISCO) and (tipo is not ACTUALIZAR_WIITDB)
        self.trabajoDesc = trabajoDesc
        # siempre se define el ultimo, porque usa repr()
        self.error = "%s\n\n%s" % (_("Error al finalizar la siguiente tarea:") ,self.__repr__())
 
    def __repr__(self):
        if self.tipo == ANADIR:
            return _("Anadir %s a la particion %s") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == EXTRAER and isinstance(self.origen, Juego):
            if (self.trabajoDesc and self.trabajoDesc.formato_extraer == 'wbfs'):
                return _("Extraer %s a la ruta %s como WBFS") % (self.origen.title, self.destino)
            elif (self.trabajoDesc and self.trabajoDesc.formato_extraer == 'wdf'):
                return _("Extraer %s a la ruta %s como WDF") % (self.origen.title, self.destino)
            else: # self.trabajoDesc.formato_extraer == 'iso':
                return _("Extraer %s a la ruta %s como ISO") % (self.origen.title, self.destino)
        elif self.tipo == CLONAR and isinstance(self.origen, Juego):
            return _("Copiando el juego %s desde %s a la particion %s") % (self.origen.title, self.origen.particion , self.destino)
        elif self.tipo == DESCARGA_CARATULA:
            return _("Descargando caratula de %s") % (self.origen)
        elif self.tipo == DESCARGA_DISCO:
            return _("Descargando disco de %s") % (self.origen)
        elif self.tipo == COPIAR_CARATULA and isinstance(self.origen, Juego):
            return _("Copiando la caratula %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == COPIAR_DISCO and isinstance(self.origen, Juego):
            return _("Copiando el disco %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == RECORRER_DIRECTORIO:
            return _("Recorrer directorio %s") % (os.path.basename(self.origen))
        elif self.tipo == DESCOMPRIMIR_RAR:
            return _("Descomprimir RAR %s") % (os.path.basename(self.origen))
        elif self.tipo == ACTUALIZAR_WIITDB:
            return _("Actualizar WiiTDB desde %s ...") % (self.origen[:35])
        elif self.tipo == EDITAR_JUEGO_WIITDB:
            return _("Editar Juego WiiTDB: %s") % (self.origen)
        elif self.tipo == VER_URL:
            return _("Abrir pagina: %s") % (self.origen)
        elif self.tipo == CONVERSION_ISO_WBFS:
            return _("Convirtiendo ISO -> WBFS: (%s -> %s)") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == CONVERSION_ISO_WDF:
            return _("Convirtiendo ISO -> WDF: (%s -> %s)") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == CONVERSION_WBFS_ISO:
            return _("Convirtiendo WBFS -> ISO: (%s -> %s)") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == CONVERSION_WDF_ISO:
            return _("Convirtiendo WDF -> ISO: (%s -> %s)") % (os.path.basename(self.origen), self.destino)
        else:
            return _("Trabajo desconocido")
