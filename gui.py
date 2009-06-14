#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import time
import sys
from threading import Thread

import gtk
import gobject
import pango

import config
import util
from builder_wrapper import GtkBuilderWrapper
from trabajo import PoolTrabajo
from preferencias import session, Preferencia
from juego import Juego
from animar import Animador

class WiithonGUI(GtkBuilderWrapper):

    def __init__(self, core):
        GtkBuilderWrapper.__init__(self, os.path.join(config.WIITHON_FILES_RECURSOS_GLADE  , 'wiithon.ui'))

        self.core = core
        self.buscar = ""
        self.modo = "desconocido" # desconocido | ver | manager

        self.preferencia = session.query(Preferencia).first()
        # Nunca se han creado preferencias
        if self.preferencia == None:
            self.preferencia = Preferencia()
            session.save( self.preferencia )
            session.commit()

        # verificar que las rutas existen
        if(not os.path.exists(self.preferencia.ruta_anadir)):
        	self.preferencia.ruta_anadir = os.getcwd()

        if(not os.path.exists(self.preferencia.ruta_anadir_directorio)):
        	self.preferencia.ruta_anadir_directorio = os.getcwd()

        if(not os.path.exists(self.preferencia.ruta_extraer_iso)):
        	self.preferencia.ruta_extraer_iso = os.getcwd()

        if(not os.path.exists(self.preferencia.ruta_copiar_caratulas)):
        	self.preferencia.ruta_copiar_caratulas = os.getcwd()

        if(not os.path.exists(self.preferencia.ruta_copiar_discos)):
        	self.preferencia.ruta_copiar_discos = os.getcwd()

        ######### PUNTEROS ##############

        # Referencia copia a la lista de juegos
        self.listaJuegos = None

        # Juego seleccionado
        self.pathJuegoSeleccionado = None
        self.seleccionJuegoSeleccionado = None
        self.iteradorJuegoSeleccionado = None
        self.IDGAMEJuegoSeleccionado = ""

        self.seleccionParticionSeleccionada = None
        self.iteradorParticionSeleccionada = None
        self.DEVICEParticionSeleccionada = ""

        ########### HILOS ###############

        # permite usar hilos con PyGTK http://faq.pygtk.org/index.py?req=show&file=faq20.006.htp
        # modo seguro con hilos
        gobject.threads_init()

        self.wb_principal.set_title('Wiithon')
        # FIXME: Hacer otro icono pequeño
        # self.wb_principal.set_icon_from_file( "/usr/share/pixmaps/wiithon.svg" )
        self.wb_principal.show()

        self.wb_tb_anadir.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_anadir_directorio.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_extraer.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_renombrar.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_clasificar1.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_borrar.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_copiar_SD.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_acerca_de.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_copiar_1_1.connect('clicked' , self.on_tb_toolbar_clicked)

        # oculto la fila de progreso
        self.wb_box_progreso.hide()

        #ocultar de momento
        self.wb_expander1.hide()

        self.wb_busqueda = util.Entry(clear=True)
        self.wb_busqueda.show()
        self.wb_box_busqueda.pack_start(self.wb_busqueda)

        self.wb_busqueda.connect('changed' , self.on_busqueda_changed)
        self.wb_principal.connect('destroy', self.salir)

        # carga la vista del TreeView de particiones
        self.tv_partitions_modelo = self.cargarParticionesVista()

        destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")
        self.wb_estadoBatch.set_from_file( destinoIcono )

        '''
        if os.geteuid() != 0:
            self.alert("error" , _("REQUIERE_ROOT") % (config.APP , config.APP) )
            raise AssertionError, _("Error en permisos")
        '''

        self.listaParticiones = self.core.getListaParticiones()
        self.numParticiones = len(self.listaParticiones)
        if(self.numParticiones == 0):
            # establecemos el modo de wiithon
            self.modo = "ver"

            # carga la vista del TreeView de juegos
            self.tv_games_modelo = self.cargarJuegosVista( )

            # Lista los juegos de TODAS las particiones
            self.DEVICEParticionSeleccionada = "%"

            # cargar datos desde la base de datos
            self.refrescarListaJuegosFromBDD()

            #ocultar algunas coasa
            self.wb_vboxProgresoEspacio.hide()
            self.wb_labelEspacio.hide()

            # no hay trabajos en este modo
            self.poolTrabajo = None

            if( len(self.listaJuegos)>0 ):
                self.alert("warning" , _("No se han encontrado particiones WBFS:\nConecte un disco duro con una particion de juegos de Wii (tipo WBFS)\nEn este modo, SOLO puede visualizar toda su base de datos de juegos acumulada por %s en sesiones anteriores." % (config.APP)))
            else:
                self.alert("warning" , _("No se han encontrado particiones WBFS:\nConecte un disco duro con una particion de juegos de Wii (tipo WBFS) y reinicie %s\n" % (config.APP)))
        else:
            # establecemos el modo de wiithon, hay particiones que gestionar
            self.modo = "manager"

            # carga la vista del TreeView de juegos
            self.tv_games_modelo = self.cargarJuegosVista( )

            # carga el modelo de datos del TreeView de particiones
            self.cargarParticionesModelo(self.tv_partitions_modelo , self.listaParticiones)

            # selecciono la primera partición
            # indirectamente se carga:
            # lee el modelo de datos de la partición seleccionada
            # tambien refresca la lista de juegos del CORE
            self.seleccionarPrimeraFila( self.wb_tv_partitions , self.on_tv_partitions_cursor_changed)

            # Trabajador, se le mandan trabajos de barra de progreso (trabajos INTENSOS)
            self.poolTrabajo = PoolTrabajo( self.core , 1)
            self.poolTrabajo.setDaemon(True)
            self.poolTrabajo.start()

            # Para atender mensajes
            self.hiloAtenderMensajes = HiloAtenderMensajes( self.core , self.poolTrabajo , self.wb_progreso1 , self )
            self.hiloAtenderMensajes.setDaemon(True)
            self.hiloAtenderMensajes.start()

        # descargar caratulas desde un hilo, inicialmente mira caratulas en los juegos existentes (trabajos LIGEROS)
        self.poolBash = PoolTrabajo( self.core , 6)
        self.poolBash.setDaemon(True)
        self.poolBash.start()
        for juego in self.listaJuegos:
            self.poolBash.nuevoTrabajoDescargaCaratula( juego.idgame )
            self.poolBash.nuevoTrabajoDescargaDisco( juego.idgame )

        self.animar = Animador( self.wb_estadoBatch , self.poolBash , self.poolTrabajo)
        self.animar.setDaemon(True)
        self.animar.start()

        # si no hay juegos pongo las caratulas por defecto
        if( len(self.listaJuegos) == 0 ):
            destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
            self.wb_img_caratula1.set_from_file( destinoCaratula )
            destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
            self.wb_img_disco1.set_from_file( destinoDisco )

        if(self.numParticiones > 0):
            # Seleccciono particion de las preferencias
            pass

        if(len(self.listaJuegos) > 0):
            # Selecciono el juego de las preferencias
            pass

        # pongo el foco en el buscador
        self.wb_busqueda.grab_focus()

    def main(self , opciones , argumentos):

        for arg in argumentos:
            arg = os.path.abspath(arg)
            if os.path.exists(arg):
                if util.getExtension(arg)=="iso":
                    self.poolTrabajo.nuevoTrabajoAnadir( arg )
                else:
                    self.alert("warning" , _("Formato desconocido"))

        gtk.main()

    # http://www.pygtk.org/pygtk2reference/class-pangoattribute.html
    def getEstilo_azulGrande(self):

        #Creo una lista de atributos
        atributos = pango.AttrList()

        #inserto el tamaño (tamaño_en_puntos * 1000)
        #el 0,-1 indica que se aplica a todo el texto del label.
        atributos.insert(pango.AttrSize(13000,0,-1))

        #inserto el grosor
        #200=ultra-light, 300=light, 400=normal, 700=bold, 800=ultra-bold, 900=heavy
        atributos.insert(pango.AttrWeight(700,0,-1))

        #color (de 0 a 65535 (no 255 ...))
        atributos.insert(pango.AttrForeground(0x0011,0x4444,0xFFFF,0,-1))

        return atributos

    def getEstilo_grisGrande(self):

        #Creo una lista de atributos
        atributos = pango.AttrList()

        #inserto el tamaño (tamaño_en_puntos * 1000)
        #el 0,-1 indica que se aplica a todo el texto del label.
        atributos.insert(pango.AttrSize(13000,0,-1))

        #inserto el grosor
        #200=ultra-light, 300=light, 400=normal, 700=bold, 800=ultra-bold, 900=heavy
        atributos.insert(pango.AttrWeight(700,0,-1))

        #color (de 0 a 65535 (no 255 ...))
        atributos.insert(pango.AttrForeground(0xCCCC,0xCCCC,0xCCCC,0,-1))

        return atributos

    def cargarParticionesVista(self):
        tv_partitions = self.wb_tv_partitions

        render = gtk.CellRendererText()

        columna1 = gtk.TreeViewColumn(_('Dispositivo'), render , text=1)
        columna2 = gtk.TreeViewColumn(_('Fabricante'), render , text=2)

        tv_partitions.append_column(columna1)
        tv_partitions.append_column(columna2)

        tv_partitions.connect('cursor-changed', self.on_tv_partitions_cursor_changed)

        modelo = gtk.ListStore (    gobject.TYPE_INT ,    # autonumerico (oculto)
                gobject.TYPE_STRING,    # device
                gobject.TYPE_STRING)    # fabricante
        tv_partitions.set_model(modelo)

        return modelo

    def cargarParticionesModelo(self , modelo , listaParticiones):
        if listaParticiones:
            modelo.clear()
            i = 0
            for particion in listaParticiones:
                iterador = modelo.insert(i)
                modelo.set_value(iterador,0,i)
                cachos = particion.split(":")
                modelo.set_value(iterador,1,cachos[0])
                if ( len(cachos) > 1 ):
                    modelo.set_value(iterador,2,cachos[1])
                else:
                    modelo.set_value(iterador,2,"")
                i = i + 1

    def editar_idgame( self, renderEditable, i, nuevoIDGAME):
        if self.iteradorJuegoSeleccionado != None:
            actualIDGAME = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,1)
            if(actualIDGAME != nuevoIDGAME):
                if len(nuevoIDGAME) == 6:
                    if self.core.renombrarIDGAME(self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado , nuevoIDGAME):
                        # modificamos el juego modificado de la BDD
                        juego = session.query(Juego).filter('idgame=="%s" and device=="%s"' % (self.IDGAMEJuegoSeleccionado , self.DEVICEParticionSeleccionada)).first()
                        if juego != None:
                            juego.idgame = nuevoIDGAME

                            # Refrescamos del modelo la columna modificada
                            self.tv_games_modelo.set_value(self.iteradorJuegoSeleccionado,1,nuevoIDGAME)
                    else:
                        self.alert('error' , _("Error renombrando"))
                else:
                    self.alert('error' , _("Error: La longitud del IDGAME, debe ser 6."))

    def editar_celda( self, renderEditable, i, nuevoNombre):
        if self.iteradorJuegoSeleccionado != None:
            nombreActual = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,2)
            if(nombreActual != nuevoNombre):
                if not util.tieneCaracteresRaros(nuevoNombre , util.BLACK_LIST2):
                    if self.core.renombrarNOMBRE(self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado , nuevoNombre):
                        # modificamos el juego modificado de la BDD
                        juego = session.query(Juego).filter('idgame=="%s" and device=="%s"' % (self.IDGAMEJuegoSeleccionado , self.DEVICEParticionSeleccionada)).first()
                        if juego != None:
                            juego.title = nuevoNombre

                            # Refrescamos del modelo la columna modificada
                            self.tv_games_modelo.set_value(self.iteradorJuegoSeleccionado,2,nuevoNombre)
                    else:
                        self.alert('error' , _("Error renombrando"))
                else:
                    self.alert('error' , _("Se han detectado caracteres no validos: %s") % (util.BLACK_LIST2))

    def cargarJuegosVista(self):
        # Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
        tv_games = self.wb_tv_games
        
        # FIXME: ¿Porque no funciona?, especifico el entry de busqueda
        tv_games.set_search_entry( self.wb_busqueda )
        # activar busqueda desde el Treeview
        #tv_games.set_enable_search(True)

        # ¿Como aplico propiedades style?
        #tv_games.set_property("even-row-color" , gtk.gdk.Color(0xFFFF,0x0,0x0) )
        #tv_games.set_property("odd-row-color" ,   gtk.gdk.Color(0x0 , 0x0 , 0x0) )

        renderEditableIDGAME = gtk.CellRendererText()
        renderEditable = gtk.CellRendererText()
        if self.modo == "manager":
            renderEditableIDGAME.set_property("editable", True)
            renderEditableIDGAME.connect ("edited", self.editar_idgame)
            
            renderEditable.set_property("editable", True)
            renderEditable.set_property("attributes", self.getEstilo_azulGrande() )
            renderEditable.connect ("edited", self.editar_celda)
        else: # realmente en modo "ver", no es editable
            renderEditable.set_property("attributes", self.getEstilo_grisGrande() )
        render = gtk.CellRendererText()

        # prox versión meter background ----> foreground ... etc
        # http://www.pygtk.org/docs/pygtk/class-gtkcellrenderertext.html
        self.columna1 = columna1 = gtk.TreeViewColumn(_('IDGAME'), renderEditableIDGAME , text=1)
        self.columna2 = columna2 = gtk.TreeViewColumn(_('Nombre'), renderEditable , text=2)
        self.columna3 = columna3 = gtk.TreeViewColumn(_('Tamanio'), render , text=3)

        columna1.set_expand(False)
        columna1.set_min_width(80)
        columna1.set_reorderable(True)
        columna1.set_sort_order(gtk.SORT_DESCENDING)
        columna1.set_sort_column_id(1)

        columna2.set_expand(True)
        columna2.set_reorderable(True)
        columna2.set_sort_indicator(True)
        columna2.set_sort_order(gtk.SORT_DESCENDING)
        columna2.set_sort_column_id(2)

        columna3.set_expand(False)
        columna3.set_min_width(80)
        columna3.set_reorderable(True)
        columna3.set_sort_order(gtk.SORT_DESCENDING)
        columna3.set_sort_column_id(3)

        tv_games.append_column(columna1)
        tv_games.append_column(columna2)
        tv_games.append_column(columna3)

        tv_games.connect('cursor-changed', self.on_tv_games_cursor_changed)

        modelo = gtk.ListStore (    gobject.TYPE_INT ,      # orden (campo oculto)
                gobject.TYPE_STRING,                        # IDGAME
                gobject.TYPE_STRING,                        # Nombre
                gobject.TYPE_STRING,                        # Tamaño
                )
        tv_games.set_model(modelo)

        return modelo

    def cargarJuegosModelo(self , modelo , listaJuegos):
        modelo.clear()
        i = 0
        for juego in listaJuegos:
            iterador = modelo.insert(i)
            # El modelo tiene una columna más no representada
            modelo.set_value(iterador,0, i )
            modelo.set_value(iterador,1,                juego.idgame)
            modelo.set_value(iterador,2,                juego.title)
            modelo.set_value(iterador,3, "%.2f GB" %    juego.size)
            i = i + 1

    def salir(self , widget=None, data=None):
        # guardar campo clave de los seleccionados
        if self.DEVICEParticionSeleccionada != None:
            self.preferencia.device_seleccionado = self.DEVICEParticionSeleccionada
        if self.IDGAMEJuegoSeleccionado != None:
            self.preferencia.idgame_seleccionado = self.IDGAMEJuegoSeleccionado

        # guardar cambios en las preferencias
        session.commit()

        # cerrar gui
        gtk.main_quit()

        # cerrar hilos
        try:
            self.hiloAtenderMensajes.interrumpir()
            self.poolTrabajo.interrumpir()
            self.animar.interrumpir()
            self.animar.join()
            self.poolBash.join()
        except AttributeError:
            pass

    def alert(self, level, message):
        alert_glade = gtk.Builder()
        alert_glade.add_from_file( os.path.join(config.WIITHON_FILES_RECURSOS_GLADE  , 'alerta.ui') )
        alert_glade.set_translation_domain( config.APP )

        level_icons = {
                'question': gtk.STOCK_DIALOG_QUESTION,
                'info':     gtk.STOCK_DIALOG_INFO,
                'warning':  gtk.STOCK_DIALOG_WARNING,
                'error':    gtk.STOCK_DIALOG_ERROR,
                }

        level_buttons = {
                'question': (gtk.STOCK_YES, gtk.STOCK_NO),
                'info':     (gtk.STOCK_APPLY, None),
                'warning':  (gtk.STOCK_APPLY, None),
                'error':    (gtk.STOCK_CLOSE, None),
                }

        # configure the label text:
        alert_msg = alert_glade.get_object('lbl_message')
        alert_msg.set_text(message)

        # configure the icon to display
        img = alert_glade.get_object('img_alert')

        try:
            img.set_from_stock(level_icons[level], gtk.ICON_SIZE_DIALOG)
        except IndexError:
            img.set_from_stock(level_icons['info'], gtk.ICON_SIZE_DIALOG)

        # configure the buttons
        btn_ok = alert_glade.get_object('btn_ok')
        btn_no = alert_glade.get_object('btn_no')

        if level_buttons[level][0]:
            btn_ok.set_label(level_buttons[level][0])
        else:
            btn_ok.set_visible(False)

        if level_buttons[level][1]:
            btn_no.set_label(level_buttons[level][1])
        else:
            btn_no.hide()

        alert_glade.get_object(config.GLADE_ALERTA).set_title(level)
        res = alert_glade.get_object(config.GLADE_ALERTA).run()
        alert_glade.get_object(config.GLADE_ALERTA).hide()

        return res

    def question(self, pregunta):
        return self.alert('question', pregunta)

    # callback de la señal "changed" del buscador
    # Refresca de la base de datos y filtra según lo escrito.
    def on_busqueda_changed(self , widget):
        self.buscar = widget.get_text()
        self.refrescarListaJuegos()

    def refrescarListaJuegosFromBDD(self):
        self.listaJuegos = []
        for juego in session.query(Juego):
            self.listaJuegos.append( juego )
        self.refrescarListaJuegos()

    # refresco desde el disco duro (lento)
    def refrescarListaJuegosFromCore(self):
        # recargar el modelo de datos la lista de juegos
        self.listaJuegos = self.core.getListaJuegos( self.DEVICEParticionSeleccionada )

        # Eliminamos los devices de toda la bdd
        for juego in session.query(Juego):
            juego.device = ""

        # el core nos da una lista de tuplas de 3
        # lo convertimos a una lista de objetos Juego
        i = 0
        while i < len( self.listaJuegos ):
            # el core nos da
            tuplaJuego = self.listaJuegos[ i ]

            juego = session.query(Juego).filter( 'idgame=="%s"' % (tuplaJuego[0]) ).first()
            if juego == None:
                # es un juego nuevo, se guarda en la bdd
                juego = Juego(tuplaJuego[0] , tuplaJuego[1] , tuplaJuego[2] , self.DEVICEParticionSeleccionada)
                session.save( juego )
            else:
                #actualizo el device al que pertenece
                juego.title = tuplaJuego[1]
                # El tamaño no cambia
                #juego.size = float(tuplaJuego[2])
                juego.device = self.DEVICEParticionSeleccionada

            self.listaJuegos[ i ] = juego

            i += 1

        self.refrescarListaJuegos()
        
    # FIXME: Devuelve si el usuario esta editando el tv_games
    # sirve para evitar cambiar la selección mientras esta editando
    def get_usuario_esta_editando(self):
        return False

    # refresco desde memoria (rápido)
    def refrescarListaJuegos(self):
        subListaJuegos = []
        for juego in session.query(Juego).filter('device like "%s" and (title like "%%%s%%" or idgame like "%s%%")' % (self.DEVICEParticionSeleccionada , self.buscar , self.buscar)):
            subListaJuegos.append( juego )

        # cargar la lista sobre el Treeview
        self.cargarJuegosModelo( self.tv_games_modelo , subListaJuegos )

        if not self.get_usuario_esta_editando():
            # seleccionamos el primero
            # FIXME: hay que seleccionar el que marca las preferencias
            self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed)

    def seleccionarPrimeraFila(self , treeview , callback):
        # selecciono el primero y provoco el evento
        iter_primero = treeview.get_model().get_iter_first()
        if iter_primero != None:
            treeview.get_selection().select_iter( iter_primero )
        callback( treeview )

    def refrescarEspacio(self):
        info = self.core.getEspacioLibre( self.DEVICEParticionSeleccionada )
        usado = info[0]
        libre = info[1]
        total = info[2]
        self.wb_labelEspacio.set_text("%.2f GB / %.2f GB" % (usado , total))
        try:
            porcentaje = usado * 100.0 / total
        except ZeroDivisionError:
            porcentaje = 0.0
        self.wb_progresoEspacio.set_text("%d juegos" % (len(self.listaJuegos)))
        self.wb_progresoEspacio.set_fraction( porcentaje / 100.0 )

    def refrescarTareasPendientes(self):
        # La actual tarea no cuenta
        tareas_pendientes = self.poolTrabajo.numTrabajos - 1

        # singular y plural
        if tareas_pendientes == 1:
            self.wb_estadoTrabajo.set_text( _("Hay %d tarea pendiente") % tareas_pendientes)
            self.wb_estadoTrabajo.show()
        elif tareas_pendientes > 1:
            self.wb_estadoTrabajo.set_text( _("Hay %d tareas pendientes") % tareas_pendientes )
            self.wb_estadoTrabajo.show()
        else:
            self.wb_estadoTrabajo.hide()

    # Click en particiones --> refresca la lista de juegos
    def on_tv_partitions_cursor_changed(self , treeview):
        # particion seleccionado
        self.seleccionParticionSeleccionada, self.iteradorParticionSeleccionada  = self.wb_tv_partitions.get_selection().get_selected()
        if self.iteradorParticionSeleccionada != None:
            # establece en el core la nueva partición seleccionada
            self.core.setParticionSeleccionada( self.seleccionParticionSeleccionada.get_value(self.iteradorParticionSeleccionada,0) )

            # sincroniza la variable DEVICE con el core
            self.DEVICEParticionSeleccionada = self.core.getDeviceSeleccionado()

            # refrescamos la lista de juegos, leyendo del core
            self.refrescarListaJuegosFromCore()
            
            # refrescar espacio
            self.refrescarEspacio()

    # Click en juegos --> refresco la imagen de la caratula y disco
    def on_tv_games_cursor_changed(self , treeview):
        self.seleccionJuegoSeleccionado , self.iteradorJuegoSeleccionado = self.wb_tv_games.get_selection().get_selected()
        if self.iteradorJuegoSeleccionado != None:
            self.pathJuegoSeleccionado = int(self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,0))
            self.IDGAMEJuegoSeleccionado = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,1)

            destinoCaratula = os.path.join(config.HOME_WIITHON_CARATULAS , self.IDGAMEJuegoSeleccionado+".png")
            destinoDisco = os.path.join(config.HOME_WIITHON_DISCOS , self.IDGAMEJuegoSeleccionado+".png")
        else:
            destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
            destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")

        self.wb_img_caratula1.set_from_file( destinoCaratula )
        self.wb_img_disco1.set_from_file( destinoDisco )

    def on_tb_toolbar_clicked(self , id_tb):
        if(self.modo == "ver" and id_tb != self.wb_tb_copiar_SD and id_tb != self.wb_tb_acerca_de):
            self.alert("warning" , _("Tienes que seleccionar una particion WBFS para realizar esta accion"))
        elif(id_tb == self.wb_tb_acerca_de):
            self.wb_aboutdialog.run()
            self.wb_aboutdialog.hide()
        elif(id_tb == self.wb_tb_copiar_1_1):
            if self.numParticiones > 1:
                self.wb_dialogo_copia_1on1.run()
                self.wb_dialogo_copia_1on1.hide()
            else:
                self.alert("warning" , _("No hay un numero suficiente de particiones validas, para realizar esta accion."))
        elif(id_tb == self.wb_tb_borrar):
            if self.iteradorJuegoSeleccionado != None:
                if ( self.question(_('Quieres borrar el juego con ID = %s?') % self.IDGAMEJuegoSeleccionado) == 1 ):
                    # borrar del HD
                    if self.core.borrarJuego( self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado ):

                        # borrar de la tabla
                        self.tv_games_modelo.remove( self.iteradorJuegoSeleccionado )

                        # seleccionar el primero
                        self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed )

                        # debería haber liberado espacio
                        # FIXME: pequeño bug
                        self.refrescarEspacio()
                    else:
                        self.alert("warning" , _("Error borrando"))
            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))
        elif(id_tb == self.wb_tb_extraer):
            if self.iteradorJuegoSeleccionado != None:
                botones = (
                        gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK,
                        )

                fc_extraer = gtk.FileChooserDialog(_('Elige un directorio donde extraer la ISO de %s') % (self.IDGAMEJuegoSeleccionado), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                fc_extraer.set_default_response(gtk.RESPONSE_OK)
                fc_extraer.set_local_only(True)
                fc_extraer.set_current_folder( self.preferencia.ruta_extraer_iso )
                fc_extraer.show()

                if ( fc_extraer.run() == gtk.RESPONSE_OK ):

                    self.preferencia.ruta_extraer_iso = fc_extraer.get_current_folder()

                    self.core.setDestinoExtraer( fc_extraer.get_filenames() )
                    '''
                    Tarea EXTRAER JUEGO
                    '''
                    self.poolTrabajo.nuevoTrabajoExtraer( self.IDGAMEJuegoSeleccionado )
                    self.refrescarTareasPendientes()

                fc_extraer.destroy()
            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))
        elif(id_tb == self.wb_tb_renombrar):
            if self.iteradorJuegoSeleccionado != None:
                # Obtiene el foco
                self.wb_tv_games.grab_focus()
                # Editar celda
                self.wb_tv_games.set_cursor( self.pathJuegoSeleccionado , self.columna2 , True )
            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))
        elif(id_tb == self.wb_tb_anadir or id_tb == self.wb_tb_anadir_directorio):
            if self.iteradorParticionSeleccionada != None:

                botones = (gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK,
                        )

                if(id_tb == self.wb_tb_anadir):
                    fc_anadir = gtk.FileChooserDialog(_("Elige una ISO o un RAR"), None , gtk.FILE_CHOOSER_ACTION_OPEN , botones)
                    fc_anadir.set_select_multiple(True)
                    filter = gtk.FileFilter()
                    filter.set_name(_('Imagen ISO, Comprimido RAR'))
                    filter.add_pattern('*.iso')
                    filter.add_pattern('*.rar')
                    fc_anadir.add_filter(filter)
                    fc_anadir.set_current_folder( self.preferencia.ruta_anadir )

                elif(id_tb == self.wb_tb_anadir_directorio):
                    fc_anadir = gtk.FileChooserDialog(_("Elige un directorio"), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                    fc_anadir.set_current_folder( self.preferencia.ruta_anadir_directorio )

                fc_anadir.set_default_response(gtk.RESPONSE_OK)
                fc_anadir.set_local_only(True)

                if fc_anadir.run() == gtk.RESPONSE_OK:
                    '''
                    Tarea AÑADIR JUEGO
                    '''
                    if(id_tb == self.wb_tb_anadir):
                        self.preferencia.ruta_anadir = fc_anadir.get_current_folder()
                    elif(id_tb == self.wb_tb_anadir_directorio):
                        self.preferencia.ruta_anadir_directorio = fc_anadir.get_current_folder()

                    ficherosSeleccionados = fc_anadir.get_filenames()

                    #Ordenamos los ficheros seleccionados
                    ficherosSeleccionados.sort()
                    
                    '''
                    for fichero in ficherosSeleccionados:
                        if (util.getExtension(fichero) == "iso"):
                            IDGAME = util.getMagicISO(fichero)
                            if IDGAME != None:
                                self.poolBash.nuevoTrabajoDescargaCaratula( IDGAME )
                                self.poolBash.nuevoTrabajoDescargaDisco( IDGAME )
                    '''

                    self.poolTrabajo.nuevoTrabajoAnadir( ficherosSeleccionados )
                    self.refrescarTareasPendientes()

                fc_anadir.destroy()
            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

        elif(id_tb == self.wb_tb_copiar_SD):
            if self.iteradorJuegoSeleccionado != None:
                botones = (
                        gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK,
                        )

                fc_copiar_SD = gtk.FileChooserDialog(_('Paso 1 de 2: Elige un directorio para las CARATULAS'), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                fc_copiar_SD.set_default_response(gtk.RESPONSE_OK)
                fc_copiar_SD.set_local_only(True)
                fc_copiar_SD.set_current_folder( self.preferencia.ruta_copiar_caratulas )
                fc_copiar_SD.show()

                if ( fc_copiar_SD.run() == gtk.RESPONSE_OK ):
                    fc_copiar_discos_SD = gtk.FileChooserDialog(_('Paso 2 de 2: Elige un directorio para los DISCOS'), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                    fc_copiar_discos_SD.set_default_response(gtk.RESPONSE_OK)
                    fc_copiar_discos_SD.set_local_only(True)
                    fc_copiar_discos_SD.set_current_folder( self.preferencia.ruta_copiar_discos )
                    fc_copiar_discos_SD.show()
                    if(fc_copiar_discos_SD.run() == gtk.RESPONSE_OK):
                        self.preferencia.ruta_copiar_caratulas = fc_copiar_SD.get_current_folder()
                        self.preferencia.ruta_copiar_discos = fc_copiar_discos_SD.get_current_folder()

                        self.core.setDestinoCopiarCaratula( fc_copiar_SD.get_filenames() )
                        self.core.setDestinoCopiarDisco( fc_copiar_discos_SD.get_filenames() )

                        for juego in self.listaJuegos:
                            self.poolBash.nuevoTrabajoCopiarCaratula( juego.idgame )
                            self.poolBash.nuevoTrabajoCopiarDisco( juego.idgame )

                    fc_copiar_discos_SD.destroy()

                fc_copiar_SD.destroy()
            else:
                self.alert("warning" , _("No tienes ningun juego"))

class HiloAtenderMensajes(Thread):

    def __init__(self , core , hilo , progreso , gui):
        Thread.__init__(self)
        self.core = core
        self.hilo = hilo
        self.progreso = progreso
        self.gui = gui
        self.interrumpido = False
        self.timer = 0
        self.hiloCalcularProgreso = None

    def run(self):
        cola = self.core.getMensajes()
        while not self.interrumpido:
            if self.hilo.numTrabajos > 0:
                objMensaje = cola.get()

                # Refrescar tareas pendientes
                gobject.idle_add( self.refrescarTareasPendientes )

                # hay trabajo
                gobject.idle_add( self.mostrarHBoxProgreso )

                tipo = objMensaje.getTipo()
                mensaje = objMensaje.getMensaje()

                # Todo esto hay que rehacerlo, definar BIEN los comandos entre GUI <---> POOL de trabajo
                if( tipo == "INFO" ):
                    gobject.idle_add(self.actualizarLabel , mensaje)
                elif( tipo == "WARNING" ):
                    gobject.idle_add(self.actualizarLabel ,_( "CUIDADO: %s" % mensaje ))
                elif( tipo == "ERROR" ):
                    gobject.idle_add(self.actualizarLabel , _( "ERROR: %s" % mensaje ))
                elif( tipo == "COMANDO" ):
                    if(mensaje == "EMPIEZA"):
                        termino = False
                    elif(mensaje == "TERMINA"):
                        termino = True
                    elif(mensaje == "PROGRESO_INICIA_CALCULO"):
                        hiloCalcularProgreso = HiloCalcularProgreso( self.actualizarLabel , self.actualizarFraccion )
                        hiloCalcularProgreso.setDaemon(True)
                        hiloCalcularProgreso.start()
                    elif(mensaje == "PROGRESO_FIN_CALCULO"):
                        if( self.hiloCalcularProgreso!= None and self.hiloCalcularProgreso.isAlive() ):
                            self.hiloCalcularProgreso.interrumpir()
                            self.hiloCalcularProgreso.join()
                            self.hiloCalcularProgreso = None
                    elif(mensaje == "PROGRESO_0"):
                        gobject.idle_add(self.actualizarFraccion , 0.0 )
                    elif(mensaje == "PROGRESO_100"):
                        gobject.idle_add(self.actualizarFraccion , 1.0 )
                    elif(mensaje == "REFRESCAR_JUEGOS"):
                        gobject.idle_add(self.refrescarJuegosFromCore)
                    else:
                        raise AssertionError, _("DEBUG: Comando desconocido")
                cola.task_done()

                # atiendo la cola
                time.sleep(0.10)

                if((self.hilo.numTrabajos == 0) and termino):
                    gobject.timeout_add( 3000, self.ocultarHBoxProgreso )
            else:
                # FIXME : usar wait o algo así
                # el trabajador debería esperar (sin espera activa)
                # hasta que sea requerido
                time.sleep(0.2)

    def actualizarLabel( self, etiqueta ):
        self.progreso.set_text( etiqueta )

    def actualizarFraccion( self , fraccion ):
        self.progreso.set_fraction( fraccion )

    def ocultarHBoxProgreso(self):
        self.gui.wb_box_progreso.hide()
        # Para que no se repita
        return False

    def mostrarHBoxProgreso(self):
        self.gui.wb_box_progreso.show()

    def refrescarTareasPendientes(self):
        self.gui.refrescarTareasPendientes()

    # el callback de AÑADIR un juego es refrescar
    # FIXME: quitar gui como parametro, pasar mejor un callback para cada vez que acaba un trabajo
    def refrescarJuegosFromCore(self):
        self.gui.refrescarListaJuegosFromCore()
        self.gui.refrescarEspacio()

    def interrumpir(self):
        self.interrumpido = True
        if self.hiloCalcularProgreso != None:
            self.hiloCalcularProgreso.interrumpir()

class HiloCalcularProgreso(Thread):
    def __init__(self , actualizarLabel , actualizarFraccion):
        Thread.__init__(self)
        self.actualizarLabel = actualizarLabel
        self.actualizarFraccion = actualizarFraccion
        self.interrumpido = False
        self.porcentaje = 0.0

    def run(self):
        while not self.interrumpido:
            try:
                ultimaLinea = util.getSTDOUT("tail %s -n 1" % config.HOME_WIITHON_LOGS_PROCESO)
                cachos = ultimaLinea.split(";")

                if cachos[0] == "FIN":
                    porcentaje = 100
                    informativo = _("Finalizando. Hecho en")
                    self.interrumpir()
                else:
                    porcentaje = self.porcentaje = float(cachos[0])
                    informativo = _("quedan")

                hora = int(cachos[1])
                minutos = int(cachos[2])
                segundos = int(cachos[3])

                if(hora > 0):
                    gobject.idle_add(self.actualizarLabel , "%d%% - %s %dh%dm%ds" % ( porcentaje , informativo , hora , minutos , segundos ))
                elif(minutos > 0):
                    gobject.idle_add(self.actualizarLabel , "%d%% - %s %dm%ds" % ( porcentaje , informativo , minutos , segundos ))
                else:
                    gobject.idle_add(self.actualizarLabel , "%d%% - %s %ds" % ( porcentaje, informativo , segundos ))

                porcentual = porcentaje / 100.0
                gobject.idle_add(self.actualizarFraccion , porcentual )
            except ValueError:
                pass
            time.sleep(1)

    def interrumpir(self):
        self.interrumpido = True

