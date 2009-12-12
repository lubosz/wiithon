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

(AUTOMATICO, EXPLICITO)=([ "%d" % i for i in range(2) ])

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
    def get_elegir_particion(self, listaParticiones, modo_particion = AUTOMATICO, device_explicito = ''):
        
        if modo_particion == EXPLICITO:
            i = 0
            encontrado = False
            while not encontrado and i<len(listaParticiones):
                encontrado = listaParticiones[i].device == device_explicito
                if not encontrado:
                    i += 1
            if encontrado:
                return listaParticiones[i]
            else:
                print _("No se ha encontrado la particion: %s") % device_explicito
                return None

        else: # AUTOMATICO
            # Del error SI se dan cuenta el GUI o CLI
            if(len(listaParticiones) <= 0):
                return None
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
                    iElegido = raw_input(_("Elige la particion WBFS con la que va a trabajar : "))
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
        
        (NADA, LISTAR, ANADIR, ANADIR_ALL, EXTRAER, FORMATEAR, MOSTRAR_AYUDA, RENOMBRAR,
        BORRAR, INSTALAR, CARATULAS, DISCOS, MOSTRAR_VERSION)=([ "%d" % i for i in range(13) ])
        
        accion = NADA
        modo_game = AUTOMATICO
        modo_particion = AUTOMATICO
        device_explicito = ''
        game_explicito = ''
        anadir_value = ''

        PAUSA = False
        for option, value in opciones:
            if config.DEBUG:
                print "%s => %s" % (option, value)            

            if   option in ['--pause']:
                PAUSA = True
            elif option in ['-p', '--partition']:
                modo_particion = EXPLICITO
                device_explicito = value
            elif option in ['-g', '--game']:
                modo_game = EXPLICITO
                game_explicito = value
            elif option in ['-w', '--work']:
                if os.path.isdir(value):
                    os.chdir(value)
            elif option in ['-h', '--help']:
                accion = MOSTRAR_AYUDA
            elif option in ['-l', '--ls']:
                accion = LISTAR
            elif option in ['-f', '--format']:
                accion = FORMATEAR
            elif option in ['-m','--massive']:
                accion = ANADIR_ALL
            elif option in ['-a', '--add']:
                accion = ANADIR
                anadir_value = value
            elif option in ['-e', '--extract']:
                accion = EXTRAER
            elif option in ['-r', '--rename']:
                accion = RENOMBRAR
            elif option in ['-d', '--delete']:
                accion = BORRAR
            elif option in ['-i', '--install']:
                accion = INSTALAR
            elif option in ['--covers']:
                accion = CARATULAS
            elif option in ['--discs']:
                accion = DISCOS
            elif option in ['-v', '--version']:
                accion = MOSTRAR_VERSION
        
        # A = acciones que necesitan una particion WBFS
        # OR
        # B = acciones que necesitan una particion WBFS y un juego
        if accion == LISTAR or accion == ANADIR or accion == ANADIR_ALL or accion == EXTRAER or accion == RENOMBRAR or accion == BORRAR or accion == INSTALAR or accion == CARATULAS or accion == DISCOS:
            listaParticiones = self.core.sincronizarParticiones()
            self.sel_parti = self.get_elegir_particion(listaParticiones, modo_particion, device_explicito)
            if self.sel_parti is not None:
                listaJuegos = self.core.syncronizarJuegos(self.sel_parti)
                listaJuegos.sort( self.criterio_ordenacion_juegos )
                hayJuegos = len(listaJuegos) > 0

                # B = acciones que necesitan una particion WBFS y un juego
                if accion == EXTRAER or accion == RENOMBRAR or accion == BORRAR:
                    if hayJuegos:
                        juego = self.getJuego(listaJuegos, modo_game, game_explicito)
                        if juego is not None:
                            if accion == EXTRAER:
                                print _("Extraer Juego %s a ISO") % juego
                                if( self.core.extraerJuego(juego, ".", self.core.prefs.FORMATO_EXTRACT) ):
                                    print _("Juego %s extraido OK") % (juego)
                                else:
                                    print _("ERROR extrayendo la ISO de %s") % (juego)                            
                            elif accion == RENOMBRAR:
                                print _("Renombrar el juego %s.") % (juego)
                                NUEVO_NOMBRE = raw_input(_("Escriba el nuevo nombre : "))
                                if len(NUEVO_NOMBRE) > 0:
                                    if ( self.core.renombrarNOMBRE( juego , NUEVO_NOMBRE ) ):
                                        print _("ISO renombrada correctamente a %s") % NUEVO_NOMBRE
                                    else:
                                        print _("ERROR al renombrar")
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
                    else:
                        print _("La particion %s no contiene juegos") % self.sel_parti
                        
                # A = acciones que necesitan una particion WBFS
                if accion == ANADIR or accion == ANADIR_ALL or accion == LISTAR or accion == INSTALAR or accion == CARATULAS or accion == DISCOS:
                    if accion == ANADIR_ALL or accion == ANADIR:
                    
                        if accion == ANADIR_ALL:
                            # directorio actual
                            archivo = "."
                            
                            print _("Buscando ficheros RAR recursivamente ... ")
                            self.encolar( util.rec_glob(archivo, "*.rar") )

                            print _("Buscando imagenes ISO recursivamente ... ")
                            self.encolar( util.rec_glob(archivo, "*.iso") )
                            
                            print _("Buscando imagenes WBFS recursivamente ... ")
                            self.encolar( util.rec_glob(archivo, "*.wbfs") )
                            
                            print _("Buscando imagenes WDF recursivamente ... ")
                            self.encolar( util.rec_glob(archivo, "*.wdf") )
                            
                        elif accion == ANADIR:
                            if(
                                    os.path.isfile(anadir_value) and 
                                        (
                                            self.core.getAutodetectarFormato(anadir_value) is not None
                                        )
                                    ):
                                self.encolar( anadir_value )
                            elif( not util.tieneCaracteresRaros(anadir_value) ):
                                self.encolar( glob.glob(anadir_value) )
                            else:
                                self.encolar( anadir_value )

                        # comun a ANADIR y ANADIR_ALL
                        if (len(self.listaFicheros) == 0):
                            print _("No se ha encontrado ningun fichero en los formatos validos: %s") % "iso, rar, wbfs, wdf."
                        else:
                            self.procesar(self.sel_parti)

                    elif accion == LISTAR:
                        print _("Listando juegos de : %s") % self.sel_parti
                        self.listarJuegos(listaJuegos)
                        self.mostrarEspacioLibre(self.sel_parti)
                    elif accion == INSTALAR:
                        print _("Inserte un juego de la Wii en su lector de DVD ...")
                        print _("Juegos originales, solo con lectores LG.")
                        raw_input(_("Pulse cualquier tecla para continuar ... "))
                        self.instalarJuego(self.sel_parti)
                    elif accion == CARATULAS or accion == DISCOS:
                        
                        # descargo todas las caratulas y discos
                        if(self.core.descargarTodasLasCaratulaYDiscos(listaJuegos)):
                            print _("OK, todas las caratulas se han descargado")
                        else:
                            print _("ERROR, descargando alguna caratula")
                        
                        # defino el destino
                        destino = os.getcwd()
                        
                        # copia al directorio de trabajo                            
                        for juego in listaJuegos:
                            if accion == CARATULAS:
                                self.core.copiarCaratula(juego, destino)
                            elif accion == DISCOS:
                                self.core.copiarDisco(juego, destino)
                            
                        print _("Tarea finalizada")
            else:
                print _("Has conectado el disco duro? No se ha encontrado ninguna particion valida.")

        # C = acciones que necesitan una particion FAT32
        elif accion == FORMATEAR:                
            listaParticiones = self.core.sincronizarParticiones(config.DETECTOR_WBFS_FAT32)
            self.sel_parti = self.get_elegir_particion(listaParticiones)
            if self.sel_parti is not None:
                try:
                    respuesta = raw_input(_("Realmente, desea formatear a WBFS la particion %s? (S/N) ") % self.sel_parti)
                    if respuesta.lower() == _("s"):
                        if self.core.formatearWBFS(self.sel_parti):
                            print _("%s se ha formateado correctamente") % self.sel_parti
                        else:
                            print _("Error al formatear %s") % self.sel_parti
                    else:
                        print _("No se ha formateado %s") % self.sel_parti
                except KeyboardInterrupt:
                    print
                    print _("Interrumpido por el usuario.")
                    print _("No se ha formateado %s") % self.sel_parti
            else:
                print _("Has conectado el disco duro? No se ha encontrado ninguna particion valida.")
                print _("Comprueba que tienes la particion FAT32 montada.")

        # D = acciones que no necesitan nada
        elif accion == MOSTRAR_AYUDA:
            self.uso()
            
        elif accion == MOSTRAR_VERSION:
            print "Wiithon version %s (rev %s)" % (config.VER, config.REV)

        if PAUSA:
            raw_input(_("Pulse cualquier tecla para continuar ...\n"))

        sys.exit(0)


    def procesar_rar(self, particion, archivoRAR, correctos, erroneos):
        # presuponemos que hay error y no hay exito
        exito = False
        error = True

        nombreISO = self.core.getNombreISOenRAR(archivoRAR)        
        rutaISO = os.path.join(self.core.prefs.ruta_extraer_rar, nombreISO)
           
        if (not os.path.exists(archivoRAR)):
            erroneos.append(_("El archivo RAR %s: No existe") % archivoRAR)

        elif os.path.exists(rutaISO):
            if not self.core.prefs.rar_overwrite_iso:
                erroneos.append(_("Error al descomprimrir. Ya existe %s. Si desea sobreescribirlo, modifique la opcion en preferencias.") % rutaISO)
            else:
                if os.path.exists(rutaISO):
                    os.remove(rutaISO)
                    error = False

        elif nombreISO is None:
            erroneos.append(_("Error: El archivo RAR %s no contiene ninguna ISO") % (archivoRAR))

        else:
            error = False
            
        if not util.space_for_dvd_iso_wii(self.core.prefs.ruta_extraer_rar):
            erroneos.append(_("No hay 4.4GB libres para descomprimir el fichero RAR: %s en la ruta %s. Puede cambiar la ruta en preferencias.") % (archivoRAR, self.ruta_extraer_rar))
            error = True
        
        if not error:

            if ( self.core.unpack(archivoRAR, self.core.prefs.ruta_extraer_rar, nombreISO, self.core.prefs.rar_overwrite_iso) ):

                correctos, erroneos, exito = self.procesar_iso(particion, rutaISO, correctos, erroneos)

                # dont ask, if want ask ---> delete                
                if self.core.prefs.rar_preguntar_borrar_iso:
                    os.remove(rutaISO)

                # dont ask, if want ask ---> delete
                if self.core.prefs.rar_preguntar_borrar_rar:
                    util.remove_multipart_rar(archivoRAR)
            else:
                erroneos.append(_("Error al descomrpimir el RAR : %s") % (archivoRAR))

        return correctos, erroneos, exito
        
    def procesar_iso(self, particion, fichero, correctos, erroneos):
        ok = self.core.anadirISO(particion , fichero )
        if ( ok ):
            correctos.append(_("ISO %s aniadida correctamente") % fichero)
        else:
            erroneos.append(_("ERROR aniadiendo la ISO : %s (comprueba que sea una ISO de WII)") % fichero)

        return correctos, erroneos, ok

    # Trabajo toda la "listaFicheros", añadiendo todo a la partición WBFS
    def procesar(self, particion):
        correctos = []
        erroneos = []

        listaFicheros = self.listaFicheros

        numFicheros = len(listaFicheros)
        if(numFicheros>0):

            numFicherosProcesados = 0
            for fichero in listaFicheros:
                numFicherosProcesados = numFicherosProcesados + 1
                print "===================== "+os.path.basename(fichero)+" ("+str(numFicherosProcesados)+"/"+str(numFicheros)+") ===================="
                print "{"
                print _("Copiar .%s: %s a la particion %s") % (util.getExtension(fichero).upper(), os.path.basename(fichero), particion)
                
                ok = False
                if( util.getExtension(fichero) == "rar" ):
                    correctos, erroneos, ok = self.procesar_rar(particion, fichero, correctos, erroneos)
                elif(self.core.getAutodetectarFormato(fichero) is not None):
                    correctos, erroneos, ok = self.procesar_iso(particion, fichero, correctos, erroneos)
                else:
                    erroneos.append(_("ERROR %s no es un ningun juego de Wii") % (fichero))
                    
                if ok:
                    print "OK"
                else:
                    print "ERROR"

                print "}"
                print
                    

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
            MAGIC_DVD = util.getMagicISO(lector.device, 'iso')
            SALIDA = "%s/%s.iso" % (os.getcwd(), MAGIC_DVD)
            reemplazada = False
            if (os.path.exists(SALIDA)):
                print _("Ya hay una ISO en : %s") % (SALIDA)
                respuesta = raw_input(_("Desea reemplazarla (S/N) : "))
                if(respuesta.lower() == _("s")):
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
    def getJuego(self, listaJuegos, modo_game = AUTOMATICO, game_explicito = ''):        
        if modo_game == EXPLICITO:
            i = 0
            encontrado = False
            while not encontrado and i<len(listaJuegos):
                encontrado = listaJuegos[i].idgame == game_explicito
                if not encontrado:
                    i += 1
            if encontrado:
                return listaJuegos[i]
            else:
                print _("No se ha encontrado el juego: %s") % game_explicito

        else: # AUTOMATICO
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
                print "%3s\t%6s\t%-40s\t%7s\t%6s" % ("NUM","IDGAME",_("TITULO"),_("SIZE") , _("Caratula?"))
            else:
                print "%6s\t%-55s\t%7s\t%6s" % ("IDGAME",_("TITULO"),_("SIZE") , _("Caratula?"))
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
        # long text in translated po
        print _("AYUDA_CLI")

    def encolar(self , juegos):
        if type(juegos) == list:
            self.listaFicheros.extend( juegos )
        else:
            self.listaFicheros.append( juegos )
