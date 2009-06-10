#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import sys , os , util , glob
import config
from util import NonRepeatList

class WiithonCLI:

    # Lista de ficheros pendientes de añadir, estos pueden ser:
    # Tipo 1: Imagenes ISO
    # Tipo 2: Comprimidos RAR
    # Tipo 3: Carpetas
    # La lista de ficheros debería ser una cola mejor que una lista
    listaFicheros = NonRepeatList()

    def __init__(self , core):
        self.core = core
        # varias particiones
        listaParticiones = self.core.getListaParticiones()
        # Del error SI se dan cuenta el GUI o CLI
        if(len(listaParticiones) == 0):
            raise AssertionError, _("Has conectado el disco duro? No se ha encontrado ninguna particion valida.")
        if(len(listaParticiones) > 1):
            haElegido = False
            print _("Lista de particiones autodetectadas : ")
            haElegido = False
            while( not haElegido ):
                i = 1
                for dispositivo in listaParticiones:
                    print _("%d - Particion: %s" % (i , dispositivo))
                    i = i + 1
                iSalir = str(i)
                print _("%d - Salir") % (iSalir)
                iElegido = raw_input(_("Elige la particion WBFS con la que va ha trabajar : "))
                if( iElegido == iSalir ):
                    raise AssertionError, _("Saliendo por peticion del usuario.")
                    haElegido = True
                else:
                    try:
                        DEVICE = listaParticiones[ int(iElegido) - 1 ]
                        try:
                            cachos = DEVICE.split(":")
                            DEVICE = cachos[0]
                            FABRICANTE = cachos[1]
                        except:
                            raise AssertionError, _("Error obteniendo el Fabricando del HD")
                        haElegido = True
                    except IndexError:
                        raise AssertionError, _("Fuera de rango")
                    except ValueError:
                        raise AssertionError, _("Valor incorrecto")

    # No entiendo muy bien lo de opciones y argumentos, aunque no me lo he podido mirar mucho
    def main(self, opciones, argumentos):

        PARAMETROS = NonRepeatList()
        PARAMETROS.extend(argumentos)
        numParametros = len(PARAMETROS)

        if numParametros > 0:
            parm1 = PARAMETROS[0].lower()
            if numParametros > 1:
                parm2 = PARAMETROS[1].lower()
                parm2_sensible = PARAMETROS[1]
                if numParametros > 2:
                    parm3 = PARAMETROS[2].lower()
                    parm3_sensible = PARAMETROS[2]

        DEVICE = self.core.getDeviceSeleccionado()
        FABRICANTE = self.core.getFabricanteSeleccionado()

        listaJuegos = self.core.getListaJuegos(DEVICE)
        hayJuegos = len(listaJuegos) > 0

        # estamos dentro del if numParametros > 1:
        if numParametros == 0 or parm1 == "listar" or parm1 == "ls" :
            if(hayJuegos):
                print _("Listando juegos de : %s") % (DEVICE + " " + FABRICANTE)
                self.listarISOs(DEVICE , listaJuegos)
                self.mostrarEspacioLibre(DEVICE)
            else:
                print _("No tienes instalado ningún juego en %s %s" % (DEVICE, FABRICANTE))
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
                    IDGAME = self.get_IDJUEGO_de_Lista(DEVICE , listaJuegos)
                print _("Borrar juego con ID : %s en particion %s %s" % (IDGAME , DEVICE , FABRICANTE))
                if( IDGAME != None and self.core.borrarJuego(DEVICE , IDGAME) ):
                    print _("Juego %s borrado correctamente" % (IDGAME))
                else:
                    print _("ERROR borrando el juego")
            else:
                print _("No hay Juegos que borrar")

        elif ( parm1 == "caratula" or parm1 == "cover"):
            if(hayJuegos):
                if(numParametros >= 2):
                    IDGAME = parm2_sensible
                else:
                    IDGAME = self.get_IDJUEGO_de_Lista(DEVICE , listaJuegos)
                if(self.core.descargarCaratula(IDGAME)):
                    print _("OK, descargado %s.png" % IDGAME)
                else:
                    print _("ERROR, descargando %s.png" % IDGAME)
            else:
                print _("No hay Juegos para descargar una caratula")
        elif ( parm1 == "caratulas" or parm1 == "covers"):
            if(hayJuegos):
                tipo = "normal"
                if(numParametros >= 2): # 3 parametros
                    if (parm2 == "panoramico" or parm2 == "widescreen"):
                        print _("Se descargaran en formato paronamico")
                        tipo = "panoramico"
                    elif (parm2 == "3d"):
                        print _("Se descargaran en 3D")
                        tipo = "3d"
                if(self.core.descargarTodasLasCaratulaYDiscos(DEVICE , listaJuegos , tipo)):
                    print _("OK, todas las caratulas se han descargado")
                else:
                    print _("ERROR, descargando alguna caratula")
                    print _("Vuelvelo a intentar o mira en : http://www.theotherzone.com/wii/")
            else:
                print _("No hay Juegos para descargar caratulas")
        elif ( parm1 == "renombrar" or parm1 == "rename" or parm1 == "r"):
            if(hayJuegos):
                if(numParametros >= 3):
                    IDGAME = parm2_sensible
                    NUEVO_NOMBRE = parm3_sensible
                else:
                    IDGAME = self.get_IDJUEGO_de_Lista(DEVICE , listaJuegos)
                    NUEVO_NOMBRE = raw_input(_("Escriba el nuevo nombre : "))
                print _("Renombrar juego ID : %s como %s" % (IDGAME , NUEVO_NOMBRE))
                if ( self.core.renombrarISO( DEVICE , IDGAME , NUEVO_NOMBRE ) ):
                    print _("ISO renombrada correctamente a %s" % NUEVO_NOMBRE)
                else:
                    print _("ERROR al renombrar")
            else:
                print _("No hay Juegos para renombrar")
        elif ( parm1 == "check" or parm1 == "comprobar" or parm1 == "scandisk"):
            if(hayJuegos):
                print _("Verificando todos los juegos de la particion %s") % (DEVICE + " " + FABRICANTE)
                self.verificarTodosLosJuegos(DEVICE , listaJuegos)
            else:
                print _("No hay Juegos para verificar")
        elif ( parm1 == "extraer" or parm1 == "extract" or parm1 == "x"):
            if(hayJuegos):
                if(numParametros >= 2):
                    IDGAME = parm2_sensible
                else:
                    IDGAME = self.get_IDJUEGO_de_Lista(DEVICE , listaJuegos)
                print _("Extraer ISO de juego con ID : %s en particion %s %s" % (IDGAME , DEVICE , FABRICANTE))
                if( self.core.extraerJuego(DEVICE , IDGAME) ):
                    print _("Juego %s extraido OK" % (IDGAME))
                else:
                    print _("ERROR extrayendo la ISO de %s" % (IDGAME))
            else:
                print _("No hay Juegos para extraer")
        elif ( parm1 == "ayuda" or parm1 == "h" or parm1 == "help" or parm1 == "-h" or parm1 == "--help" ):
            self.uso()
        else:
            #Los parametros es una lista de ISOS explicita
            for parametro in PARAMETROS:
                if ( os.path.isdir(parametro) or parametro.lower() == "buscar" or parametro.lower() == "meter" or parametro.lower() == "-r" or parametro.lower() == "metertodo" or parametro.lower() == "buscartodo" or parametro.lower() == "search" ):
                    if( not os.path.isdir(parametro) ):
                        archivo = "."

                    print _("Buscando en %s ficheros RAR ... " % os.path.dirname(archivo))
                    self.encolar( util.rec_glob(archivo, "*.rar") )

                    print _("Buscando en %s Imagenes ISO ... " % os.path.dirname(archivo))
                    self.encolar( util.rec_glob(archivo, "*.iso") )

                elif    (
                        os.path.isfile(parametro) and
                        (
                            util.getExtension(parametro) == "iso" or
                            util.getExtension(parametro) == "rar"
                        )
                    ):
                    self.encolar( parametro )

                # si tiene caracteres raros -> no es expresión regular
                # porque de otro forma, peta la expresion regular.
                elif( not util.tieneCaracteresRaros(parametro) ):
                    self.encolar( glob.glob(parametro) )
                else:
                    self.encolar( parametro )

            if (len(self.listaFicheros) == 0):
                print _("No se ha encontrado ninguna imagen ISO")

        self.procesar( )


    # Trabajo toda la "listaFicheros", añadiendo todo a la partición WBFS
    def procesar(self):
        correctos = []
        erroneos = []
        DEVICE = self.core.getDeviceSeleccionado()
        FABRICANTE = self.core.getFabricanteSeleccionado()

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
                        print _("Aniadir RAR con ISO dentro : %s a la particion %s %s" % (os.path.basename(fichero), DEVICE, FABRICANTE))
                        nombreRAR = fichero
                        nombreISO = self.core.getNombreISOenRAR(nombreRAR)
                        if (nombreISO != ""):
                            if( not os.path.exists(nombreISO) ):
                                # Paso 1 : Descomprimir
                                if ( self.core.descomprimirRARconISODentro(nombreRAR) ):
                                    print _("Descomprimido correctamente")
                                    # Paso 2 : Añadir la ISO
                                    if ( self.core.anadirISO(DEVICE , nombreISO ) ):
                                            mensaje = _("ISO %s descomprimida y añadida correctamente" % nombreISO)
                                            print "OK"
                                            correctos.append(mensaje)
                                    else:
                                        mensaje = _("ERROR añadiendo la ISO : %s (comprueba que sea una ISO de WII)" % nombreISO)
                                        print "ERROR"
                                        erroneos.append(mensaje)

                                    if config.borrarISODescomprimida:
                                        # Paso 3 : Borrar la iso descomprimida
                                        try:
                                            print _("Se va ha borrar la ISO descomprimida")
                                            os.remove(nombreISO)
                                            print _("La ISO %s temporal fue borrada" % (nombreISO))
                                        except:
                                            print _("ERROR al borrar la ISO : %s" % (nombreISO))
                                        print "}"
                                        print
                                    else:
                                        print _("No se ha borrado la ISO temporal")
                                else:
                                    mensaje = _("ERROR al descomrpimir el RAR : %s" % (nombreRAR))
                                    print "ERROR"
                                    print "}"
                                    print
                                    erroneos.append(mensaje)
                            else:
                                mensaje = _("ERROR no se puede descomrpimir por que reemplazaria el ISO : %s" % (nombreISO))
                                print "ERROR"
                                print "}"
                                print
                                erroneos.append(mensaje)
                        else:
                            mensaje = _("ERROR el RAR %s no tenia ninguna ISO" % (nombreRAR))
                            print "ERROR"
                            print "}"
                            print
                            erroneos.append(mensaje)
                    elif( util.getExtension(fichero) == "iso" ):
                        print _("Aniadir ISO : %s a la particion %s %s" % (os.path.basename(fichero) , DEVICE , FABRICANTE))
                        if ( self.core.anadirISO(DEVICE , fichero ) ):
                            mensaje = _("ISO %s aniadida correctamente" % fichero)
                            print "OK"
                            print "}"
                            print
                            correctos.append(mensaje)
                        else:
                            mensaje = _("ERROR aniadiendo la ISO : %s (comprueba que sea una ISO de WII)" % fichero)
                            print "ERROR"
                            print "}"
                            print
                            erroneos.append(mensaje)
                    else:
                        mensaje = _("ERROR %s no es un ningun juego de Wii" % (fichero))
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

            print _("================= INFORME DE RESULTADOS =========================")
            print "{"

            if(len(correctos) == numFicherosProcesados):
                print "\t{"
                print _("%s================= Todo metido en el HD correctamente ===================" % ("\t"))
                print "\t}"
            else:
                if(len(correctos) > 0):
                    print _("%s================ Juegos correctos (%d/%d) ==============" % ("\t" , len(correctos) , numFicherosProcesados))
                    print "\t{"
                    for mensaje in correctos:
                        print "\t"+mensaje
                    print "\t}"

            if(len(erroneos) > 0):
                print _("%s=================== Juegos erroneos (%d/%d) =================" % ("\t" , len(erroneos) , numFicherosProcesados))
                print "\t{"
                for mensaje in erroneos:
                    print "\t"+mensaje
                print "\t}"

            print "}"


    # Dumpea la ISO de un BACKUP y lo mete a la partición WBFS
    def instalarJuego(self , DEVICE):

        salida = ""
        print _("Buscando un Disco de Wii ...")

        salida = util.getSTDOUT( config.DETECTOR_WBFS_LECTOR )

        # Le quito el ultimo salto de linea y forma la lista cortando por saltos de linea
        listaParticiones = NonRepeatList()
        if (salida <> ""):
            listaParticiones = salida[:-1].split("\n")

        numListaParticiones = len(listaParticiones)
        if(numListaParticiones<=0):
            print _("No se ha encontrado ningun disco de la Wii")
        elif(numListaParticiones > 1):
            print _("Hay mas de un juego de la Wii, deja solo 1 para eliminar la ambiguedad")
        else:# 1 juego de wii
            try:
                cachos = listaParticiones[0].split(":")
                LECTOR_DVD = cachos[0]
                FABRICANTE_DVD = cachos[1]
                MAGIC_DVD = util.getMagicISO(LECTOR_DVD)
                SALIDA = os.getcwd()+"/"+MAGIC_DVD+".iso"
                reemplazada = False
                if (os.path.exists(SALIDA)):
                    print _("Ya hay una ISO en : %s" % (SALIDA))
                    respuesta = raw_input(_("Desea reemplazarla (S/N) : "))
                    if(respuesta.lower() == "s" or respuesta.lower() == "si"):
                        reemplazada = False
                    else:
                        reemplazada = True
                print _("%s a un ISO temporal de 4.4GB en = %s.iso ..." % (FABRICANTE_DVD , MAGIC_DVD))
                if( reemplazada or (os.system("dd if="+LECTOR_DVD+" of="+SALIDA+" bs=1M")==0) ):
                    if ( self.core.anadirISO(DEVICE , SALIDA)):
                        if( self.core.descargarCaratula(MAGIC_DVD) ):
                            print _("Caratula descargada como %s/%s.png" % (os.getcwd() , MAGIC_DVD))
                        else:
                            print _("No se ha encontrado caratula para el juego %s" % MAGIC_DVD)
                    else:
                        print _("Error al pasar la ISO al disco duro")
                    print _("wiithon no borra la ISO temporal, puedes borrarla si no la necesitas")
                else:
                    print _("Error al dumpear la ISO")
            except KeyboardInterrupt:
                print _("Interrumpido por el usuario")


    # Esta forma parte del GUI, es una forma del CLI de seleccionar 1 juego
    def get_IDJUEGO_de_Lista(self , DEVICE , listaJuegos):
        numJuegos = len(listaJuegos)
        if(numJuegos > 0):
            print "--------------------------------------------------------------------------------"
            print "%3s\t%6s\t%-40s\t%7s\t%6s" % ("NUM","IDGAME",_("TITULO"),_("TAMANIO") , _("Caratula?"))
            print "--------------------------------------------------------------------------------"
            i = 1
            for juego in listaJuegos:
                ocupado = float(juego[2])
                if (self.core.existeCaratula(juego[0])):
                    caratula = _("SI")
                else:
                    caratula = _("NO")
                print "%3s\t%s\t%-40s\t%.2f GB\t%6s" % ( i , juego[0] , juego[1] , ocupado , caratula)
                if ( (i % config.NUM_LINEAS_PAUSA) == 0 ):
                    raw_input(_("Presiona cualquier tecla para mostrar %d lineas mas" % (config.NUM_LINEAS_PAUSA)))
                i = i + 1
            print "--------------------------------------------------------------------------------"

            try:
                numJuego = int( raw_input(_("Indique el NUM del juego : ")) )
                # 1 <= numJuego <= numJuegos
                if ((1 <= numJuego) and (numJuego <= numJuegos)):
                    try:
                        return listaJuegos[numJuego-1][0]
                    except IndexError:
                        print _("Numero fuera de rango")
            except ValueError:
                print _("El numero dado es incorrecto")
        return "??????"

    # dada la lista de juegos, esta se representa
    # en GUI se refrescaría el TreeView
    # en CLI se haría como se hace ahora
    def listarISOs(self , DEVICE , listaJuegos):
        numJuegos = len(listaJuegos)
        if(numJuegos > 0):
            print "--------------------------------------------------------------------------------"
            print "%6s\t%-55s\t%7s\t%6s" % ("IDGAME",_("TITULO"),_("TAMANIO") , _("Cararuta?"))
            print "--------------------------------------------------------------------------------"
            i = 1
            for juego in listaJuegos:
                ocupado = float(juego[2])
                if (self.core.existeCaratula(juego[0]) and self.core.existeDisco(juego[0])):
                    caratula = _("SI")
                else:
                    caratula = _("NO")
                print "%s\t%-55s\t%.2f GB\t%6s" % (juego[0] , juego[1] , ocupado , caratula)
                if ( (i % config.NUM_LINEAS_PAUSA) == 0 ):
                    raw_input(_("Presiona cualquier tecla para mostrar %d lineas mas" % (config.NUM_LINEAS_PAUSA)))
                i = i + 1
            print "--------------------------------------------------------------------------------"
            print _("%s%d juegos de WII" % ( "\t\t\t\t\t\t\t" ,numJuegos))
            return numJuegos
        else:
            return 0


    # Dada una lista de juegos, verifica su estado
    # Hay que separar la lógica de la presentación
    def verificarTodosLosJuegos(self , DEVICE , listaJuegos):
        listaCorruptos = []
        numJuegos = len(listaJuegos)
        if(numJuegos > 0):
            print "--------------------------------------------------------------------------------"
            print "%6s\t%-40s\t%s" % ("IDGAME",_("TITULO") , _("Corrupto?"))
            print "--------------------------------------------------------------------------------"
            for juego in listaJuegos:
                if( self.core.verificarJuego( DEVICE , juego[0] ) ):
                    corrupto = _("NO ESTA CORRUPTO")
                else:
                    corrupto = _("ESTA CORRUPTO")
                    listaCorruptos.append(juego)
                print "%s\t%-40s\t%s" % ( juego[0] , juego[1] , corrupto)
        numCorruptos = len(listaCorruptos)
        if (numCorruptos > 0):
            print "--------------------------------------------------------------------------------"
            print _("Lista de juegos corruptos")
            print "--------------------------------------------------------------------------------"
            for juego in listaCorruptos:
                print "%s\t%-40s" % ( juego[0] , juego[1] )
            print "--------------------------------------------------------------------------------"
            print _("Hay %d juegos corruptos, se recomienda que los desinstale" % (numCorruptos))
            print "--------------------------------------------------------------------------------"
            respuesta = raw_input(_("Quieres desinstalarlos? (S/N) "))
            if(respuesta.lower() == _("s") or respuesta.lower() == _("si")):
                for juego in listaCorruptos:
                    if (borrarJuego(DEVICE , juego[0])):
                        print _("%s borrado correctamente" % (juego[0]))
                    else:
                        print _("ERROR : %s NO se ha borrado correctamente" % (juego[0]))
            else:
                print _("Saliendo. No se ha desinstalado nada")


    def mostrarEspacioLibre(self , DEVICE):
        info = self.core.getEspacioLibre(DEVICE)
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Usado") , info[0])
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Libre") , info[1])
        print "\t\t\t\t\t\t\t%s : %.2f GB" % (_("Total") , info[2])

    def uso(self):
        wiithon = os.path.basename(sys.argv[0])
        print '''
Listar juegos. El programa por defecto, sin parametros, hace un listado de los juegos (lanzara el GUI en alguna prox versión):
\t\t%s

Añadir ISO mediante una lista explicita de las ISOS:
\t\t%s "%s/wii/mario.iso" "iso2" "iso3" "isoN"

Añadir ISO con exp. reg. La expresión solo afecta al directorio actual, actualmente no es recursivo:
\t\t%s *.iso

Buscar y Añadir ISO's recursivamente. Busca todos las imagenes isos RECURSIVAMENTE, incluso tambien busca dentro de RAR, a falta de implementar zip), tal vez necesites apt-get install rar.
\t\t%s buscar

Borrar juegos. Especificando el juego mediante un menú:
\t\t%s borrar

Borrar juegos. Podemos borrar con el IDGAME:
\t\t%s borrar IDJUEGO

Borrar juegos. Podemos borrar con el IDGAME obtenido a partir de un ISO local. El archivo ISO local NO es borrado:
\t\t%s borrar "%s/wii/mario.iso"

Renombrar juegos. Especificando el juego mediante un menú:
\t\t%s renombrar

Renombrar juegos, puedes cambiar el nombre de los juegos ya metidos en HD, útil para que nos enteremos cuando estemos con el USB Loader:
\t\t%s renombrar IDGAME "Mario Kart Wii"

Extraer juegos a un archivo ISO. El juego es especificado mediante un menú:
\t\t%s extraer

Extraer juegos a un archivo ISO. OJO! : El archivo ISO de salida pertenecerá a root:
\t\t%s extraer IDJUEGO

Descargar todas las caratulas automaticamente a 160x225. Ojo puede que el servidor te banee, si te ocurre intentalo 5 minutos más tarde:
\t\t%s caratulas

Descargar la caratulas de un juego especificado por su IDGAME, la imagen es bajada a 160x225. El comando es un singular, es "caratula" ya que "caratulas" descarga todas:
\t\t%s caratula IDGAME

Descargar la caratulas de un juego especificado por menú, la imagen es bajada a 160x225. El comando es un singular, es "caratula" ya que "caratulas" descarga todo:
\t\t%s caratula"

Comprobar Integridad de los juegos. Muchos de nuestros juegos pueden estar corruptos sin aún saberlo debido a el bug de borrado de las primeras versiones de WBFS
\t\t%s comprobar

Instar juegos desde el DVD, al estilo del usb loader, pero algo más lento porque dumpea a ISO y cuando termina mete la ISO:
\t\t%s instalar


Web : http://blogricardo.wordpress.com/2009/04/07/wiithon-wbfs-gui-para-wii
''' % (
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
    wiithon,
    wiithon
      )

    def encolar(self , juegos):
        if type(juegos) == list:
            self.listaFicheros.extend( juegos )
        else:
            self.listaFicheros.append( juegos )

