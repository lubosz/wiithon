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
import shutil

import config
import util
from util import NonRepeatList
from builder_wrapper import GtkBuilderWrapper
from trabajo import PoolTrabajo
from animar import Animador
from fila_treeview import FilaTreeview
from wiitdb_schema import Juego, Particion, JuegoWIITDB, JuegoDescripcion, Preferencia

db =        util.getBDD()
session =   util.getSesionBDD(db)

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

    # Lista de particiones, obtenido por el core
    lParti = None
    
    lJuegos_filtrada = None

    # Representación de la fila seleccionada en los distintos treeviews
    sel_juego = FilaTreeview()
    sel_parti = FilaTreeview()
    sel_parti_1on1 = FilaTreeview()
    
    # tiempo del ultimo click en tv_games
    ultimoClick = 0
    
    # builder para el glade
    alert_glade = None
    
    # Hilo que actualiza wiitdb
    xmlWiiTDB = None
    
    # valor busqueda
    buscar = ""
    
    # modo ver | manager
    modo = "ver"

    def __init__(self, core):
        GtkBuilderWrapper.__init__(self,
                                   os.path.join(config.WIITHON_FILES_RECURSOS_GLADE,
                                                'wiithon.ui'))
                                                
        self.core = core
        
        # Cellrenderers que se modifican según cambia el modo
        self.renderEditableIDGAME = None
        self.renderEditableNombre = None

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

                ('Copiar', None, _('Copiar a otra particion'), None, '',
                self.menu_contextual_copiar),

                ('Borrar', gtk.STOCK_DELETE, None, None, '',
                 self.menu_contextual_borrar),
                ])
        
        '''
        * The name of the action. Must be specified.
        * The stock id for the action. Optional with a default value of None if a label is specified.
        * The label for the action. This field should typically be marked for translation, see the set_translation_domain() method. Optional with a default value of None if a stock id is specified.
        * The accelerator for the action, in the format understood by the gtk.accelerator_parse() function. Optional with a default value of None.
        * The tooltip for the action. This field should typically be marked for translation, see the set_translation_domain() method. Optional with a default value of None.
        * The callback function invoked when the action is activated. Optional with a default value of None.
        '''

        self.uimgr.insert_action_group(actiongroup)

        self.uimgr.add_ui_from_string(self.ui_desc)
        self.wb_tv_games.connect('button-press-event', self.on_tv_games_click_event)

        self.wb_principal.drag_dest_set(0, [], 0)
                                        #[('text/uri-list', gtk.TARGET_OTHER_APP, 25)],
                                        #gtk.gdk.ACTION_DEFAULT)

        self.wb_principal.connect("drag_motion", self.drop_motion)
        self.wb_principal.connect("drag_drop", self.drag_drop)
        self.wb_principal.connect("drag_data_received", self.drag_data_received_cb)

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
            
        backup_preferencia_device = self.preferencia.device_seleccionado
        backup_preferencia_idgame = self.preferencia.idgame_seleccionado
        
        # preferencias
        session.commit()

        # permite usar hilos con PyGTK http://faq.pygtk.org/index.py?req=show&file=faq20.006.htp
        # modo seguro con hilos
        gobject.threads_init()

        # ocultar barra de progreso
        self.ocultarHBoxProgreso()

        self.wb_principal.set_icon_from_file(config.ICONO)
        self.wb_principal.show()

        # conexion señales de la toolbar
        self.wb_tb_refrescar_wbfs.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_anadir.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_anadir_directorio.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_extraer.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_renombrar.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_clasificar1.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_borrar.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_copiar_SD.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_acerca_de.connect('clicked' , self.on_tb_toolbar_clicked)
        self.wb_tb_copiar_1_1.connect('clicked' , self.on_tb_toolbar_clicked)

        self.wb_busqueda = util.Entry(clear=True)
        self.wb_busqueda.show()
        self.wb_box_busqueda.pack_start(self.wb_busqueda)
        self.wb_busqueda.connect('changed' , self.on_busqueda_changed)
        self.wb_principal.connect('destroy', self.salir)

        # carga la vista del TreeView de particiones
        self.tv_partitions_modelo = self.cargarParticionesVista(self.wb_tv_partitions, self.on_tv_partitions_cursor_changed)
        
        # carga la vista del TreeView de juegos
        self.tv_games_modelo = self.cargarJuegosVista()
        
        # carga la Vista para las particiones de la copia 1on1
        self.tv_partitions2_modelo = self.cargarParticionesVista(self.wb_tv_partitions2, self.on_tv_partitions2_cursor_changed)
        
        # estilos
        self.wb_estadoTrabajo.set_property("attributes", self.getEstilo_azulGrande())

        # trabajos LIGEROS
        self.poolBash = PoolTrabajo(
                                    self.core , config.NUM_HILOS ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    self.callback_termina_trabajo_descargar_caratula,
                                    self.callback_termina_trabajo_descargar_disco,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None ,
                                    None
                                    )
        self.poolBash.setDaemon(True)
        self.poolBash.start()
        
        # Trabajador, se le mandan trabajos de barra de progreso (trabajos INTENSOS)
        self.poolTrabajo = PoolTrabajo(
                                    self.core , 1,
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
                                    self.callback_termina_trabajo_copiar,
                                    None,
                                    None,
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
        self.poolTrabajo.setDaemon(True)
        self.poolTrabajo.start()
            
        # Animacion que define si hay actividad de la pool batch
        self.animar = Animador( self.wb_estadoBatch , self.poolBash , self.poolTrabajo)
        self.animar.setDaemon(True)
        self.animar.start()
            
        # reffresco inicial en busca de particiones wbfs
        self.refrescarParticionesWBFS()
        
        # advertencia si no encuentra
        if(len(self.lParti) == 0):
            if (os.geteuid() != 0) and (len(self.lJuegos_filtrada)==0):
                self.alert("warning" , _("No se han detectado particiones WBFS.\nSi has conectado una particion WBFS y no ha sido detectada, es debido a que no hay permisos de lectura y escritura.\nPara solucionarlo siga los pasos de la guia de instalacion."))
            else:
                if(len(self.lJuegos_filtrada)>0):
                    self.alert("warning" , _("No hay particiones WBFS, solo puede ver sus juegos acumuladas en %s") % (config.APP))
                else:
                    self.alert("warning" , _("No hay particiones WBFS, conecte y refresque"))
        else:
            if backup_preferencia_device != "" and backup_preferencia_idgame != "":
                self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 0 , backup_preferencia_device)
                self.seleccionarFilaConValor(self.wb_tv_games, len(self.lJuegos_filtrada) , 0 , backup_preferencia_idgame)
        
        # pongo el foco en el buscador
        if( len(self.lJuegos_filtrada)>0 ):
            self.wb_busqueda.grab_focus()
        else:
            self.wb_tb_refrescar_wbfs.grab_focus()

    def refrescarParticionesWBFS(self, verbose = True):
        
        if not self.poolTrabajo.estaOcupado():
            
            ##################################################################################
            # No hay particion seleccionada
            self.sel_parti.obj = None
            #
            # Inicialmente se muestran todas las particiones
            self.todo = True
            #
            # autodeteccion de particiones wbfs
            self.lParti = self.core.getListaParticiones(session)
            #
            # carga particiones al treeview
            self.cargarParticionesModelo(self.tv_partitions_modelo , self.lParti)
            #
            # leer juegos de las aparticiones y guardar en la BDD
            self.leer_juegos_de_las_particiones(self.lParti)
            #
            # Buscar juego en la bdd
            self.lJuegos_filtrada = self.buscar_juego_bdd(self.buscar)
            #
            # descargar caratulas y discos
            for juego in session.query(Juego).group_by('idgame').order_by('lower(title)'):
                if not self.core.existeCaratula(juego.idgame):
                    self.poolBash.nuevoTrabajoDescargaCaratula( juego )
                else:
                    juego.tieneCaratula = True

                if not self.core.existeDisco(juego.idgame):
                    self.poolBash.nuevoTrabajoDescargaDisco( juego )
                else:
                    juego.tieneDiscArt = True
            #
            # refrescar de los resultados de busqueda.
            self.refrescarModeloJuegos( self.lJuegos_filtrada )
            #                    
            # Selecciona el primer juego
            self.seleccionarPrimeraFila(self.wb_tv_partitions)
            
            ##################################################################################
            
        else:
            if verbose:
                self.alert("warning" , _("No puedes refrescar las particiones mientras hay tareas sin finalizar"))

    def main(self , opciones , argumentos):
        if len(self.lParti) > 0:
            for arg in argumentos:
                arg = os.path.abspath(arg)
                if os.path.exists(arg):
                    if util.getExtension(arg)=="iso":
                        self.poolTrabajo.nuevoTrabajoAnadir(arg , self.sel_parti.obj.device)
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

        columna1 = gtk.TreeViewColumn(_('Dispositivo'), render , text=0)
        columna2 = gtk.TreeViewColumn(_('Total'), render , text=1)

        columna1.set_reorderable(True)
        columna1.set_sort_order(gtk.SORT_DESCENDING)
        columna1.set_sort_column_id(0)

        columna2.set_reorderable(True)
        columna2.set_sort_order(gtk.SORT_DESCENDING)
        columna2.set_sort_column_id(1)

        treeview.append_column(columna1)
        treeview.append_column(columna2)

        treeview.connect('cursor-changed', callback_cursor_changed)

        modelo = gtk.ListStore (
                                    gobject.TYPE_STRING,   # device
                                    gobject.TYPE_STRING    # total
                                )

        treeview.set_model(modelo)

        return modelo

    def cargarJuegosVista(self):
        # Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
        tv_games = self.wb_tv_games

        self.renderEditableIDGAME = gtk.CellRendererText()
        self.renderEditableNombre = gtk.CellRendererText()
        self.renderEditableIDGAME.connect ("edited", self.editar_idgame)
        self.renderEditableNombre.connect ("edited", self.editar_nombre)
        #self.renderEditableNombre.connect ("editing-started", self.empieza_editar)
        #self.renderEditableNombre.connect ("editing-canceled", self.cancela_editar)
        render = gtk.CellRendererText()

        # prox versión meter background ----> foreground ... etc
        # http://www.pygtk.org/docs/pygtk/class-gtkcellrenderertext.html
        self.columna1 = columna1 = gtk.TreeViewColumn(_('IDGAME'), self.renderEditableIDGAME , text=0, foreground=8, background=9)
        self.columna2 = columna2 = gtk.TreeViewColumn(_('Nombre'), self.renderEditableNombre , text=1, foreground=8, background=9)
        self.columna3 = columna3 = gtk.TreeViewColumn(_('Tamanio'), render , text=2, foreground=8, background=9)
        self.columna4 = columna4 = gtk.TreeViewColumn(_('Online?'), render , text=3, foreground=8, background=9)
        self.columna5 = columna5 = gtk.TreeViewColumn(_('Local'), render , text=4, foreground=8, background=9)
        self.columna6 = columna6 = gtk.TreeViewColumn(_('Fecha'), render , text=5, foreground=8, background=9)
        self.columna7 = columna7 = gtk.TreeViewColumn(_('Rating'), render , text=6, foreground=8, background=9)
        self.columna8 = columna8 = gtk.TreeViewColumn(_('Particion'), render , text=7, foreground=8, background=9)

        columna1.set_expand(False)
        columna1.set_min_width(80)
        columna1.set_reorderable(True)
        columna1.set_sort_order(gtk.SORT_DESCENDING)
        columna1.set_sort_column_id(0)

        columna2.set_expand(True)
        columna2.set_reorderable(True)
        columna2.set_sort_indicator(True)
        columna2.set_sort_order(gtk.SORT_DESCENDING)
        columna2.set_sort_column_id(1)

        columna3.set_expand(False)
        columna3.set_min_width(80)
        columna3.set_reorderable(True)
        columna3.set_sort_order(gtk.SORT_DESCENDING)
        columna3.set_sort_column_id(2)
        
        columna4.set_expand(False)
        columna4.set_min_width(80)
        columna4.set_reorderable(True)
        columna4.set_sort_order(gtk.SORT_ASCENDING)
        columna4.set_sort_column_id(3)
        
        columna5.set_expand(False)
        columna5.set_min_width(60)
        columna5.set_reorderable(True)
        columna5.set_sort_order(gtk.SORT_ASCENDING)
        columna5.set_sort_column_id(4)
        
        columna6.set_expand(False)
        columna6.set_min_width(110)
        columna6.set_reorderable(True)
        columna6.set_sort_order(gtk.SORT_ASCENDING)
        columna6.set_sort_column_id(5)
        
        columna7.set_expand(False)
        columna7.set_min_width(100)
        columna7.set_reorderable(True)
        columna7.set_sort_order(gtk.SORT_ASCENDING)
        columna7.set_sort_column_id(6)
        
        columna8.set_expand(False)
        columna8.set_min_width(85)
        columna8.set_reorderable(True)
        columna8.set_sort_order(gtk.SORT_ASCENDING)
        columna8.set_sort_column_id(7)

        tv_games.append_column(columna1)
        tv_games.append_column(columna2)
        tv_games.append_column(columna3)
        tv_games.append_column(columna4)
        tv_games.append_column(columna5)
        tv_games.append_column(columna6)
        tv_games.append_column(columna7)
        tv_games.append_column(columna8)

        tv_games.connect('cursor-changed', self.on_tv_games_cursor_changed)

        modelo = gtk.ListStore (
                gobject.TYPE_STRING,                        # IDGAME
                gobject.TYPE_STRING,                        # Nombre
                gobject.TYPE_STRING,                        # Tamaño
                gobject.TYPE_STRING,                        # Online?
                gobject.TYPE_STRING,                        # Local
                gobject.TYPE_STRING,                        # Fecha
                gobject.TYPE_STRING,                        # Rating
                gobject.TYPE_STRING,                        # Device
                gobject.TYPE_STRING,                        # Color letra
                gobject.TYPE_STRING                         # Color fondo
                )
        tv_games.set_model(modelo)

        return modelo
        

    def cargarJuegosModelo(self , modelo , listaJuegos):
        modelo.clear()
        i = 0
        for juego in listaJuegos:
            iterador = modelo.insert(i)
            # El modelo tiene una columna más no representada
            modelo.set_value(iterador,0,                juego.idgame)
            modelo.set_value(iterador,1,                juego.title)
            modelo.set_value(iterador,2, "%.2f GB" %    juego.size)

            juegoWiiTDB = juego.getJuegoWIITDB(session)            
            if juegoWiiTDB != None:

                modelo.set_value(iterador,3, juegoWiiTDB.getTextPlayersWifi(True))
                modelo.set_value(iterador,4, juegoWiiTDB.getTextPlayersLocal(True))
                modelo.set_value(iterador,5, juegoWiiTDB.getTextFechaLanzamiento(True))
                modelo.set_value(iterador,6, juegoWiiTDB.getTextRating(True))

            else:
                
                modelo.set_value(iterador,3, _("??"))
                modelo.set_value(iterador,4, _("??"))
                modelo.set_value(iterador,5, _("??"))
                modelo.set_value(iterador,6, _("??"))
                
            modelo.set_value(iterador,7, juego.particion.device)
            modelo.set_value(iterador,8, juego.particion.getColorForeground())
            modelo.set_value(iterador,9, juego.particion.getColorBackground())

            i = i + 1

    def cargarParticionesModelo(self , modelo , listaParticiones, filtrarTodo = False):
        modelo.clear()

        i = 1
        for particion in listaParticiones:
            if( self.sel_parti == None or particion != self.sel_parti.obj ):
                iterador = modelo.insert(               i                           )
                modelo.set_value(iterador,0,            particion.device            )
                modelo.set_value(iterador,1,            "%.2f GB" % particion.total )
            # el contador esta fuera del if debido a:
            # si lo metemos la numeracion es secuencial, pero cuando insertarDeviceSeleccionado sea False
            # quiero reflejar los huecos. Esto permite un alineamiento con la lista del core
            i = i + 1

        if not filtrarTodo and (len(listaParticiones) > 1):
            # Añadir TODOS
            iterador = modelo.insert(0)
            modelo.set_value(iterador,0,        _("TODOS")          )
            modelo.set_value(iterador,1,        ""                  )

    def editar_idgame( self, renderEditable, i, nuevoIDGAME):
        if self.sel_juego.it != None:
            nuevoIDGAME = nuevoIDGAME.upper()
            if(self.sel_juego.obj.idgame != nuevoIDGAME):
                exp_reg = "[A-Z0-9]{6}"
                if re.match(exp_reg,nuevoIDGAME):
                    sql = util.decode('idgame=="%s" and idParticion=="%d"' % (nuevoIDGAME , self.sel_parti.obj.idParticion))
                    juego = session.query(Juego).filter(sql).first()
                    if juego == None:
                        if ( self.question(_('Advertencia de seguridad de renombrar desde IDGAME = %s a %s') % (self.sel_juego.obj.idgame , nuevoIDGAME)) == 1 ):
                            if self.core.renombrarIDGAME(self.sel_parti.obj.device , self.sel_juego.obj.idgame , nuevoIDGAME):
                                # modificamos el juego modificado de la BDD
                                if self.sel_juego.obj != None:
                                    self.sel_juego.obj.idgame = nuevoIDGAME

                                    # Refrescamos del modelo la columna modificada
                                    self.tv_games_modelo.set_value(self.sel_juego.it , 0 ,nuevoIDGAME)
                            else:
                                self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Ya hay un juego con ese IDGAME"))
                else:
                    self.alert('error' , _("Error: La longitud del IDGAME debe ser 6, y solo puede contener letras y numeros"))

    def editar_nombre( self, renderEditable, i, nuevoNombre):
        if self.sel_juego.it != None:
            nombreActual = self.sel_juego.obj.title
            if(nombreActual != nuevoNombre):
                if len(nuevoNombre) < config.TITULO_LONGITUD_MAX:
                    if not util.tieneCaracteresRaros(nuevoNombre , util.BLACK_LIST2):
                        if self.core.renombrarNOMBRE(self.sel_parti.obj.device , self.sel_juego.obj.idgame , nuevoNombre):
                            if self.sel_juego.obj != None:
                                self.sel_juego.obj.title = nuevoNombre
                                # Refrescamos del modelo la columna modificada
                                self.tv_games_modelo.set_value(self.sel_juego.it , 1 , nuevoNombre)
                        else:
                            self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Se han detectado caracteres no validos: %s") % (util.BLACK_LIST2))
                else:
                    self.alert('error' , _("Nuevo nombre es demasiado largo, intente con un texto menor de %d caracteres") % (config.TITULO_LONGITUD_MAX))

    def salir(self , widget=None, data=None):
        
        if self.sel_juego.obj != None:
            self.preferencia.idgame_seleccionado = self.sel_juego.obj.idgame

        if self.sel_parti.obj != None:
            self.preferencia.device_seleccionado = self.sel_parti.obj.device

        session.commit()

        # cerrar gui
        gtk.main_quit()

        # cerrar hilos
        try:
            self.poolTrabajo.interrumpir()
            self.poolBash.interrumpir()
            self.animar.interrumpir()
            self.poolTrabajo.join()
            self.poolBash.join()
            self.animar.join()
        except AttributeError:
            pass

    def alert(self, level, message):
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

        alert_glade = gtk.Builder()
        alert_glade.add_from_file( os.path.join(config.WIITHON_FILES_RECURSOS_GLADE  , "%s.ui" % config.GLADE_ALERTA) )
        alert_glade.set_translation_domain( config.APP )
        
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
        self.lJuegos_filtrada = self.buscar_juego_bdd(self.buscar)
        self.refrescarModeloJuegos( self.lJuegos_filtrada )
        #self.refrescarEspacio()

    def leer_juegos_de_las_particiones(self, particiones):

        if len(particiones) > 0:
            for particion in particiones:
                # obtener los juegos de esa particion
                self.core.getListaJuegos(session, particion)

    def buscar_juego_bdd(self, buscar):

        subListaJuegos = []

        if self.todo:
            sql = util.decode('title like "%%%s%%" or idgame like "%s%%"' % (buscar , buscar))
        else:
            sql = util.decode('idParticion="%d" and (title like "%%%s%%" or idgame like "%s%%")' % (self.sel_parti.obj.idParticion , buscar , buscar))

        query = session.query(Juego).filter(sql).order_by('lower(title)')
        for juego in query:
            subListaJuegos.append(juego)
        
        return subListaJuegos
        
    def refrescarModeloJuegos(self, listaJuegos):
        # cargar la lista sobre el Treeview
        self.cargarJuegosModelo(self.tv_games_modelo , listaJuegos)

        # seleccionar primera fila del treeview de juegos
        self.seleccionarPrimeraFila(self.wb_tv_games)

    # Llama el callback onchange de los 3 treeview conocidos
    def callback_treeview(self, treeview):
        if treeview == self.wb_tv_games:
            self.on_tv_games_cursor_changed( self.wb_tv_games )
        elif treeview == self.wb_tv_partitions:
            self.on_tv_partitions_cursor_changed( self.wb_tv_partitions )
        elif treeview == self.wb_tv_partitions2:
            self.on_tv_partitions2_cursor_changed( self.wb_tv_partitions2 )
        else:
            raise AssertionError

    def seleccionarFilaConValor(self , treeview, numFilas , columna, valor, callback = True):
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

        if callback:
            self.callback_treeview(treeview)

    def seleccionarPrimeraFila(self , treeview, callback = True):
        # selecciono el primero y provoco el evento
        iter_primero = treeview.get_model().get_iter_first()
        if iter_primero != None:
            treeview.get_selection().select_iter( iter_primero )
        if callback:
            self.callback_treeview(treeview)

    def refrescarEspacio(self):
        
        particion = self.sel_parti.obj
        
        if particion == None:
            return

        # porcentaje uso total
        usado = particion.usado
        libre = particion.libre
        total = particion.total

        self.wb_labelEspacio.set_text("%.2f GB / %.2f GB" % (usado , total))
        try:
            porcentaje = usado * 100.0 / total
        except ZeroDivisionError:
            porcentaje = 0.0
        self.wb_progresoEspacio.set_fraction( porcentaje / 100.0 )

        numJuegos = len(particion.juegos)
        self.wb_progresoEspacio.set_text(_("%d juegos") % (numJuegos))
        
        # BARRA DE ESTADO
        if len(self.lParti) == 0:
            self.wb_label_numParticionesWBFS.set_label(_("No hay particiones WBFS"))
        elif len(self.lParti) == 1:
            self.wb_label_numParticionesWBFS.set_label(_("1 particion WBFS"))
        else:
            self.wb_label_numParticionesWBFS.set_label(_("%d particiones WBFS") % (len(self.lParti)))
        
        #######################
        
        sql = util.decode("idParticion=='%d'" % (particion.idParticion))
        
        numInfos = 0
        for juego in session.query(Juego).filter(sql):
            if juego.getJuegoWIITDB(session) != None:
                numInfos += 1
        self.wb_label_juegosConInfoWiiTDB.set_text(_("Hay %d juegos con informacion WiiTDB") % numInfos)
        
        sinCaratulas = 0
        for juego in session.query(Juego).filter(sql):
            if not juego.tieneCaratula:
                sinCaratulas += 1
        if sinCaratulas == 0:
            self.wb_label_juegosSinCaratula.set_text(_("No faltan caratulas"))
        elif sinCaratulas == 1:
            self.wb_label_juegosSinCaratula.set_text(_("1 juego sin caratula"))
        else:
            self.wb_label_juegosSinCaratula.set_text(_("%d juegos sin caratula") % sinCaratulas)
        
        sinDiscArt = 0
        for juego in session.query(Juego).filter(sql):
            if not juego.tieneDiscArt:
                sinDiscArt += 1
        if sinDiscArt == 0:
            self.wb_label_juegosSinDiscArt.set_text(_("No faltan disc-art"))
        elif sinDiscArt == 1:
            self.wb_label_juegosSinDiscArt.set_text(_("1 juego sin disc-art"))
        else:
            self.wb_label_juegosSinDiscArt.set_text(_("%d juegos sin disc-art") % sinDiscArt)

    def refrescarTareasPendientes(self):
        numTareas = self.poolTrabajo.numTrabajos

        if numTareas <= 1:
            self.wb_estadoTrabajo.hide()
        else:
            etiqueta = _("Hay %d tareas") % (numTareas)
            self.wb_estadoTrabajo.set_label(etiqueta)
            self.wb_estadoTrabajo.show()

        # mostrar espacio barra progreso    
        self.wb_box_progreso.show()

    def getBuscarJuego(self, listaJuegos, idgame):
        if listaJuegos == None or idgame == None:
            return None
        encontrado = False
        i = 0
        while not encontrado and i<len(listaJuegos):
            juego = listaJuegos[i]
            encontrado = juego.idgame == idgame
            if not encontrado:
                i += 1
        if encontrado:
            return listaJuegos[i]
        else:
            return None
            
    def getBuscarParticion(self, listaParticiones, device):
        if listaParticiones == None or device == None:
            return None
        encontrado = False
        i = 0
        while not encontrado and i<len(listaParticiones):
            particion = listaParticiones[i]
            encontrado = (particion.device == device)
            if not encontrado:
                i += 1
        if encontrado:
            return listaParticiones[i]
        else:
            return None

    # Click en juegos --> refresco la imagen de la caratula y disco
    # self.wb_tv_games
    def on_tv_games_cursor_changed(self , treeview):
        if self.sel_juego != None:
            self.sel_juego.actualizar_columna(treeview)
            if self.sel_juego.it != None:
                self.sel_juego.obj = self.getBuscarJuego(self.lJuegos_filtrada, self.sel_juego.clave)
                
                self.ponerCaratula(self.sel_juego.clave, self.wb_img_caratula1)
                self.ponerDisco(self.sel_juego.clave , self.wb_img_disco1)

    # Click en particiones --> refresca la lista de juegos
    def on_tv_partitions_cursor_changed(self , treeview):
        if self.sel_parti != None:
            self.sel_parti.actualizar_columna(treeview)
            if self.sel_parti.it != None:

                # selecciono la particion actual
                self.sel_parti.obj = self.getBuscarParticion(self.lParti, self.sel_parti.clave)
                
                self.todo = self.sel_parti.obj == None
                
                # oculta partes del gui cuando esta en todo
                self.toggle_todo_particion()
                
                #if not self.todo:
            
                # refrescamos el modelo de particiones para la copia 1on1
                self.cargarParticionesModelo(self.tv_partitions2_modelo , self.lParti, True)
                
                #seleccionar primero
                self.seleccionarPrimeraFila( self.wb_tv_partitions2 )
                
                # refrescamos la lista de juegos, leyendo del core
                self.lJuegos_filtrada = self.buscar_juego_bdd(self.buscar)
                
                self.refrescarModeloJuegos( self.lJuegos_filtrada )
                
                # refrescar espacio
                self.refrescarEspacio()

    def toggle_todo_particion(self):
        if self.todo:
            # establecemos el modo de wiithon
            self.modo = "ver"

            # poner la columna titulo desactivada
            self.renderEditableIDGAME.set_property("editable", False)
            self.renderEditableNombre.set_property("editable", False)
            self.renderEditableNombre.set_property("attributes", self.getEstilo_grisGrande())
            
            #ocultar algunas coasa
            self.wb_vboxProgresoEspacio.hide()
            self.wb_labelEspacio.hide()
        else:
            # establecemos el modo de wiithon, hay particiones que gestionar
            self.modo = "manager"
            
            # poner la columna titulo activada
            self.renderEditableIDGAME.set_property("editable", True)
            self.renderEditableNombre.set_property("editable", True)
            self.renderEditableNombre.set_property("attributes", self.getEstilo_azulGrande())
            
            #mostrar algunas coasa
            self.wb_vboxProgresoEspacio.show()
            self.wb_labelEspacio.show()

    def on_tv_partitions2_cursor_changed(self , treeview):
        self.sel_parti_1on1.actualizar_columna(treeview)
        if self.sel_parti_1on1.it != None:
            # le selecciono la particion actual al 1on1
            self.sel_parti_1on1.obj = self.getBuscarParticion(self.lParti, self.sel_parti_1on1.clave)

    def ponerCaratula(self, IDGAME, widget_imagen):
        destinoCaratula = os.path.join(config.HOME_WIITHON_CARATULAS , "%s.png" % (IDGAME))

        if not os.path.exists(destinoCaratula):
            destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
        
        widget_imagen.set_from_file( destinoCaratula )

    def ponerDisco(self, IDGAME, widget_imagen):
        destinoDisco = os.path.join(config.HOME_WIITHON_DISCOS , "%s.png" % IDGAME)
        
        if not os.path.exists(destinoDisco):
            destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
            
        widget_imagen.set_from_file( destinoDisco )

    def on_tv_games_click_event(self, widget, event):
        if event.button == 1:
            tiempo_entre_clicks = event.time - self.ultimoClick
            self.ultimoClick = event.time
            if tiempo_entre_clicks < 400:
                
                if self.sel_juego.obj != None:

                    juego = self.sel_juego.obj.getJuegoWIITDB(session)
                    
                    if juego != None:
                        
                        # poner caratulas
                        self.ponerCaratula(juego.idgame, self.wb_img_caratula2)
                        self.ponerDisco(juego.idgame, self.wb_img_disco2)

                        # idgame
                        self.wb_ficha_idgame.set_text( juego.idgame )
                        
                        # fecha lanzamiento                            
                        self.wb_ficha_fecha_lanzamiento.set_text(juego.getTextFechaLanzamiento())
                            
                        # desarrollador
                        self.wb_ficha_desarrollador.set_text( juego.developer )
                        
                        # editorial
                        self.wb_ficha_editor.set_text( juego.publisher )
                        
                        # titulo y synopsys
                        hayPrincipal = False
                        haySecundario = False
                        i = 0
                        while not hayPrincipal and i<len(juego.descripciones):
                            descripcion = juego.descripciones[i]
                            hayPrincipal = descripcion.lang == config.principal
                            if hayPrincipal:
                                title = descripcion.title
                                synopsis = descripcion.synopsis
                            i += 1
                        
                        if not hayPrincipal:
                            haySecundario = False
                            i = 0
                            while not haySecundario and i<len(juego.descripciones):
                                descripcion = juego.descripciones[i]
                                haySecundario = descripcion.lang == config.secundario
                                if haySecundario:
                                    title = descripcion.title
                                    synopsis = descripcion.synopsis
                                i += 1
                                
                        if hayPrincipal or haySecundario:
                            self.wb_ficha_titulo.set_text( title )
                            self.wb_ficha_synopsis_buffer.set_text( synopsis )
                        else:
                            self.wb_ficha_titulo.set_text( juego.name )
                            self.wb_ficha_synopsis_buffer.set_text( "" )
                        
                        # generos
                        buffer = ""
                        for genero in juego.genero:
                            buffer += genero.nombre + ", "
                        self.wb_ficha_genero.set_text( buffer )
                        
                        # accesorios obligatorios
                        buffer = ""
                        for accesorio in juego.obligatorio:
                            buffer += "%s, " % accesorio.nombre
                            
                        # accesorios opcionales
                        for accesorio in juego.opcional:
                            buffer += "%s (opcional), " % accesorio.nombre

                        self.wb_ficha_accesorio.set_text( buffer )
                        
                        # clasificación PEGI
                        self.wb_ficha_ranking.set_text( juego.getTextRating() )
                        
                        
                        self.wb_ficha_online.set_text( juego.getTextPlayersWifi() )
                            
                        # numero de jugadores en local                            
                        self.wb_ficha_num_jugadores.set_text(juego.getTextPlayersLocal())
                                                
                        # esperamos a que pulse cerrar
                        res = self.wb_ficha_juego.run()
                        self.wb_ficha_juego.hide()

                    else:
                        self.alert('warning', _('No hay datos de este juego. Intente actualizar la base de datos.'))

                else:
                    self.alert("warning" , _("No has seleccionado ningun juego"))
                
        elif event.button == 3:
            popup = self.uimgr.get_widget('/GamePopup')
            popup.popup(None, None, None, event.button, event.time)

    def on_tb_toolbar_clicked(self , id_tb):
        if(self.modo == "ver" and id_tb != self.wb_tb_copiar_SD and id_tb != self.wb_tb_acerca_de and id_tb != self.wb_tb_borrar and id_tb != self.wb_tb_refrescar_wbfs):
            self.alert("warning" , _("Tienes que seleccionar una particion WBFS para realizar esta accion"))

        elif(id_tb == self.wb_tb_acerca_de):
            self.wb_aboutdialog.run()
            self.wb_aboutdialog.hide()
            
        elif(id_tb == self.wb_tb_refrescar_wbfs):
            self.refrescarParticionesWBFS()

        elif(id_tb == self.wb_tb_copiar_1_1):
            if len(self.lParti) > 1:                
                res = self.wb_dialogo_copia_1on1.run()
                self.wb_dialogo_copia_1on1.hide()
                device_destino = self.sel_parti_1on1.obj

                # salir por Cancelar ---> 0
                # salir por Escape ---> -4
                if(res > 0):
                    
                    juegosParaClonar = []
                    juegosExistentesEnDestino = []

                    if(res == 1):
                        if self.sel_juego.it != None:
                            juegosParaClonar.append( util.clonarOBJ(self.sel_juego.obj) )
                            
                            pregunta = _("Desea copiar el juego %s a la particion %s?") % (self.sel_juego.obj, device_destino)

                        else:
                            self.alert("warning" , _("No has seleccionado ningun juego"))

                    elif(res == 2):
                        for juego in self.lJuegos_filtrada:
                            juegosParaClonar.append( util.clonarOBJ(juego) )
                    
                        self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 0 , device_destino.device)

                        for juego in self.lJuegos_filtrada:
                            encontrado = False
                            i = 0
                            while (not encontrado) and (i<len(juegosParaClonar)):
                                encontrado = (juego.idgame == juegosParaClonar[i].idgame)
                                if not encontrado:
                                    i += 1
                            if encontrado:
                                juegosExistentesEnDestino.append(juegosParaClonar[i])
                                juegosParaClonar.remove(juegosParaClonar[i])
                                
                        pregunta  = "%s %s:\n\n" % (_("Se van a copiar los siguientes juegos a"), device_destino)
                        
                        i = 0
                        for juego in juegosParaClonar:
                            pregunta += "%s\n" % (juego)
                            i += 1
                            if i >= config.MAX_LISTA_COPIA_1on1:
                                pregunta += "[...] (%d %s)\n" % (len(juegosParaClonar)-config.MAX_LISTA_COPIA_1on1, _("juegos mas"))
                                break
                        pregunta += "\n\n%s %s:\n\n" % (_("A continuacion se listan los juego que NO van a ser copiados por ya estar en la particion de destino"),device_destino)
                        i = 0
                        for juego in juegosExistentesEnDestino:
                            pregunta += "%s\n" % (juego)
                            i += 1
                            if i >= config.MAX_LISTA_COPIA_1on1:
                                pregunta += "[...] (%d %s)\n" % (len(juegosExistentesEnDestino)-config.MAX_LISTA_COPIA_1on1, _("juegos mas"))
                                break
                        pregunta += "\n%s" % _("Empezar a copiar?")
                        
                    if len(juegosParaClonar) > 0:
                        if((self.question(pregunta) == 1)):
                            self.poolTrabajo.nuevoTrabajoClonar( juegosParaClonar, device_destino )
                else:
                    self.alert('info',_("No hay nada que copiar a %s") % (device_destino))
            else:
                self.alert("warning" , _("Debes tener al menos 2 particiones WBFS para hacer copias 1:1"))

        elif(id_tb == self.wb_tb_borrar):
            if self.sel_juego.it != None:
                
                borrarBDD = False
                
                if self.modo == "ver":
                    if ( self.question(_('Advertencia de borrar %s en modo ver') % (self.sel_juego.obj)) == 1 ):
                        if self.sel_juego.obj != None:
                            
                            # borrar disco
                            self.core.borrarDisco( self.sel_juego.obj )

                            # borrar caratula
                            self.core.borrarCaratula( self.sel_juego.obj )

                            # orden de borrar de la BDD
                            borrarBDD = True

                else:
                    if( self.question(_('Quieres borrar el juego: %s?') % (self.sel_juego.obj)) == 1 ):
                        # borrar del HD
                        if self.core.borrarJuego( self.sel_parti.obj.device , self.sel_juego.obj.idgame ):
                            
                            # orden de borrar de la BDD
                            borrarBDD = True

                        else:
                            self.alert("warning" , _("Error borrando"))
                            
                if borrarBDD:
                    session.delete(self.sel_juego.obj)

                    # borrar de la tabla
                    self.tv_games_modelo.remove( self.sel_juego.it )
                    
                    # Borrar de las listas                        
                    self.lJuegos_filtrada.remove( self.sel_juego.obj )
                    
                    # recargar modelo de datos
                    self.refrescarModeloJuegos( self.lJuegos_filtrada )
                    
                    # seleccionar el primero
                    #self.seleccionarPrimeraFila(self.wb_tv_games)
                    
                    self.refrescarEspacio()
                    
                    # FIXME: hacer una transacción
                    session.commit()

            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))

        elif(id_tb == self.wb_tb_extraer):
            if self.sel_juego.it != None:
                botones = (
                        gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK,
                        )

                fc_extraer = gtk.FileChooserDialog(
                    _('Elige un directorio donde extraer la ISO de %s') \
                        % (self.sel_juego.obj.idgame), None,
                    gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, botones)

                fc_extraer.set_default_response(gtk.RESPONSE_OK)
                fc_extraer.set_local_only(True)
                try:
                    fc_extraer.add_shortcut_folder(self.preferencia.ruta_extraer_iso)
                except:
                    pass
                
                res = fc_extraer.run()

                if(res == gtk.RESPONSE_OK):

                    reemplazar = False
                    if self.core.existeExtraido(self.sel_juego.obj , fc_extraer.get_filename()):
                        if( self.question(_('Desea reemplazar la iso del juego %s?') % (self.sel_juego.obj)) == 1 ):
                            reemplazar = True
                    else:
                        reemplazar = True
                        
                    if reemplazar:
                        # nueva ruta favorita
                        self.preferencia.ruta_extraer_iso = fc_extraer.get_current_folder()

                        # extraer *juego* en la ruta seleccionada
                        self.poolTrabajo.nuevoTrabajoExtraer(self.sel_juego.obj , fc_extraer.get_filename())

                fc_extraer.destroy()
                #fc_extraer.hide()
            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))

        elif(id_tb == self.wb_tb_renombrar):
            if self.sel_juego.it != None:
                # Obtiene el foco
                self.wb_tv_games.grab_focus()
                # Editar celda
                path = self.sel_juego.get_path(self.wb_tv_games)
                self.wb_tv_games.set_cursor(path , self.columna2 , True)

            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))

        elif(id_tb == self.wb_tb_anadir or id_tb == self.wb_tb_anadir_directorio):
            if self.sel_parti.it != None:

                botones =   (
                                gtk.STOCK_CANCEL,
                                gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN,
                                gtk.RESPONSE_OK,
                            )

                if(id_tb == self.wb_tb_anadir):
                    fc_anadir = gtk.FileChooserDialog(_("Elige una imagen ISO valida para Wii"), None , gtk.FILE_CHOOSER_ACTION_OPEN , botones)
                    fc_anadir.set_select_multiple(True)
                    filter = gtk.FileFilter()
                    filter.set_name(_('Imagen Wii (ISO o RAR)'))
                    filter.add_pattern('*.iso')
                    filter.add_pattern('*.rar')
                    fc_anadir.add_filter(filter)
                    fc_anadir.set_current_folder( self.preferencia.ruta_anadir )
                    #fc_anadir.set_current_name( self.preferencia.ruta_anadir )

                elif(id_tb == self.wb_tb_anadir_directorio):
                    fc_anadir = gtk.FileChooserDialog(_("Elige un directorio"), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                    fc_anadir.set_current_folder( self.preferencia.ruta_anadir_directorio )
                    #fc_anadir.set_current_name( self.preferencia.ruta_anadir_directorio )

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

                    listaISO = []
                    listaRAR = []
                    listaDirectorios = []
                    buffer_juegosYaMetidos = _("Algunos juegos no se han introducido:\n\n")
                    hay_juegosYaMetidos = False
                    for fichero in fc_anadir.get_filenames():
                        if( os.path.isdir( fichero ) ):
                            listaDirectorios.append(fichero)
                        elif( util.getExtension(fichero) == "rar" ):
                            listaRAR.append(fichero)
                        elif( util.getExtension(fichero) == "iso" ):
                            idgame = util.getMagicISO(fichero)
                            if idgame != None:
                                sql = util.decode("idgame=='%s' and idParticion=='%d'" % (idgame , self.sel_parti.obj.idParticion))
                                self.juegoNuevo = session.query(Juego).filter(sql).first()
                                if self.juegoNuevo == None:
                                    listaISO.append(fichero)
                                else:
                                    hay_juegosYaMetidos = True
                                    buffer_juegosYaMetidos += _("%s ya existe en %s\n") % (self.juegoNuevo.title, self.juegoNuevo.particion.device)
                    
                    if hay_juegosYaMetidos:
                        self.alert('warning',buffer_juegosYaMetidos)

                    if len(listaISO) > 0:
                        listaISO.sort()
                        self.poolTrabajo.nuevoTrabajoAnadir( listaISO , self.sel_parti.obj.device)
                        
                    if len(listaRAR) > 0:
                        listaRAR.sort()
                        self.poolTrabajo.nuevoTrabajoDescomprimirRAR( listaRAR , self.sel_parti.obj)
                        
                    if len(listaDirectorios) > 0:
                        listaDirectorios.sort()
                        self.poolTrabajo.nuevoTrabajoRecorrerDirectorio( listaDirectorios , self.sel_parti.obj)

                fc_anadir.destroy()

            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

        elif(id_tb == self.wb_tb_copiar_SD):
            if self.sel_juego.it != None:
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

                if ( fc_copiar_SD.run() == gtk.RESPONSE_OK ):
                    fc_copiar_discos_SD = gtk.FileChooserDialog(_('Paso 2 de 2: Elige un directorio para los DISCOS'), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
                    fc_copiar_discos_SD.set_default_response(gtk.RESPONSE_OK)
                    fc_copiar_discos_SD.set_local_only(True)
                    fc_copiar_discos_SD.set_current_folder(self.preferencia.ruta_copiar_discos)
                    if(fc_copiar_discos_SD.run() == gtk.RESPONSE_OK):
                        self.preferencia.ruta_copiar_caratulas = fc_copiar_SD.get_current_folder()
                        self.preferencia.ruta_copiar_discos = fc_copiar_discos_SD.get_current_folder()

                        # copiar toda la lista de juegos
                        self.poolBash.nuevoTrabajoCopiarCaratula(self.lJuegos_filtrada , fc_copiar_SD.get_filename())
                        self.poolBash.nuevoTrabajoCopiarDisco(self.lJuegos_filtrada, fc_copiar_discos_SD.get_filename())

                    fc_copiar_discos_SD.destroy()

                fc_copiar_SD.destroy()

            else:
                self.alert("warning" , _("No tienes ningun juego"))
                
########## WIITDB ###########
                
    def on_tb_actualizar_wiitdb_clicked(self, boton):
        
        if ( self.question(_('Seguro que deseas descargar información de los juegos de WiiTDB?\n\n%s') % (config.URL_ZIP_WIITDB)) == 1 ):
            self.poolTrabajo.nuevoTrabajoActualizarWiiTDB()
        
    def callback_empieza_importar(self, xml):
        self.juegos = 0
        self.descripciones = 0
        self.generos = 0
        self.online_features = 0
        self.accesorios = 0
        self.companies = 0
        self.actualizarLabel(_("Empezando a obtener datos de juegos desde WiiTDB"))
        self.actualizarFraccion(0.0)
        
    def callback_termina_importar(self, xml):
        self.actualizarLabel(_("Finalizada satisfactoriamente la importacion de datos desde WiiTDB"))
        self.actualizarFraccion(1.0)
        gobject.idle_add(self.refrescarModeloJuegos, self.lJuegos_filtrada)

    def callback_spinner(self, cont, total):
        porcentaje = (cont * 100.0 / total)
        self.actualizarLabel(_("%d%% - %d/%d games - %d descriptions - %d genre - %d accesories - %d companies - %d online features") % (porcentaje, cont, total , self.descripciones, self.generos, self.accesorios, self.companies, self.online_features))
        porcentual = porcentaje / 100
        self.actualizarFraccion(porcentual)

    def callback_nuevo_juego(self, juego):
        self.juegos += 1

    def callback_nuevo_descripcion(self, descripcion):
        self.descripciones += 1

    def callback_nuevo_genero(self, genero):
        self.generos += 1

    def callback_nuevo_online_feature(self, online_feature):
        self.online_features += 1

    def callback_nuevo_accesorio(self, accesorio, obligatorio):
        self.accesorios += 1

    def callback_nuevo_companie(self, companie):
        self.companies += 1

    def callback_error_importando(self, xml, motivo):
        self.alert("error" , _("Error importando %s: %s") % (xml, motivo))
        
    def callback_empieza_descarga(self, url):
        self.actualizarLabel(_("Descargando WiiTDB desde %s, espere unos minutos ...") % url)
        self.actualizarFraccion(0.01)
        
    def callback_empieza_descomprimir(self, zip):
        self.actualizarLabel(_("Empezando a descomprimir la informacion WiiTDB"))
        self.actualizarFraccion(0.99)
        
#############################

############# METODOS que modifican el GUI, si se llaman desde hilos, se hacen con gobject

    def ocultarHBoxProgreso(self):
        self.wb_box_progreso.hide()
        return False

    def actualizarLabel( self, etiqueta ):
        self.wb_progreso1.set_text( etiqueta )

    def actualizarFraccion( self , fraccion ):
        self.wb_progreso1.set_fraction( fraccion )

    def refrescarParticionesYSeleccionarJuego(self, fichero, DEVICE):

        # leer IDGAME del juego añadido
        IDGAME = util.getMagicISO(fichero)

        # consultamos al wiithon wrapper info sobre el juego con nueva IDGAME
        # lo añadimos a la lista
        juego = self.core.getInfoJuego(session, DEVICE, IDGAME)
        self.lJuegos_filtrada.append(juego)
       
        # seleccionamos la particion y la fila del juego añadido
        self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 0 , DEVICE)
        self.seleccionarFilaConValor(self.wb_tv_games, len(self.lJuegos_filtrada) , 0 , IDGAME)
        
        # descargamos su info wiitdb
        self.poolTrabajo.nuevoTrabajoActualizarWiiTDB('http://wiitdb.com/wiitdb.zip?ID=%s' % IDGAME)
        
    def refrescarParticionesYSeleccionarJuego2(self, juego , particion):
        
        juego = self.core.getInfoJuego(session, particion.device, juego.idgame)        
        self.lJuegos_filtrada.append(juego)
        
        # seleccionamos la particion y la fila del juego añadido
        self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 0 , particion.device)
        self.seleccionarFilaConValor(self.wb_tv_games, len(self.lJuegos_filtrada) , 0 , juego.idgame)
        
    def mostrarError(self, error):
        self.alert('error',error)

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
            fichero = fichero.replace("file://" , "")
            if os.path.exists(fichero):
                if(util.getExtension(fichero)=="iso"):
                    listaArrastrados.append(fichero)
                if self.sel_juego.it != None:
                    if  (
                            (util.getExtension(fichero)=="png") or
                            (util.getExtension(fichero)=="jpg") or
                            (util.getExtension(fichero)=="gif")
                        ):
                        ruta = self.core.getRutaCaratula(self.sel_juego.obj.idgame)
                        shutil.copy(fichero, ruta)
                        os.system('mogrify -resize 160x224! "%s"' % (ruta))
                        self.ponerCaratula(self.sel_juego.obj.idgame, self.wb_img_caratula1)

        listaArrastrados.sort()
        if self.poolTrabajo and len(listaArrastrados)>0:
            self.poolTrabajo.nuevoTrabajoAnadir(listaArrastrados, self.sel_parti.obj.device)

    def callback_empieza_progreso(self, trabajo):
        self.hiloCalcularProgreso = HiloCalcularProgreso( trabajo, self.actualizarLabel , self.actualizarFraccion )
        self.hiloCalcularProgreso.start()
        gobject.idle_add(self.actualizarFraccion , 0.0 )

    def callback_termina_progreso(self, trabajo):
        gobject.idle_add(self.actualizarFraccion , 1.0 )

    def callback_empieza_trabajo_anadir(self, trabajo):
        pass

    def callback_termina_trabajo_anadir(self, trabajo , fichero, device):
        if trabajo.exito:
            gobject.idle_add( self.refrescarParticionesYSeleccionarJuego , fichero , device)
            
    # Al terminar hay que seleccionar la partición destino y el juego copiado
    def callback_termina_trabajo_copiar(self, trabajo, juego, particion):
        if trabajo.exito:
            gobject.idle_add( self.refrescarParticionesYSeleccionarJuego2 , juego , particion)

    def callback_nuevo_trabajo(self, trabajo):
        gobject.idle_add( self.refrescarTareasPendientes )

    def callback_empieza_trabajo(self, trabajo):
        print _("Empieza %s") % trabajo
        gobject.idle_add( self.refrescarTareasPendientes )

    def callback_termina_trabajo(self, trabajo):
        # No hay trabajo cuando el contador este a 1, que es el propio trabajo que da la señal
        if(self.poolTrabajo.numTrabajos <= 1):
            gobject.timeout_add( 5000, self.ocultarHBoxProgreso )
            
        # al final, por ser bloqueante
        if not trabajo.exito:
            gobject.idle_add( self.mostrarError , trabajo.error )
            
        print _("Termina: %s") % trabajo

    def callback_empieza_trabajo_extraer(self, trabajo):
        pass

    def callback_termina_trabajo_extraer(self, trabajo):
        pass

    def callback_empieza_trabajo_copiar(self, trabajo):
        pass
        
    def callback_termina_trabajo_descargar_caratula(self, trabajo, juego):
        juego.tieneCaratula = trabajo.exito
        if juego.tieneCaratula:
            if juego.idgame == self.sel_juego.obj.idgame:
                gobject.idle_add( self.ponerCaratula , juego.idgame , self.wb_img_caratula1)
        else:
            print _("Falla la descarga de la caratula de %s") % juego
        
    def callback_termina_trabajo_descargar_disco(self, trabajo, juego):
        juego.tieneDiscArt = trabajo.exito
        if juego.tieneDiscArt:
            if juego.idgame == self.sel_juego.obj.idgame:
                gobject.idle_add( self.ponerDisco , juego.idgame , self.wb_img_disco1)
        else:
            print _("Falla la descarga del disco de %s") % juego

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
        
        estaAbierto = False
        
        while not estaAbierto:
            if os.path.exists(config.HOME_WIITHON_LOGS_PROCESO):
                f = file(config.HOME_WIITHON_LOGS_PROCESO)
                estaAbierto = True
            else:
                time.sleep(1)
        
        while not self.interrumpido:
            # si aún no existe el fichero que contiene los mensajes, esperamos:
            # a) a que el fichero exista
            # b) desde otro hilo nos den orden de interrupción
            try:
                f.seek(0)
                for linea in f:
                    ultimaLinea = linea

                cachos = ultimaLinea.split(config.SEPARADOR)

                if cachos[0] == "YA_ESTA_EN_DISCO" or cachos[0] == "ISO_NO_EXISTE":
                    self.interrumpir()
                    continue

                # FIN es un convenio que viene de la funcion "spinner" en libwbfs.c
                if self.trabajo.terminado or cachos[0] == "FIN":
                    self.porcentaje = 100
                    if self.trabajo.exito or cachos[0] == "FIN":
                        informativo = _("Finalizando ...")
                    else:
                        informativo = _("ERROR!")
                    gobject.idle_add(self.actualizarLabel , "%s - %d%% - %s" % ( self.trabajo , self.porcentaje, informativo ))
                    self.interrumpir()
                else:
                    try:
                        self.porcentaje = float(cachos[0])
                        
                        try:
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
                        except ValueError:
                            # para descomprimir RAR
                            gobject.idle_add(self.actualizarLabel , "%s - %d%%" % ( self.trabajo , self.porcentaje ))
                    except ValueError:
                        print _("Error en progreso")
                        self.porcentaje = 100.0
                        self.interrumpir()

                porcentual = self.porcentaje / 100.0
                gobject.idle_add(self.actualizarFraccion , porcentual )

            except UnboundLocalError:
                gobject.idle_add(self.actualizarLabel , _("Empezando ..."))

            time.sleep(1)

        f.close()

    def interrumpir(self):
        self.interrumpido = True
