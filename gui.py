#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import time
import sys
import re
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

    ui_desc = '''
<ui>
    <popup action="GamePopup">
      <menuitem action="Renombrar"/>
      <menuitem action="Extraer"/>
      <menuitem action="Copiar"/>
      <separator/>
      <menuitem action="Borrar"/>
    </popup>
</ui>
'''

    def __init__(self, core):
        GtkBuilderWrapper.__init__(self,
                                   os.path.join(config.WIITHON_FILES_RECURSOS_GLADE,
                                                'wiithon.ui'))

        self.core = core
        self.buscar = ""
        self.modo = "desconocido" # desconocido | ver | manager

        self.preferencia = session.query(Preferencia).first()
        # Nunca se han creado preferencias
        if self.preferencia == None:
            self.preferencia = Preferencia()
            session.save( self.preferencia )
            session.commit()

        # Menu contextual
        self.uimgr = gtk.UIManager()

        accelgroup = self.uimgr.get_accel_group()
        self.wb_principal.add_accel_group(accelgroup)

        actiongroup = gtk.ActionGroup('LeftButtonGroup')

        actiongroup.add_actions([
                ('Renombrar', None, _('Renombrar'), None, '',
                 self.menu_contextual_renombrar),

                ('Extraer', None, _('Extraer'), None, '',
                 self.menu_contextual_extraer),

                ('Copiar', None, _('Copiar a otra particion'), None,
                 '', self.menu_contextual_copiar),

                ('Borrar', gtk.STOCK_DELETE, None, None, '',
                 self.menu_contextual_borrar),
                ])

        self.uimgr.insert_action_group(actiongroup)

        self.uimgr.add_ui_from_string(self.ui_desc)
        self.wb_tv_games.connect('button-press-event', self.on_tv_games_click_event)

        # TEST
        self.wb_principal.drag_dest_set(0, [], 0)
                                        #[('text/uri-list', gtk.TARGET_OTHER_APP, 25)],
                                        #gtk.gdk.ACTION_DEFAULT)

        self.wb_principal.connect("drag_motion", self.drop_motion)
        self.wb_principal.connect("drag_drop", self.drag_drop)
        self.wb_principal.connect("drag_data_received", self.drag_data_received_cb)
        # /TEST

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

        # Referencia copia a la lista de juegos
        self.listaJuegos = None

        #
        self.pathJuegoSeleccionado = None
        # gtk.ListStore
        self.seleccionJuegoSeleccionado = None
        # GtkTreeIter
        self.iteradorJuegoSeleccionado = None
        # RXG99F
        self.IDGAMEJuegoSeleccionado = ""
        # referencia al objeto de la fila seleccionada
        self.juego = None

        # gtk.ListStore
        self.seleccionParticionSeleccionada = None
        # GtkTreeIter
        self.iteradorParticionSeleccionada = None
        # /dev/sda1
        self.DEVICEParticionSeleccionada = ""

        self.seleccionParticionSeleccionada_1on1 = None
        self.iteradorParticionSeleccionada_1on1 = None
        self.DEVICEParticionSeleccionada_1on1 = ""

        # permite usar hilos con PyGTK http://faq.pygtk.org/index.py?req=show&file=faq20.006.htp
        # modo seguro con hilos
        gobject.threads_init()

        self.wb_principal.set_title('Wiithon')
        # FIXME: Hacer otro icono pequeño
        # self.wb_principal.set_icon_from_file( "/usr/share/pixmaps/wiithon.svg" )
        self.wb_principal.show()

        # conexion señales de la toolbar
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
        self.tv_partitions_modelo = self.cargarParticionesVista(self.wb_tv_partitions, self.on_tv_partitions_cursor_changed)

        destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")
        self.wb_estadoBatch.set_from_file( destinoIcono )

        '''
        if os.geteuid() != 0:
            self.alert("error" , _("REQUIERE_ROOT") % (config.APP , config.APP) )
            raise AssertionError, _("Error en permisos")
        '''

        # trabajos LIGEROS
        self.poolBash = PoolTrabajo( self.core , 6)
        self.poolBash.setDaemon(True)
        self.poolBash.start()

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

            # carga la Vista para las particiones de la copia 1on1
            self.tv_partitions2_modelo = self.cargarParticionesVista(self.wb_tv_partitions2, self.on_tv_partitions2_cursor_changed)

            # carga el modelo de datos del TreeView de particiones
            self.cargarParticionesModelo(self.tv_partitions_modelo , self.listaParticiones)

            # selecciono la primera partición
            # indirectamente se carga:
            # lee el modelo de datos de la partición seleccionada
            # tambien refresca la lista de juegos del CORE
            self.seleccionarPrimeraFila( self.wb_tv_partitions , self.on_tv_partitions_cursor_changed)

            # Trabajador, se le mandan trabajos de barra de progreso (trabajos INTENSOS)
            self.poolTrabajo = PoolTrabajo( self.core , 1,
                                        self.callback_empieza_trabajo ,
                                        self.callback_termina_trabajo ,
                                        self.callback_nuevo_trabajo ,
                                        self.callback_empieza_trabajo_anadir,
                                        self.callback_termina_trabajo_anadir,
                                        self.callback_empieza_progreso,
                                        self.callback_termina_progreso,
                                        self.callback_empieza_trabajo_extraer,
                                        self.callback_termina_trabajo_extraer,
                                        self.callback_empieza_trabajo_copiar,
                                        self.callback_termina_trabajo_copiar
                                        )
            self.poolTrabajo.setDaemon(True)
            self.poolTrabajo.start()

        self.animar = Animador( self.wb_estadoBatch , self.poolBash , self.poolTrabajo)
        self.animar.setDaemon(True)
        self.animar.start()

        # si no hay juegos pongo las caratulas por defecto
        if len(self.listaJuegos) == 0:
            destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
            destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
            self.wb_img_caratula1.set_from_file( destinoCaratula )
            self.wb_img_disco1.set_from_file( destinoDisco )

        # pongo el foco en el buscador
        self.wb_busqueda.grab_focus()

    def main(self , opciones , argumentos):

        for arg in argumentos:
            arg = os.path.abspath(arg)
            if os.path.exists(arg):
                if util.getExtension(arg)=="iso":
                    self.poolTrabajo.nuevoTrabajoAnadir( arg , self.DEVICEParticionSeleccionada)
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

    def menu_contextual_renombrar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_renombrar )

    def menu_contextual_extraer(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_extraer )

    def menu_contextual_copiar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_copiar_1_1 )

    def menu_contextual_borrar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_borrar )

    def cargarParticionesVista(self, treeview, callback_cursor_changed):
        render = gtk.CellRendererText()

        columna1 = gtk.TreeViewColumn(_('Dispositivo'), render , text=1)
        columna2 = gtk.TreeViewColumn(_('Fabricante'), render , text=2)

        treeview.append_column(columna1)
        treeview.append_column(columna2)

        treeview.connect('cursor-changed', callback_cursor_changed)

        modelo = gtk.ListStore (
                gobject.TYPE_INT ,    # autonumerico (oculto)
                gobject.TYPE_STRING,    # device
                gobject.TYPE_STRING)    # fabricante
        treeview.set_model(modelo)

        return modelo

    def cargarParticionesModelo(self , modelo , listaParticiones , insertarDeviceSeleccionado = True):
        if listaParticiones:
            modelo.clear()
            i = 0
            for particion in listaParticiones:
                cachos = particion.split(":")
                if(cachos[0] != self.DEVICEParticionSeleccionada or insertarDeviceSeleccionado):
                    iterador = modelo.insert(i)
                    modelo.set_value(iterador,0,i)
                    modelo.set_value(iterador,1,cachos[0])
                    if ( len(cachos) > 1 ):
                        modelo.set_value(iterador,2,cachos[1])
                    else:
                        modelo.set_value(iterador,2,"")
                # el contador esta fuera del if debido a:
                # si lo metemos la numeracion es secuencial, pero cuando insertarDeviceSeleccionado sea False
                # quiero reflejar los huecos. Esto permite un alineamiento con la lista del core
                i = i + 1

    def editar_idgame( self, renderEditable, i, nuevoIDGAME):
        if self.iteradorJuegoSeleccionado != None:
            nuevoIDGAME = nuevoIDGAME.upper()
            if(self.IDGAMEJuegoSeleccionado != nuevoIDGAME):
                exp_reg = "[A-Z0-9]{6}"
                if re.match(exp_reg,nuevoIDGAME):
                    juego = session.query(Juego).filter('idgame=="%s" and device=="%s"' % (nuevoIDGAME , self.DEVICEParticionSeleccionada)).first()
                    if juego == None:
                        if ( self.question(_('Advertencia de seguridad de renombrar desde IDGAME = %s a %s') % (self.IDGAMEJuegoSeleccionado , nuevoIDGAME)) == 1 ):
                            if self.core.renombrarIDGAME(self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado , nuevoIDGAME):
                                # modificamos el juego modificado de la BDD
                                if self.juego != None:
                                    self.juego.idgame = nuevoIDGAME

                                    # Refrescamos del modelo la columna modificada
                                    self.tv_games_modelo.set_value(self.iteradorJuegoSeleccionado ,1 ,nuevoIDGAME)
                            else:
                                self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Ya hay un juego con ese IDGAME"))
                else:
                    self.alert('error' , _("Error: La longitud del IDGAME debe ser 6, y solo puede contener letras y numeros"))

    def editar_nombre( self, renderEditable, i, nuevoNombre):
        if self.iteradorJuegoSeleccionado != None:
            nombreActual = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,2)
            if(nombreActual != nuevoNombre):
                if len(nuevoNombre) < config.TITULO_LONGITUD_MAX:
                    if not util.tieneCaracteresRaros(nuevoNombre , util.BLACK_LIST2):
                        if self.core.renombrarNOMBRE(self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado , nuevoNombre):
                            if self.juego != None:
                                self.juego.title = nuevoNombre
                                # Refrescamos del modelo la columna modificada
                                self.tv_games_modelo.set_value(self.iteradorJuegoSeleccionado,2,nuevoNombre)
                        else:
                            self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Se han detectado caracteres no validos: %s") % (util.BLACK_LIST2))
                else:
                    self.alert('error' , _("Nuevo nombre es demasiado largo, intente con un texto menor de %d caracteres") % (config.TITULO_LONGITUD_MAX))

    def cargarJuegosVista(self):
        # Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
        tv_games = self.wb_tv_games

        # FIXME: ¿Porque no funciona?, especifico el entry de busqueda
        #tv_games.set_search_entry( self.wb_busqueda )
        # activar busqueda desde el Treeview
        tv_games.set_enable_search(True)

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
            renderEditable.connect ("edited", self.editar_nombre)
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

        # guardar cambios en las preferencias
        session.commit()

        # cerrar gui
        gtk.main_quit()

        # cerrar hilos
        try:
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
                # el nombre puede ser otro aunque tenga el mismo IDGAME (cambiado desde otra gestor por ejemplo)
                juego.title = tuplaJuego[1]

                # previamente se limpiaron los devices
                juego.device = self.DEVICEParticionSeleccionada

            self.listaJuegos[ i ] = juego

            i += 1

        session.commit()
        self.refrescarListaJuegos()

    # FIXME: Devuelve si el usuario esta editando el tv_games
    # sirve para evitar cambiar la selección mientras esta editando
    def get_usuario_esta_editando(self):
        return False

    # refresco desde memoria (rápido)
    def refrescarListaJuegos(self):
        subListaJuegos = []

        # ordenado por nombre, insensible a mayusculas
        for juego in session.query(Juego).filter('device like "%s" and (title like "%%%s%%" or idgame like "%s%%")' % (self.DEVICEParticionSeleccionada , self.buscar , self.buscar)).order_by('lower(title)'):
            subListaJuegos.append( juego )

        # cargar la lista sobre el Treeview
        self.cargarJuegosModelo( self.tv_games_modelo , subListaJuegos )

        if not self.get_usuario_esta_editando():
            # seleccionamos el primero
            # FIXME: hay que seleccionar el que marca las preferencias
            self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed)

    def seleccionarFilaConValor(self , treeview, numFilas , columna, valor, callback):
        i = 0
        encontrado = False
        while (i<numFilas) and (not encontrado):
            iter = treeview.get_model().get_iter(i)
            iter_valor = treeview.get_model().get_value(iter , columna)
            encontrado = (iter_valor == valor)
            if not encontrado:
                i += 1
        if encontrado:
            treeview.get_selection().select_path(i)
        # provoca el evento de cambio en el treeview
        callback( treeview )

    def seleccionarPrimeraFila(self , treeview , callback):
        # selecciono el primero y provoco el evento
        iter_primero = treeview.get_model().get_iter_first()
        if iter_primero != None:
            treeview.get_selection().select_iter( iter_primero )
        # provoca el evento de cambio en el treeview
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
        numTareas = self.poolTrabajo.numTrabajos

        if numTareas == 0:
            self.wb_estadoTrabajo.hide()
        else:
            if(numTareas == 1):
                etiqueta = _("Hay %d tarea") % (numTareas)
            else:
                etiqueta = _("Hay %d tareas") % (numTareas)
            self.wb_estadoTrabajo.set_label(etiqueta)
            self.wb_estadoTrabajo.show()

    # Click en particiones --> refresca la lista de juegos
    def on_tv_partitions_cursor_changed(self , treeview):
        # particion seleccionado
        self.seleccionParticionSeleccionada, self.iteradorParticionSeleccionada  = treeview.get_selection().get_selected()
        if self.iteradorParticionSeleccionada != None:
            # establece en el core la nueva partición seleccionada
            self.core.setParticionSeleccionada( self.seleccionParticionSeleccionada.get_value(self.iteradorParticionSeleccionada,0) )

            # sincroniza la variable DEVICE con el core
            self.DEVICEParticionSeleccionada = self.core.getDeviceSeleccionado()

            # refrescamos el modelo de particiones para la copia 1on1
            self.cargarParticionesModelo(self.tv_partitions2_modelo , self.listaParticiones , False)
            self.seleccionarPrimeraFila( self.wb_tv_partitions2 , self.on_tv_partitions2_cursor_changed)

            # refrescamos la lista de juegos, leyendo del core
            self.refrescarListaJuegosFromCore()

            # descargar caratulas de todos los juegos de la NUEVA lista de juegos
            self.poolBash.nuevoTrabajoDescargaCaratula( self.listaJuegos )
            self.poolBash.nuevoTrabajoDescargaDisco( self.listaJuegos )

            # refrescar espacio
            self.refrescarEspacio()

    def on_tv_partitions2_cursor_changed(self , treeview):
        # particion seleccionado
        self.seleccionParticionSeleccionada_1on1, self.iteradorParticionSeleccionada_1on1  = treeview.get_selection().get_selected()
        if self.iteradorParticionSeleccionada_1on1 != None:
            # establece en el core la nueva partición seleccionada para 1on1
            self.core.setParticionSeleccionada_1on1( self.seleccionParticionSeleccionada_1on1.get_value(self.iteradorParticionSeleccionada_1on1,0) )

            # sincroniza la variable con el core
            self.DEVICEParticionSeleccionada_1on1 = self.core.getDeviceSeleccionado_1on1()

    # Click en juegos --> refresco la imagen de la caratula y disco
    # self.wb_tv_games
    def on_tv_games_cursor_changed(self , treeview):
        self.seleccionJuegoSeleccionado , self.iteradorJuegoSeleccionado = treeview.get_selection().get_selected()
        if self.iteradorJuegoSeleccionado != None:
            self.pathJuegoSeleccionado = int(self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,0))
            self.IDGAMEJuegoSeleccionado = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,1)
            self.juego = session.query(Juego).filter('idgame=="%s" and device=="%s"' % (self.IDGAMEJuegoSeleccionado , self.DEVICEParticionSeleccionada)).first()

            destinoCaratula = os.path.join(config.HOME_WIITHON_CARATULAS , self.IDGAMEJuegoSeleccionado+".png")
            destinoDisco = os.path.join(config.HOME_WIITHON_DISCOS , self.IDGAMEJuegoSeleccionado+".png")
        else:
            destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
            destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")

        self.wb_img_caratula1.set_from_file( destinoCaratula )
        self.wb_img_disco1.set_from_file( destinoDisco )

    def on_tv_games_click_event(self, widget, event):
        if event.button == 3:
            popup = self.uimgr.get_widget('/GamePopup')
            popup.popup(None, None, None, event.button, event.time)

    def on_tb_toolbar_clicked(self , id_tb):
        if(self.modo == "ver" and id_tb != self.wb_tb_copiar_SD and id_tb != self.wb_tb_acerca_de and id_tb != self.wb_tb_borrar):
            self.alert("warning" , _("Tienes que seleccionar una particion WBFS para realizar esta accion"))

        elif(id_tb == self.wb_tb_acerca_de):
            self.wb_aboutdialog.run()
            self.wb_aboutdialog.hide()

        elif(id_tb == self.wb_tb_copiar_1_1):
            if self.numParticiones > 1:
                res = self.wb_dialogo_copia_1on1.run()
                self.wb_dialogo_copia_1on1.hide()

                if(res == 1):
                    if self.juego != None:
                        print _("Copiar el juego %s a la particion %s") % (self.juego.title , self.DEVICEParticionSeleccionada_1on1)
                        self.poolTrabajo.nuevoTrabajoClonar( self.juego, self.DEVICEParticionSeleccionada_1on1)

                    else:
                        self.alert("warning" , _("No has seleccionado ningun juego"))

                elif(res == 2):
                    print _("Copiar todos los juegos a la particion %s") % (self.DEVICEParticionSeleccionada_1on1)
                    self.alert('error' , "Sin implementar aun")

            else:
                self.alert("warning" , _("No hay un numero suficiente de particiones validas, para realizar esta accion."))

        elif(id_tb == self.wb_tb_borrar):
            if self.iteradorJuegoSeleccionado != None:
                if self.modo == "ver":
                    if ( self.question(_('Advertencia de borrar %s en modo ver') % self.IDGAMEJuegoSeleccionado) == 1 ):
                        if self.juego != None:
                            # borrar disco
                            self.core.borrarDisco( self.juego )

                            # borrar caratula
                            self.core.borrarCaratula( self.juego )

                            # borrar de la bdd
                            session.delete( self.juego )

                            # borrar de la tabla
                            self.tv_games_modelo.remove( self.iteradorJuegoSeleccionado )

                            # seleccionar el primero
                            self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed )

                else:
                    if ( self.question(_('Quieres borrar el juego con %s (%s)?') % (self.juego.title , self.juego.idgame)) == 1 ):
                        # borrar del HD
                        if self.core.borrarJuego( self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado ):

                            # borrar de la tabla
                            self.tv_games_modelo.remove( self.iteradorJuegoSeleccionado )

                            # seleccionar el primero
                            self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed )

                            '''
                            # como no refresco toda la lista, al menos borro el elemento
                            try:
                                self.listaJuegos.remove( self.juego )
                            except ValueError:
                                pass
                            '''

                            # debería haber liberado espacio
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

                fc_extraer = gtk.FileChooserDialog(
                    _('Elige un directorio donde extraer la ISO de %s') \
                        %(self.IDGAMEJuegoSeleccionado), None,
                    gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, botones)

                fc_extraer.set_default_response(gtk.RESPONSE_OK)
                fc_extraer.set_local_only(True)
                fc_extraer.set_current_folder( self.preferencia.ruta_extraer_iso )
                fc_extraer.show()

                if ( fc_extraer.run() == gtk.RESPONSE_OK ):

                    # nueva ruta favorita
                    self.preferencia.ruta_extraer_iso = fc_extraer.get_current_folder()

                    # extraer *juego* en la ruta seleccionada
                    self.poolTrabajo.nuevoTrabajoExtraer( self.juego , fc_extraer.get_filename() )

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

                    # ordenar la ruta de archivos
                    ficherosSeleccionados.sort()

                    self.poolTrabajo.nuevoTrabajoAnadir( ficherosSeleccionados , self.DEVICEParticionSeleccionada)

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

                        # copiar toda la lista de juegos
                        self.poolBash.nuevoTrabajoCopiarCaratula( self.listaJuegos, fc_copiar_SD.get_filename() )
                        self.poolBash.nuevoTrabajoCopiarDisco( self.listaJuegos, fc_copiar_discos_SD.get_filename() )

                    fc_copiar_discos_SD.destroy()

                fc_copiar_SD.destroy()

            else:
                self.alert("warning" , _("No tienes ningun juego"))

############# METODOS que modifican el GUI, si se llaman desde hilos, se hacen con gobject

    def ocultarHBoxProgreso(self):
        self.wb_box_progreso.hide()
        return False

    def mostrarHBoxProgreso(self):
        self.wb_box_progreso.show()

    def actualizarLabel( self, etiqueta ):
        self.wb_progreso1.set_text( etiqueta )

    def actualizarFraccion( self , fraccion ):
        self.wb_progreso1.set_fraction( fraccion )

    def refrescarJuegosYSeleccionarElNuevo(self, idgame):
        #self.refrescarListaJuegosFromCore()
        #self.refrescarEspacio()
        self.seleccionarFilaConValor(self.wb_tv_games, len(self.listaJuegos) , 1 , idgame, self.on_tv_games_cursor_changed)

    def refrescarParticionesYSeleccionarJuegoClonado(self, IDGAME, DEVICE):
        self.seleccionarFilaConValor(self.wb_tv_partitions, self.numParticiones , 1 , DEVICE, self.on_tv_partitions_cursor_changed)
        self.seleccionarFilaConValor(self.wb_tv_games, len(self.listaJuegos) , 1 , IDGAME, self.on_tv_games_cursor_changed)

############# CALLBACKS

    def drag_drop(self, widget, drag_context, x, y, timestamp):
        widget.drag_get_data(drag_context, "text/uri-list")
        drag_context.finish(True, False, timestamp)

    def drop_motion(self, widget, drag_context, x, y, timestamp):
        drag_context.drag_status(gtk.gdk.ACTION_COPY, timestamp)
        return True

    def drag_data_received_cb(self, widget, drag_context, x, y, selection_data, info, timestamp):
        'Callback invoked when the DnD data is received'
        tuplaArrastrados = selection_data.get_uris()
        listaArrastrados = []
        for fichero in tuplaArrastrados:
            listaArrastrados.append(fichero.replace("file://" , ""))
        listaArrastrados.sort()
        if self.poolTrabajo:
            self.poolTrabajo.nuevoTrabajoAnadir(listaArrastrados, self.DEVICEParticionSeleccionada)

    def callback_empieza_progreso(self, trabajo):
        self.hiloCalcularProgreso = HiloCalcularProgreso( trabajo, self.actualizarLabel , self.actualizarFraccion )
        self.hiloCalcularProgreso.start()
        gobject.idle_add(self.actualizarFraccion , 0.0 )
        print "empezar progreso"

    def callback_termina_progreso(self, trabajo):
        self.hiloCalcularProgreso.progreso = 100
        gobject.idle_add(self.actualizarFraccion , 1.0 )
        print "termina progreso"

    def callback_empieza_trabajo_anadir(self, trabajo):
        print "callback_empieza_trabajo_anadir"

    def callback_termina_trabajo_anadir(self, trabajo , idgame):
        print "callback_termina_trabajo_anadir"
        if trabajo.exito:
            gobject.idle_add( self.refrescarJuegosYSeleccionarElNuevo , idgame)

    def callback_nuevo_trabajo(self, trabajo):
        print "callback_nuevo_trabajo"
        gobject.idle_add( self.refrescarTareasPendientes )
        gobject.idle_add( self.mostrarHBoxProgreso )

    def callback_empieza_trabajo(self, trabajo):
        print "callback_empieza_trabajo"
        print _("Empieza %s") % trabajo

    def callback_termina_trabajo(self, trabajo):
        print _("Termina: %s") % trabajo
        # No hay trabajo cuando el contador este a 1, que es el propio trabajo que da la señal
        if(self.poolTrabajo.numTrabajos <= 1):
            gobject.timeout_add( 5000, self.ocultarHBoxProgreso )

    def callback_empieza_trabajo_extraer(self, trabajo):
        pass

    def callback_termina_trabajo_extraer(self, trabajo):
        pass

    def callback_empieza_trabajo_copiar(self, trabajo):
        pass

    # Al terminar hay que seleccionar la partición destino y el juego copiado
    def callback_termina_trabajo_copiar(self, trabajo, juego, DEVICE):
        gobject.idle_add( self.refrescarParticionesYSeleccionarJuegoClonado , juego.idgame , DEVICE)

class HiloCalcularProgreso(Thread):
    def __init__(self , trabajo, actualizarLabel , actualizarFraccion):
        Thread.__init__(self)
        self.trabajo = trabajo
        self.actualizarLabel = actualizarLabel
        self.actualizarFraccion = actualizarFraccion
        self.interrumpido = False
        self.porcentaje = 0.0
        try:
            os.remove ( config.HOME_WIITHON_LOGS_PROCESO )
        except OSError:
            pass

    def run(self):
        while not self.interrumpido:
            try:
                # si aún no existe el fichero que contiene los mensajes, esperamos:
                # a) a que el fichero exista
                # b) desde otro hilo nos den orden de interrupción
                if os.path.exists(config.HOME_WIITHON_LOGS_PROCESO):

                    try:
                        for linea in file(config.HOME_WIITHON_LOGS_PROCESO):
                            ultimaLinea = linea

                        cachos = ultimaLinea.split(";")

                        # FIN es un convenio que viene de la funcion "spinner" en libwbfs.c
                        if self.trabajo.terminado:
                            self.porcentaje = 100
                            if self.trabajo.exito:
                                informativo = _("Finalizado.")
                            else:
                                informativo = _("ERROR!")
                            gobject.idle_add(self.actualizarLabel , "%s - %d%% - %s" % ( self.trabajo , self.porcentaje, informativo ))
                            self.interrumpir()
                        else:
                            self.porcentaje = float(cachos[0])
                            informativo = _("quedan")

                            hora = int(cachos[1])
                            minutos = int(cachos[2])
                            segundos = int(cachos[3])

                            if(hora > 0):
                                gobject.idle_add(self.actualizarLabel , "%s - %d%% - %s %dh%dm%ds" % ( self.trabajo , self.porcentaje , informativo , hora , minutos , segundos ))
                            elif(minutos > 0):
                                gobject.idle_add(self.actualizarLabel , "%s - %d%% - %s %dm%ds" % ( self.trabajo , self.porcentaje , informativo , minutos , segundos ))
                            else:
                                gobject.idle_add(self.actualizarLabel , "%s - %d%% - %s %ds" % ( self.trabajo , self.porcentaje, informativo , segundos ))

                        porcentual = self.porcentaje / 100.0
                        gobject.idle_add(self.actualizarFraccion , porcentual )

                    except UnboundLocalError:
                        gobject.idle_add(self.actualizarLabel , _("Empezando ..."))

                time.sleep(1)

            except ValueError:
                self.interrumpir()

    def interrumpir(self):
        self.interrumpido = True
