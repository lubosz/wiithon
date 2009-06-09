#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import config
import util
from pool import Pool
import threading , subprocess
from threading import Thread
from threading import Semaphore
from mensaje import Mensaje

'''
Herencia Multiple, Es un Pool (implementado en pool.py) y un Thread

Para poner un trabajo llamamos al metodo nuevoTrabajo( x )
    Su unico parametro es un objeto de tipo Trabajo
'''
class PoolTrabajo(Pool , Thread):
    def __init__(self , core , numHilos = 1):
        Pool.__init__(self , numHilos)
        Thread.__init__(self)
        self.core = core
        self.numHilos = numHilos

    def nuevoTrabajo( self , trabajo ):
        self.nuevoElemento( trabajo )

    def ejecutar(self , numHilo , trabajo , core):

        # FIXME: el device debe sacarlo del objeto juego
        DEVICE = self.core.getDeviceSeleccionado()

        if (trabajo.getQueHacer() == "ANADIR"):
            fichero = trabajo.getAQuien()
            self.anadir(core , fichero , DEVICE)
        elif( trabajo.getQueHacer() == "EXTRAER" ):
            IDGAME = trabajo.getAQuien()
            self.extraer(core , IDGAME , DEVICE)
        elif( trabajo.getQueHacer() == "DESCARGA_CARATULA" ):
            IDGAME = trabajo.getAQuien()
            self.descargarCaratula(core , IDGAME)
        elif( trabajo.getQueHacer() == "DESCARGA_DISCO" ):
            IDGAME = trabajo.getAQuien()
            self.descargarDisco(core , IDGAME)
        elif( trabajo.getQueHacer() == "COPIAR_CARATULA" ):
            IDGAME = trabajo.getAQuien()
            self.copiarCaratula(core , IDGAME)
        elif( trabajo.getQueHacer() == "COPIAR_DISCO" ):
            IDGAME = trabajo.getAQuien()
            self.copiarDisco(core , IDGAME)
        elif( trabajo.getQueHacer() == "VERIFICAR_JUEGO" ):
            IDGAME = trabajo.getAQuien()
            self.verificarJuego(core , DEVICE , IDGAME)

    def descargarCaratula(self , core , IDGAME):
        core.descargarCaratula( IDGAME , "3d")

    def descargarDisco(self , core , IDGAME):
        core.descargarDisco( IDGAME )

    def copiarCaratula(self , core , IDGAME):
        core.copiarCaratula( IDGAME )

    def copiarDisco(self , core , IDGAME):
        core.copiarDisco( IDGAME )

    def verificarJuego(self , core , DEVICE , IDGAME):
        if not core.verificarJuego(DEVICE , IDGAME):
            print _("%s es un juego corrupto" % (IDGAME))
        else:
            print _("No se ha detectado corrupcion en %s" % (IDGAME))

    def anadir(self , core , fichero , DEVICE):
        core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )

        if( not os.path.exists(DEVICE) or not os.path.exists(fichero) ):
            core.nuevoMensaje( Mensaje("ERROR",_("La ISO o la partición no existe")) )
        elif( util.getExtension(fichero) == "rar" ):
            nombreRAR = fichero
            nombreISO = core.getNombreISOenRAR(nombreRAR)
            if (nombreISO != ""):
                if( not os.path.exists(nombreISO) ):
                    if ( core.descomprimirRARconISODentro(nombreRAR) ):
                        self.nuevoTrabajoAnadir( nombreISO )
                    else:
                        core.nuevoMensaje( Mensaje("ERROR",_("Al descomrpimir el RAR : %s") % (nombreRAR)) )
                else:
                    core.nuevoMensaje( Mensaje("ERROR",_("No se puede descomrpimir por que reemplazaría el ISO : %s") % (nombreISO)) )
            else:
                core.nuevoMensaje( Mensaje("ERROR",_("El RAR %s no tenia ninguna ISO") % (nombreRAR)) )
        elif( os.path.isdir( fichero ) ):
            print fichero

            encontrados =  util.rec_glob(fichero, "*.rar")
            if (len(encontrados) == 0):
                core.nuevoMensaje( Mensaje("INFO",_("No se ha encontrado ningun RAR con ISOS dentro")))
            else:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado )

            encontrados =  util.rec_glob(fichero, "*.iso")
            if (len(encontrados) == 0):
                core.nuevoMensaje( Mensaje("INFO",_("No se ha encontrado ningun ISO")))
            else:
                for encontrado in encontrados:
                    self.nuevoTrabajoAnadir( encontrado )

        elif( util.getExtension(fichero) == "iso" ):
            core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_0") )
            core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA_CALCULO") )
            if ( core.anadirISO(DEVICE , fichero ) ):
                core.nuevoMensaje( Mensaje("INFO",_("ISO %s anadida correctamente") % (fichero)) )
                core.nuevoMensaje( Mensaje("COMANDO","REFRESCAR_JUEGOS") )
            else:
                core.nuevoMensaje( Mensaje("ERROR",_("Anadiendo la ISO : %s (comprueba que sea una ISO de WII)") % (fichero)) )

            core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN_CALCULO") )
            core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_100") )
        else:
            core.nuevoMensaje( Mensaje("ERROR",_("%s no es un ningun juego de Wii") % (os.path.basename(fichero)) ) )

        # borrar fichero auxiliar
        try:
            os.remove ( config.HOME_WIITHON_LOGS_PROCESO )
        except OSError:
            pass

        core.nuevoMensaje( Mensaje("COMANDO","TERMINA") )

        # Esperar que todos los mensajes sean atendidos
        core.getMensajes().join()

    def extraer(self , core , IDGAME , DEVICE):
        core.nuevoMensaje( Mensaje("COMANDO","EMPIEZA") )

        core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_0") )
        core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_INICIA_CALCULO") )
        if ( core.extraerJuego(DEVICE , IDGAME ) ):
            core.nuevoMensaje( Mensaje("INFO",_("ISO de %s extraida correctamente") % (IDGAME)) )
        else:
            core.nuevoMensaje( Mensaje("ERROR",_("Extrayendo la ISO : %s") % (IDGAME)) )
        core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_FIN_CALCULO") )
        core.nuevoMensaje( Mensaje("COMANDO","PROGRESO_100") )

        # borrar fichero auxiliar
        try:
            os.remove ( config.HOME_WIITHON_LOGS_PROCESO )
        except OSError:
            pass

        core.nuevoMensaje( Mensaje("COMANDO","TERMINA") )

        # Esperar que todos los mensajes sean atendidos
        core.getMensajes().join()

    def run(self):
        self.empezar( args=(self.core,) )

    '''
    Encola un o varios trabajos para añadir
    Primer parametro: una ruta o una lista de rutas
    '''
    def nuevoTrabajoAnadir(self , fichero):
        if type(fichero) == list:
            for f in fichero:
                self.nuevoTrabajo( Trabajo("ANADIR" , f) )
        else:
            self.nuevoTrabajo( Trabajo("ANADIR" , fichero) )

    '''
    Encola uno o varios trabajos para extraer
    Primer parametro: un IDGAME o una lista de IDGAMEs
    '''
    def nuevoTrabajoExtraer(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("EXTRAER" , i) )
        else:
            self.nuevoTrabajo( Trabajo("EXTRAER" , IDGAME) )

    def nuevoTrabajoDescargaCaratula(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("DESCARGA_CARATULA" , i) )
        else:
            self.nuevoTrabajo( Trabajo("DESCARGA_CARATULA" , IDGAME) )

    def nuevoTrabajoDescargaDisco(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("DESCARGA_DISCO" , i) )
        else:
            self.nuevoTrabajo( Trabajo("DESCARGA_DISCO" , IDGAME) )

    def nuevoTrabajoCopiarCaratula(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("COPIAR_CARATULA" , i) )
        else:
            self.nuevoTrabajo( Trabajo("COPIAR_CARATULA" , IDGAME) )

    def nuevoTrabajoCopiarDisco(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("COPIAR_DISCO" , i) )
        else:
            self.nuevoTrabajo( Trabajo("COPIAR_DISCO" , IDGAME) )

    def nuevoTrabajoVerificarJuego(self , IDGAME):
        if type(IDGAME) == list:
            for i in IDGAME:
                self.nuevoTrabajo( Trabajo("VERIFICAR_JUEGO" , i) )
        else:
            self.nuevoTrabajo( Trabajo("VERIFICAR_JUEGO" , IDGAME) )

'''
Primer parametro = ("ANADIR"|"EXTRAER"|"DESCARGA_CARATULA"|"DESCARGA_DISCO"|"COPIAR_CARATULA"|"COPIAR_DISCO"|"VERIFICAR_JUEGO")
Segundo parametro = Objeto sobre el que se trabaja, depende del primer parametro
            Si el primer parametro es:
                ANADIR: Se espera que el segundo sea 1 ruta o una lista de rutas

                EXTRAER: Se espera que el segundo sea un IDGAME o una lista de IDGAMEs

********************************************************************************************************
Sin implementar: un tercer parametro con el callback de acabar el trabajo
********************************************************************************************************

FIXME: hacerlo con enumerados (o el equivalente python)
POSIBLE SOLUCION:

    (ANADIR,EXTRAER)=([ "%d" % i for i in range(2) ])
'''
class Trabajo:
    def __init__(self, queHacer , aQuien):
        self.queHacer = queHacer
        self.aQuien = aQuien

    def getQueHacer(self):
        return self.queHacer

    def getAQuien(self):
        return self.aQuien

