#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import threading , subprocess
from threading import Thread, Semaphore

import config
import util
from pool import Pool
from mensaje import Mensaje
from juego import Juego

# pseudo-enumerado
(ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO)=([ "%d" % i for i in range(7) ])

'''
Herencia Multiple, Es un Pool (implementado en pool.py) y un Thread

Para poner un Trabajo llamamos al metodo nuevoTrabajo( x )
    Su unico parametro es un objeto de tipo trabajo
'''
class PoolTrabajo(Pool , Thread):
    def __init__(self , core , numHilos = 1 , 
                                        callback_empieza_trabajo = None,
                                        callback_termina_trabajo = None,
                                        callback_nuevo_trabajo = None,
                                        callback_empieza_trabajo_anadir = None,
                                        callback_termina_trabajo_anadir = None,
                                        callback_empieza_progreso = None,
                                        callback_termina_progreso = None,
                                        callback_empieza_trabajo_extraer = None,
                                        callback_termina_trabajo_extraer = None,
                                        callback_empieza_trabajo_copiar = None,
                                        callback_termina_trabajo_copiar = None
                                        ):
        Pool.__init__(self , numHilos)
        Thread.__init__(self)
        self.core = core
        self.numHilos = numHilos
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

    def run(self):
        self.empezar( args=(self.core,) )

    def ejecutar(self , numHilo , trabajo , core):
        
        print "<%s>" % trabajo
        
        if self.callback_empieza_trabajo:
            self.callback_empieza_trabajo(trabajo)

        if (trabajo.tipo == ANADIR):

            if self.callback_empieza_trabajo_anadir:
                self.callback_empieza_trabajo_anadir(trabajo)
            
            fichero = trabajo.origen
            DEVICE = trabajo.destino
            trabajo.exito = self.anadir(core ,trabajo , fichero , DEVICE)
            if trabajo.exito:
                idgame = util.getMagicISO(fichero)
            else:
                idgame = None

            if self.callback_termina_trabajo_anadir:
                self.callback_termina_trabajo_anadir(trabajo, idgame)

        elif( trabajo.tipo == EXTRAER):

            if self.callback_empieza_trabajo_extraer:
                self.callback_empieza_trabajo_extraer(trabajo)

            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.extraer(core ,trabajo, juego , destino)

            if self.callback_termina_trabajo_extraer:
                self.callback_termina_trabajo_extraer(trabajo)

        elif( trabajo.tipo == CLONAR ):
            print "aaaa"
            if self.callback_empieza_trabajo_copiar:
                self.callback_empieza_trabajo_copiar(trabajo)
            print "bbbbbbb"
            juego = trabajo.origen
            DEVICE = trabajo.destino
            trabajo.exito = self.clonar(core ,trabajo, juego , DEVICE)
            print "cccccc"
            if self.callback_termina_trabajo_copiar:
                self.callback_termina_trabajo_copiar(trabajo, juego, DEVICE)
            
        elif( trabajo.tipo == DESCARGA_CARATULA ):
            juego = trabajo.origen
            self.descargarCaratula(core , juego)
        elif( trabajo.tipo == DESCARGA_DISCO ):
            juego = trabajo.origen
            trabajo.exito = self.descargarDisco(core , juego)
        elif( trabajo.tipo == COPIAR_CARATULA ):
            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.copiarCaratula(core , juego, destino)
        elif( trabajo.tipo == COPIAR_DISCO ):
            juego = trabajo.origen
            destino = trabajo.destino
            trabajo.exito = self.copiarDisco(core , juego , destino)
        
        trabajo.terminado = True

        # termina un trabajo genérico
        if self.callback_termina_trabajo:
            self.callback_termina_trabajo(trabajo)

        print "</>"

    def anadir(self , core ,trabajo , fichero , DEVICE):
        exito = False

        if( not os.path.exists(DEVICE) or not os.path.exists(fichero) ):
            pass
            #core.nuevoMensaje( Mensaje("ERROR",_("La ISO o la particion no existe")) )
        elif( util.getExtension(fichero) == "rar" ):
            nombreRAR = fichero
            nombreISO = core.getNombreISOenRAR(nombreRAR)
            if (nombreISO != ""):
                if( not os.path.exists(nombreISO) ):
                    if ( core.descomprimirRARconISODentro(nombreRAR) ):
                        exito = True
                        self.nuevoTrabajoAnadir( nombreISO , DEVICE)
                    else:
                        pass
                        #core.nuevoMensaje( Mensaje("ERROR",_("Al descomrpimir el RAR : %s") % (nombreRAR)) )
                else:
                    pass
                    #core.nuevoMensaje( Mensaje("ERROR",_("No se puede descomrpimir por que reemplazaria el ISO : %s") % (nombreISO)) )
            else:
                pass
                #core.nuevoMensaje( Mensaje("ERROR",_("El RAR %s no tenia ninguna ISO") % (nombreRAR)) )
        elif( os.path.isdir( fichero ) ):
            encontrados =  util.rec_glob(fichero, "*.rar")
            if (len(encontrados) == 0):
                pass
                #core.nuevoMensaje( Mensaje("INFO",_("No se ha encontrado ningun RAR con ISOS dentro")))
            else:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado , DEVICE)

            encontrados =  util.rec_glob(fichero, "*.iso")
            if (len(encontrados) == 0):
                pass
                #core.nuevoMensaje( Mensaje("INFO",_("No se ha encontrado ningun ISO")))
            else:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado , DEVICE)
                    
            exito = True

        elif( util.getExtension(fichero) == "iso" ):
            
            if self.callback_empieza_progreso:
                self.callback_empieza_progreso(trabajo)
            
            #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_0") )
            #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA_CALCULO") )
            if ( core.anadirISO(DEVICE , fichero ) ):
                exito = True
                #core.nuevoMensaje( Mensaje("INFO",_("ISO %s anadida correctamente") % (fichero)) )
                #core.nuevoMensaje( Mensaje("COMANDO","REFRESCAR_JUEGOS") )
            else:
                pass
                #core.nuevoMensaje( Mensaje("ERROR",_("Anadiendo la ISO : %s (comprueba que sea una ISO de WII)") % (fichero)) )

            if self.callback_termina_progreso:
                self.callback_termina_progreso(trabajo)

            #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN_CALCULO") )
            #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_100") )
        else:
            #core.nuevoMensaje( Mensaje("ERROR",_("%s no es un ningun juego de Wii") % (os.path.basename(fichero)) ) )
            pass

        #core.nuevoMensaje( Mensaje("COMANDO","TERMINA") )

        # Esperar que todos los mensajes sean atendidos
        #core.getMensajes().join()
        return exito

    def extraer(self , core , trabajo , juego , destino):
        exito = False

        #core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_0") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA_CALCULO") )
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)
        
        if ( core.extraerJuego(juego, destino) ):
            exito = True
            #core.nuevoMensaje( Mensaje("INFO",_("ISO de %s extraida correctamente") % (IDGAME)) )
        else:
            pass
        
        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)
            
            #core.nuevoMensaje( Mensaje("ERROR",_("Extrayendo la ISO : %s") % (IDGAME)) )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN_CALCULO") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_100") )
        #core.nuevoMensaje( Mensaje("COMANDO","TERMINA") )

        # Esperar que todos los mensajes sean atendidos
        #core.getMensajes().join()
        
        return exito


    def clonar(self, core , trabajo , juego , DEVICE):
        exito = False
        
        #core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_0") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA_CALCULO") )
        
        if self.callback_empieza_progreso:
            self.callback_empieza_progreso(trabajo)
        
        if ( core.clonarJuego(juego , DEVICE) ):
            exito = True
            #core.nuevoMensaje( Mensaje("INFO",_("Juego %s ha sido copiado en %s correctamente") % (juego.title , DEVICE_destino)) )
        else:
            pass
            #core.nuevoMensaje( Mensaje("ERROR",_("Copiando el juego %s en %s") % (juego.title , DEVICE_destino)) )
            
        if self.callback_termina_progreso:
            self.callback_termina_progreso(trabajo)
            
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN_CALCULO") )
        #core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_100") )
        #core.nuevoMensaje( Mensaje("COMANDO","TERMINA") )

        # Esperar que todos los mensajes sean atendidos
        #core.getMensajes().join()
        
        return exito

    def descargarCaratula(self , core , juego):
        return core.descargarCaratula( juego.idgame , "3d" )

    def descargarDisco(self , core , juego):
        return core.descargarDisco( juego.idgame )

    def copiarCaratula(self , core , juego, destino):
        return core.copiarCaratula( juego, destino )

    def copiarDisco(self , core , juego, destino):
        return core.copiarDisco( juego, destino )

    def nuevoTrabajo( self , tipo , origenes , destino=None ):
        if isinstance(origenes, list):
            trabajos = []
            for origen in origenes:
                trabajo = Trabajo(tipo , origen, destino)
                self.nuevoElemento(trabajo)
                trabajos.append(trabajo)
            if self.callback_nuevo_trabajo:
                self.callback_nuevo_trabajo(trabajos)
        else:
            trabajo = Trabajo(tipo , origenes, destino)
            self.nuevoElemento(trabajo)
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

'''
tipo:
    tipo de Trabajo
    (ANADIR,EXTRAER,CLONAR,DESCARGA_CARATULA,DESCARGA_DISCO,COPIAR_CARATULA,COPIAR_DISCO)
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
 
    def __repr__(self):
        if self.tipo == ANADIR:
            return _("Anadir %s a la particion %s") % (os.path.basename(self.origen), self.destino)
        elif self.tipo == EXTRAER and isinstance(self.origen, Juego):
            return _("Extraer %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == CLONAR and isinstance(self.origen, Juego):
            return _("Copiando el juego %s a la particion %s") % (self.origen.title, self.destino)
        elif self.tipo == DESCARGA_CARATULA and isinstance(self.origen, Juego):
            return _("Descargando caratula de %s") % (self.origen.title)
        elif self.tipo == DESCARGA_DISCO and isinstance(self.origen, Juego):
            return _("Descargando disco de %s") % (self.origen.title)
        elif self.tipo == COPIAR_CARATULA and isinstance(self.origen, Juego):
            return _("Copiando la caratula %s a la ruta %s") % (self.origen.title, self.destino)
        elif self.tipo == COPIAR_DISCO and isinstance(self.origen, Juego):
            return _("Copiando el disco %s a la ruta %s") % (self.origen.title, self.destino)
