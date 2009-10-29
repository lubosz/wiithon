#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys
import os
import glob

import util
from util import NonRepeatList
from wiitdb_schema import Particion
import config

class WiithonCLI:

    # Lista de ficheros pendientes de añadir, estos pueden ser:
    # Tipo 1: Imagenes ISO
    # Tipo 2: Comprimidos RAR
    # Tipo 3: Carpetas
    # La lista de ficheros debería ser una cola mejor que una lista
    listaFicheros = NonRepeatList()

    # indice (fila) de la partición seleccionado
    sel_parti = None

    def __init__(self , core):
        self.core = core

    # Define una única partición
    def get_elegir_particion(self, listaParticiones):
        # Del error SI se dan cuenta el GUI o CLI
        if(len(listaParticiones) <= 0):
            raise AssertionError, _("Has conectado el disco duro? No se ha encontrado ninguna particion valida.")
        elif(len(listaParticiones) > 1):
            haElegido = False
            print _("Lista de particiones autodetectadas : ")
            haElegido = False
            while( not haElegido ):
                i = 1
                for dispositivo in listaParticiones:
                    print "%d - %s" % (i , dispositivo)
                    i = i + 1
                print _("%d - Salir") % (i)
                iElegido = raw_input(_("Elige la particion WBFS con la que va ha trabajar : "))
                if( iElegido == i ):
                    raise AssertionError, _("Saliendo por peticion del usuario.")
                    haElegido = True
                else:
                    try:
                        return listaParticiones[int(iElegido) - 1]
                    except IndexError:
                        raise AssertionError, _("Fuera de rango")
                    except ValueError:
                        raise AssertionError, _("Valor incorrecto")
        else:
            return listaParticiones[0]
            
    def criterio_ordenacion_juegos(self, juego1, juego2):
        if juego1.title.lower() > juego2.title.lower():
            return 1
        else:
            if juego1.title.lower() < juego2.title.lower():
                return -1
            else:
                return 0

    # No entiendo muy bien lo de opciones y argumentos, aunque no me lo he podido mirar mucho
    def main(self, opciones, argumentos):
        
        (NADA, LISTAR, EXTRAER, FORMATEAR, MOSTRAR_AYUDA, RENOMBRAR,
        BORRAR, INSTALAR)=([ "%d" % i for i in range(8) ])
        
        accion = NADA

        PAUSA = False
        for option, value in opciones:
            if config.DEBUG:
                print "%s => %s" % (option, value)            

            if   option in ['-p', '--pause']:
                PAUSA = True
            elif option in ['-w', '--work']:
                if os.path.isdir(value):
                    os.chdir(value)
            elif option in ['-h', '--help']:
                accion = MOSTRAR_AYUDA
            elif option in ['-l', '--ls']:
                accion = LISTAR
            elif option in ['-f', '--format']:
                accion = FORMATEAR
            elif option in ['-e', '--extract']:
                accion = EXTRAER
            elif option in ['-r', '--rename']:
                accion = RENOMBRAR
            elif option in ['-d', '--delete']:
                accion = BORRAR
            elif option in ['-i', '--install']:
                accion = INSTALAR
        
        # A = acciones que necesitan una particion WBFS
        # OR
        # B = acciones que necesitan una particion WBFS y un juego
        if accion == LISTAR or accion == EXTRAER or accion == RENOMBRAR or accion == BORRAR or accion == INSTALAR:
            listaParticiones = self.core.sincronizarParticiones()
            self.sel_parti = self.get_elegir_particion(listaParticiones)
            listaJuegos = self.core.syncronizarJuegos(self.sel_parti)
            listaJuegos.sort( self.criterio_ordenacion_juegos )
            hayJuegos = len(listaJuegos) > 0
            if hayJuegos:
                
                # B = acciones que necesitan una particion WBFS y un juego
                if accion == EXTRAER or accion == RENOMBRAR or accion == BORRAR:
                    juego = self.getJuego(listaJuegos)
                    if juego is not None:
                        if accion == EXTRAER:
                            print _("Extraer Juego %s a ISO") % juego
                            if( self.core.extraerJuego(juego) ):
                                print _("Juego %s extraido OK") % (juego)
                            else:
                                print _("ERROR extrayendo la ISO de %s") % (juego)                            
                        elif accion == RENOMBRAR:
                            print _("Renombrar el juego %s.") % (juego)
                            NUEVO_NOMBRE = raw_input(_("Escriba el nuevo nombre : "))
                            if ( self.core.renombrarNOMBRE( juego , NUEVO_NOMBRE ) ):
                                print _("ISO renombrada correctamente a %s") % NUEVO_NOMBRE
                            else:
                                print _("ERROR al renombrar")
                        elif accion == BORRAR:
                            print _("Borrando juego %s") % juego
                            if( self.core.borrarJuego(juego) ):
                                print _("Juego %s borrado correctamente") % (juego)
                            else:
                                print _("ERROR borrando el juego")
                    else:
                        print _("No has seleccionado ningun juego")
                        
                # A = acciones que necesitan una particion WBFS
                if accion == LISTAR or accion == INSTALAR:
                    if accion == LISTAR:
                        print _("Listando juegos de : %s") % self.sel_parti
                        self.listarJuegos(listaJuegos)
                        self.mostrarEspacioLibre(self.sel_parti)
                    elif accion == INSTALAR:
                        print _("Inserte un juego de la Wii en su lector de DVD ...")
                        print _("Juegos originales, solo con lectores LG.")
                        raw_input(_("Pulse cualquier tecla para continuar ... "))
                        self.instalarJuego(self.sel_parti)

            else:
                print _("La particion %s no contiene juegos") % self.sel_parti
                
        # C = acciones que necesitan una particion FAT32
        elif accion == FORMATEAR:                
            listaParticiones = self.core.sincronizarParticiones(config.DETECTOR_WBFS_FAT32)
            self.sel_parti = self.get_elegir_particion(listaParticiones)
            try:
                respuesta = raw_input(_(" Esta seguro de formatear %s (S/N)? ") % self.sel_parti)
                if respuesta.lower() == _("s"):
                    if self.core.formatearWBFS(self.sel_parti):
                        print _("%s se ha formateado correctamente") % self.sel_parti
                    else:
                        print _("%s NO se ha podido formatear") % self.sel_parti
                else:
                    print _("No se ha formateado %s") % self.sel_parti
            except KeyboardInterrupt:
                print
                print _("Interrumpido por el usuario.")
                print _("No se ha completado el formateo de %s") % self.sel_parti

        # D = acciones que no necesitan nada
        if accion == MOSTRAR_AYUDA:
            self.uso()

        if PAUSA:
            raw_input(_("Pulse cualquier tecla para continuar ...\n"))
        sys.exit(0)

        numParametros = len(argumentos)
        if numParametros > 0:
            parm1 = argumentos[0].lower()
            if numParametros > 1:
                parm2 = argumentos[1].lower()
                parm2_sensible = PARAMETROS[1]
                if numParametros > 2:
                    parm3 = argumentos[2].lower()
                    parm3_sensible = argumentos[2]

        if numParametros == 1 and (parm1 == "formatear" or parm1 == "format"):
            listaParticiones = self.core.sincronizarParticiones(config.DETECTOR_WBFS_FAT32)
            self.sel_parti = self.get_elegir_particion(listaParticiones)
            try:
                respuesta = raw_input(_(" Esta seguro de formatear %s (S/N)? ") % self.sel_parti)
                if respuesta.lower() == _("s"):
                    if self.core.formatearWBFS(self.sel_parti):
                        print _("%s se ha formateado correctamente") % self.sel_parti
                    else:
                        print _("%s NO se ha podido formatear") % self.sel_parti
                else:
                    print _("No se ha formateado %s") % self.sel_parti
            except KeyboardInterrupt:
                print
                print _("Interrumpido por el usuario.")
                print _("No se ha formateado %s") % self.sel_parti
        else:
            listaParticiones = self.core.sincronizarParticiones()
            self.sel_parti = self.get_elegir_particion(listaParticiones)
            
            DEVICE = self.sel_parti.device
            FABRICANTE = self.sel_parti.fabricante

            listaJuegos = self.core.syncronizarJuegos(self.sel_parti)
            listaJuegos.sort( self.criterio_ordenacion_juegos )
            hayJuegos = len(listaJuegos) > 0

            # estamos dentro del if numParametros > 1:
            if numParametros == 0 or parm1 == "listar" or parm1 == "ls" :
                if(hayJuegos):
                    print _("Listando juegos de : %s") % (DEVICE + " " + FABRICANTE)
                    self.listarJuegos(listaJuegos)
                    self.mostrarEspacioLibre(self.sel_parti)
                else:
                    print _("No tienes instalado ningun juego en %s") % (DEVICE)
            elif ( parm1 == "instalar" or parm1 == "install"):
                try:
                    print _("Inserte un juego de la Wii en su lector de DVD ...")
                    raw_input(_("Pulse cualquier tecla para continuar ... "))
                    self.instalarJuego(DEVICE)
                except KeyboardInterrupt:
                    print
            elif ( parm1 == "desinstalar" or parm1 == "borrar" or parm1 == "rm" or parm1 == "quitar" or parm1 == "remove"):
                if(hayJuegos):
                    if(numParametros >= 2):
                        parametro = parm2_sensible
                        if (util.getExtension(parametro) == "iso"):
                            IDGAME = util.getMagicISO(parametro)
                        else:
                            IDGAME = parametro
                    else:
                        juego = self.getJuego(listaJuegos)
                    print "%s = %s %s %s %s" % (_("Borrar juego con IDGAME") , juego.idgame , _("en particion"), DEVICE , FABRICANTE)
                    if( juego != None and self.core.borrarJuego(juego) ):
                        print _("Juego %s borrado correctamente" % (juego))
                    else:
                        print _("ERROR borrando el juego")
                else:
                    print _("No hay Juegos que borrar")

            elif ( parm1 == "caratula" or parm1 == "cover"):
                if(hayJuegos):
                    if(numParametros >= 2):
                        IDGAME = parm2_sensible
                    else:
                        juego = self.getJuego(listaJuegos)
                    # FIXME: parametros descarga
                    if(self.core.descargarCaratula(juego.idgame)):
                        print _("OK, descargado %s.png") % juego.idgame
                    else:
                        print _("ERROR, descargando %s.png") % juego.idgame
                else:
                    print _("No hay Juegos para descargar una caratula")
            elif ( parm1 == "caratulas" or parm1 == "covers"):
                if(hayJuegos):
                    if(numParametros >= 1): # 2 parametros
                        if(self.core.descargarTodasLasCaratulaYDiscos(listaJuegos)):
                            print _("OK, todas las caratulas se han descargado")
                        else:
                            print _("ERROR, descargando alguna caratula")
                else:
                    print _("No hay Juegos para descargar caratulas")
            elif ( parm1 == "renombrar" or parm1 == "rename" or parm1 == "r"):
                if(hayJuegos):
                    if(numParametros >= 3):
                        IDGAME = parm2_sensible
                        NUEVO_NOMBRE = parm3_sensible
                    else:
                        IDGAME = self.getJuego(listaJuegos)
                        NUEVO_NOMBRE = raw_input(_("Escriba el nuevo nombre : "))
                    print "%s = %s %s %s" % ( _("Renombrar juego IDGAME") , IDGAME , _("como") , NUEVO_NOMBRE)
                    if ( self.core.renombrarISO( DEVICE , IDGAME , NUEVO_NOMBRE ) ):
                        print _("ISO renombrada correctamente a %s") % NUEVO_NOMBRE
                    else:
                        print _("ERROR al renombrar")
                else:
                    print _("No hay Juegos para renombrar")
            elif ( parm1 == "extraer" or parm1 == "extract" or parm1 == "x"):
                if(hayJuegos):
                    if(numParametros >= 2):
                        IDGAME = parm2_sensible
                    else:
                        IDGAME = self.getJuego(listaJuegos)
                    print "%s = %s %s %s %s" % ( _("Extraer ISO de juego con IDGAME") ,IDGAME , _("en particion") , DEVICE , FABRICANTE)
                    if( self.core.extraerJuego(DEVICE , IDGAME) ):
                        print _("Juego %s extraido OK") % (IDGAME)
                    else:
                        print _("ERROR extrayendo la ISO de %s") % (IDGAME)
                else:
                    print _("No hay Juegos para extraer")
            elif ( parm1 == "ayuda" or parm1 == "h" or parm1 == "help" or parm1 == "-h" or parm1 == "--help" ):
                self.uso()
            else:
                #Los parametros es una lista de ISOS explicita
                for parametro in argumentos:
                    if ( os.path.isdir(parametro) or parametro.lower() == "buscar" or parametro.lower() == "meter" or parametro.lower() == "-r" or parametro.lower() == "metertodo" or parametro.lower() == "buscartodo" or parametro.lower() == "search" ):
                        if( not os.path.isdir(parametro) ):
                            archivo = "."

                        print _("Buscando en %s ficheros RAR ... ") % os.path.dirname(archivo)
                        self.encolar( util.rec_glob(archivo, "*.rar") )

                        print _("Buscando en %s Imagenes ISO ... ") % os.path.dirname(archivo)
                        self.encolar( util.rec_glob(archivo, "*.iso") )

                    elif    (
                            os.path.isfile(parametro) and
                            (
                                util.getExtension(parametro) == "iso" or
                                util.getExtension(parametro) == "rar"
                            )
                        ):
                        parametro = os.path.abspath( parametro )
                        self.encolar( parametro )

                    # si tiene caracteres raros -> no es expresión regular
                    # porque de otro forma, peta la expresion regular.
                    elif( not util.tieneCaracteresRaros(parametro) ):
                        self.encolar( glob.glob(parametro) )
                    else:
                        self.encolar( parametro )

                if (len(self.listaFicheros) == 0):
                    print _("No se ha encontrado ninguna imagen ISO")

            self.procesar(DEVICE, FABRICANTE)


    # Trabajo toda la "listaFicheros", añadiendo todo a la partición WBFS
    def procesar(self, DEVICE, FABRICANTE):
        correctos = []
        erroneos = []

        listaFicheros = self.listaFicheros

        numFicheros = len(listaFicheros)
        if(numFicheros>0):

            #Expandir directorios
            # ...

            numFicherosProcesados = 0
            for fichero in listaFicheros:
                numFicherosProcesados = numFicherosProcesados + 1
                print "===================== "+os.path.basename(fichero)+" ("+str(numFicherosProcesados)+"/"+str(numFicheros)+") ===================="
                print "{"
                if( os.path.exists(DEVICE) and os.path.exists(fichero) ):
                    if( util.getExtension(fichero) == "rar" ):
                        print "%s : %s %s %s %s" % (_("Aniadir RAR con ISO dentro") , os.path.basename(fichero), _("a la particion") , DEVICE, FABRICANTE)
                        nombreRAR = fichero
                        nombreISO = self.core.getNombreISOenRAR(nombreRAR)
                        if (nombreISO != ""):
                            if( not os.path.exists(nombreISO) ):
                                # Paso 1 : Descomprimir
                                if ( self.core.unpack(nombreRAR) ):
                                    print _("Descomprimido correctamente")
                                    # Paso 2 : Añadir la ISO
                                    if ( self.core.anadirISO(DEVICE , nombreISO ) ):
                                            mensaje = _("ISO %s descomprimida y anadida correctamente") % (nombreISO)
                                            print "OK"
                                            correctos.append(mensaje)
                                    else:
                                        mensaje = _("ERROR anadiendo la ISO : %s (comprueba que sea una ISO de WII)") % (nombreISO)
                                        print "ERROR"
                                        erroneos.append(mensaje)

                                        '''
                                    if config.borrarISODescomprimida:
                                        # Paso 3 : Borrar la iso descomprimida
                                        try:
                                            print _("Se va ha borrar la ISO descomprimida")
                                            os.remove(nombreISO)
                                            print _("La ISO %s temporal fue borrada") % (nombreISO)
                                        except:
                                            print _("ERROR al borrar la ISO : %s") % (nombreISO)
                                        print "}"
                                        print
                                    else:
                                        print _("No se ha borrado la ISO temporal")
                                        '''
                                else:
                                    mensaje = _("ERROR al descomrpimir el RAR : %s") % (nombreRAR)
                                    print "ERROR"
                                    print "}"
                                    print
                                    erroneos.append(mensaje)
                            else:
                                mensaje = _("ERROR no se puede descomrpimir por que reemplazaria el ISO : %s") % (nombreISO)
                                print "ERROR"
                                print "}"
                                print
                                erroneos.append(mensaje)
                        else:
                            mensaje = _("ERROR el RAR %s no tenia ninguna ISO") % (nombreRAR)
                            print "ERROR"
                            print "}"
                            print
                            erroneos.append(mensaje)
                    elif( util.getExtension(fichero) == "iso" ):
                        print "%s : %s %s %s %s" % (_("Aniadir ISO") , os.path.basename(fichero) , _("a la particion") , DEVICE , FABRICANTE)
                        if ( self.core.anadirISO(DEVICE , fichero ) ):
                            mensaje = _("ISO %s aniadida correctamente") % fichero
                            print "OK"
                            print "}"
                            print
                            correctos.append(mensaje)
                        else:
                            mensaje = _("ERROR aniadiendo la ISO : %s (comprueba que sea una ISO de WII)") % fichero
                            print "ERROR"
                            print "}"
                            print
                            erroneos.append(mensaje)
                    else:
                        mensaje = _("ERROR %s no es un ningun juego de Wii") % (fichero)
                        print "ERROR"
                        print "}"
                        print
                        erroneos.append(mensaje)
                else:
                    mensaje = _("ERROR la ISO o la particion no existe")
                    print "ERROR"
                    print "}"
                    print
                    erroneos.append(mensaje)

            print "================= %s =========================" % (_("INFORME DE RESULTADOS"))
            print "{"

            if(len(correctos) == numFicherosProcesados):
                print "\t{"
                print "%s================= %s ===================" % ("\t" , _("Todo metido en el HD correctamente"))
                print "\t}"
            else:
                if(len(correctos) > 0):
                    print "%s================ %s (%d/%d) ==============" % ("\t" , _("Juegos correctos") , len(correctos) , numFicherosProcesados)
                    print "\t{"
                    for mensaje in correctos:
                        print "\t"+mensaje
                    print "\t}"

            if(len(erroneos) > 0):
                print "%s=================== %s (%d/%d) =================" % ("\t" , _("Juegos erroneos") , len(erroneos) , numFicherosProcesados)
                print "\t{"
                for mensaje in erroneos:
                    print "\t"+mensaje
                print "\t}"

            print "}"

    # Dumpea la ISO de un BACKUP y lo mete a la partición WBFS
    def instalarJuego(self , particion):
        print _("Buscando un Disco de Wii ...")

        # Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
        listaParticiones = self.core.sincronizarParticiones(config.DETECTOR_WBFS_LECTOR)
        numListaParticiones = len(listaParticiones)

        if(numListaParticiones<=0):
            print _("No se ha encontrado ningun disco de la Wii")
        elif(numListaParticiones > 1):
            print _("Hay mas de un juego de la Wii, deja solo 1 para eliminar la ambiguedad")
        else:# 1 juego de wii
            lector = listaParticiones[0]
            MAGIC_DVD = util.getMagicISO(lector.device)
            SALIDA = "%s/%s.iso" % (os.getcwd(), MAGIC_DVD)
            reemplazada = False
            if (os.path.exists(SALIDA)):
                print _("Ya hay una ISO en : %s") % (SALIDA)
                respuesta = raw_input(_("Desea reemplazarla (S/N) : "))
                if(respuesta.lower() == "s" or respuesta.lower() == "si"):
                    reemplazada = False
                else:
                    reemplazada = True
            print _("Dumpeando desde %s a %s utilizando %s temporalmente") % (lector, particion, SALIDA)
            print _("Puede llevar mucho tiempo ...")
            comando = "dd if=%s of=%s bs=40M conv=noerror,sync"
            if( reemplazada or util.call_out_null(comando % (LECTOR_DVD, SALIDA)) ):
                if( self.core.anadirISO(particion , SALIDA) ):
                    print _("OK, el juego se ha pasado a la particion %s") % particion
                else:
                    print _("Error al pasar la ISO a la particion %s") % particion
                print _("wiithon no borra la ISO temporal: %s, puedes borrarla si no la necesitas") % SALIDA
            else:
                print _("Error al dumpear la ISO")

    # Esta forma parte del GUI, es una forma del CLI de seleccionar 1 juego
    def getJuego(self, listaJuegos):        
        numJuegos = len(listaJuegos)
        if(numJuegos > 0):
            self.listarJuegos(listaJuegos, True)
            try:
                respuesta = ''
                haEscritoAlgo = False
                while not haEscritoAlgo:
                    respuesta = raw_input(_("Indique el NUM del juego : "))
                    if respuesta != '':
                        haEscritoAlgo = True
                
                numJuego = int(respuesta)
                # 1 <= numJuego <= numJuegos
                if ((1 <= numJuego) and (numJuego <= numJuegos)):
                    try:
                        return listaJuegos[numJuego-1]
                    except IndexError:
                        print _("Numero fuera de rango")
            except ValueError:
                print _("El numero dado es incorrecto")
        return None

    def listarJuegos(self , listaJuegos, mostrarIndice = False):
        numJuegos = len(listaJuegos)
        if(numJuegos > 0):
            print "--------------------------------------------------------------------------------"
            if mostrarIndice:
                print "%3s\t%6s\t%-40s\t%7s\t%6s" % ("NUM","IDGAME",_("TITULO"),_("TAMANIO") , _("Caratula?"))
            else:
                print "%6s\t%-55s\t%7s\t%6s" % ("IDGAME",_("TITULO"),_("TAMANIO") , _("Caratula?"))
            print "--------------------------------------------------------------------------------"

            i = 1
            for juego in listaJuegos:
                if (self.core.existeCaratula(juego.idgame) and self.core.existeDisco(juego.idgame)):
                    caratula = _("SI")
                else:
                    caratula = _("NO")

                if mostrarIndice:
                    print "%3s\t%s\t%-40s\t%.2f GB\t%6s" % ( i , juego.idgame , juego.title , juego.size , caratula)
                else:
                    print "%s\t%-55s\t%.2f GB\t%6s" % (juego.idgame , juego.title , juego.size , caratula)

                if ( (i % config.NUM_LINEAS_PAUSA) == 0 ):
                    raw_input(_("Presiona cualquier tecla para mostrar %d lineas mas") % (config.NUM_LINEAS_PAUSA))

                i = i + 1
            print "--------------------------------------------------------------------------------"
            print "%s%d %s" % ("\t\t\t\t\t\t\t" ,numJuegos , _("juegos de WII") )

    def mostrarEspacioLibre(self , particion):
        info = self.core.getEspacioLibreUsado(particion)
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Usado") , info[0])
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Libre") , info[1])
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Total") , info[2])

    def uso(self):
        wiithon = os.path.basename(sys.argv[0])
        print _("AYUDA_CLI") % (
                                wiithon,
                                wiithon, sys.argv[0],
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon, sys.argv[0],
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon,
                                wiithon
                                  )

    def encolar(self , juegos):
        if type(juegos) == list:
            self.listaFicheros.extend( juegos )
        else:
            self.listaFicheros.append( juegos )
