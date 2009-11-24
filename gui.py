#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import time
import sys
import re
import traceback
import signal
from threading import Thread

import gtk
import gobject
import pango
import shutil

import config
import util
import wiitdb_schema
from util import NonRepeatList
from builder_wrapper import GtkBuilderWrapper
from trabajo import PoolTrabajo
from animar import Animador
from fila_treeview import FilaTreeview
from wiitdb_schema import Juego, Particion, JuegoWIITDB, JuegoDescripcion, Preferencia, Genero
from informacion_gui import InformacionGuiPresentacion
from selector_ficheros import SelectorFicheros
from textview_custom import TextViewCustom
from estadistica import MuestraEstadistica

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiithonGUI(GtkBuilderWrapper):

    def __init__(self, core, loading):
        GtkBuilderWrapper.__init__(self, os.path.join(config.WIITHON_FILES_RECURSOS_GLADE, '%s.ui' % config.APP))

        # referencia al core
        self.core = core
        
        # loading y su mutex
        self.loading = loading
        self.loading_cerrado = False

        # Lista de particiones
        self.lParti = None

        # lista de juegos mostrados
        self.lJuegos = None
        
        # mutex de seguridad para preferencias
        # evita problemas de concurrencia en la bdd
        self.wiitdb_mutex = False

        # Representación de la fila seleccionada en los distintos treeviews
        self.sel_juego = FilaTreeview()
        self.sel_parti = FilaTreeview()
        self.sel_parti_1on1 = FilaTreeview()

        # valor busqueda
        self.buscar = ""

        # informacion del gui
        self.info = None

        # Cellrenderers que se modifican según cambia el modo
        self.renderEditableIDGAME = None
        self.renderEditableNombre = None
        
        # controlador hook de excepciones
        sys.excepthook = self.excepthook

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

                ('VerJuegoWiiTDB', None, _("Ver Juego en WiiTDB"), None, '',
                 self.menu_contextual_ver_juego_wiitdb),

                ('EditarJuegoWiiTDB', None, _("Editar Juego en WiiTDB"), None, '',
                 self.menu_contextual_editar_juego_wiitdb),
                 
                ('BuscarGoogle', None, "%s Google" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_google),
                 
                ('BuscarWikipedia', None, "%s Wikipedia" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_wikipedia),
                 
                ('BuscarYoutube', None, "%s Youtube" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_youtube),
                 
                ('BuscarIGN', None, "%s IGN" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_ign),
                 
                ('BuscarGameSpot', None, "%s GameSpot" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_gamespot),
                 
                ('BuscarVGChartz', None, "%s VGChartz" % _("Buscar en"), None, '',
                 self.menu_contextual_buscar_vgchartz),

                ])
        
        self.uimgr.insert_action_group(actiongroup)

        ui_desc = '''
        <ui>
            <popup action="GamePopup">
                <menuitem action="Renombrar"/>
                <menuitem action="Extraer"/>
                <menuitem action="Copiar"/>
                <separator/>
                <menuitem action="Borrar"/>
                <separator/>
                <menuitem action="VerJuegoWiiTDB"/>
                <menuitem action="EditarJuegoWiiTDB"/>
                <separator/>
                <menuitem action="BuscarGoogle"/>
                <menuitem action="BuscarWikipedia"/>
                <menuitem action="BuscarYoutube"/>
                <menuitem action="BuscarIGN"/>
                <menuitem action="BuscarGameSpot"/>
                <menuitem action="BuscarVGChartz"/>
            </popup>
        </ui>
        '''

        self.uimgr.add_ui_from_string(ui_desc)
        self.wb_tv_games.connect('button-press-event', self.on_tv_games_click_event)

        # http://www.pygtk.org/pygtk2tutorial-es/sec-DNDMethods.html
        self.wb_principal.drag_dest_set(0, [], gtk.gdk.ACTION_DEFAULT)

        self.wb_principal.connect("drag_motion", self.drop_motion)
        self.wb_principal.connect("drag_drop", self.drag_drop)
        self.wb_principal.connect("drag_data_received", self.drag_data_received_cb)

        # iniciar preferencias
        self.core.prefs.cargarPreferenciasPorDefecto(   self.wb_prefs_vbox_general,
                                                        self.wb_prefs_vbox_caratulas,
                                                        self.wb_prefs_vbox_wiitdb,
                                                        self.wb_prefs_vbox_buscadores,
                                                        True
                                                        )

        backup_preferencia_device = self.core.prefs.device_seleccionado
        backup_preferencia_idgame = self.core.prefs.idgame_seleccionado

        # ocultar barra de progreso
        #self.ocultarHBoxProgreso()

        self.wb_principal.set_icon_from_file(config.ICONO)
        #self.wb_principal.maximize()
        self.wb_principal.set_size_request(1000, -1)
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
        self.wb_tb_preferencias.connect('clicked' , self.on_tb_toolbar_clicked)

        self.wb_busqueda = util.Entry(clear=True)
        self.wb_busqueda.show()
        self.wb_box_busqueda.pack_start(self.wb_busqueda)
        self.wb_busqueda.connect('changed' , self.on_busqueda_changed)
        
        self.wb_principal.connect('destroy', self.salir)

        # carga la vista del TreeView de particiones
        self.tv_partitions_modelo = self.cargarParticionesVista(self.wb_tv_partitions, self.on_tv_partitions_cursor_changed)
        
        # carga la Vista para las particiones de la copia 1on1
        self.tv_partitions2_modelo = self.cargarParticionesVista(self.wb_tv_partitions2, self.on_tv_partitions2_cursor_changed)
        
        # carga la vista del TreeView de juegos
        self.tv_games_modelo = self.cargarJuegosVista()
        
        ################### crear text view custom para info de wiitdb #########
        self.tvc_info_juego = TextViewCustom()
        self.tvc_info_juego.cargar_tags_html()
        
        sw1 = gtk.ScrolledWindow()
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw1.set_size_request(-1, 540)
        sw1.set_shadow_type(gtk.SHADOW_IN)
        sw1.add(self.tvc_info_juego)
        
        self.tvc_info_juego.show()
        sw1.show()
        self.wb_hbox_hueco_info_juego.pack_start(sw1, expand=True, fill=True, padding=0)
        ################### crear text view custom para descripcion wiitdb #########
        
        self.tvc_descripcion = TextViewCustom()
        self.tvc_descripcion.cargar_tags_html()
        
        sw2 = gtk.ScrolledWindow()
        sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw2.set_size_request(-1, 540)
        sw2.set_shadow_type(gtk.SHADOW_IN)
        sw2.add(self.tvc_descripcion)
        
        self.tvc_descripcion.show()
        sw2.show()
        self.wb_hbox_hueco_descripcion.pack_start(sw2, expand=True, fill=True, padding=0)
        ################## /FIN ##################################################
        
        # estilos
        self.wb_estadoTrabajo.set_property("attributes", self.getEstilo_azulGrande())

        # trabajos LIGEROS
        self.poolBash = PoolTrabajo(
                                    self.core , self.core.prefs.NUM_HILOS ,
                                    self.callback_empieza_trabajo ,
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
                                    self.callback_termina_importar
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
        self.poolTrabajo.poolBash = self.poolBash
        self.poolTrabajo.start()

        # info gui
        self.info = InformacionGuiPresentacion(self.wb_labelEspacio, self.wb_progresoEspacio, 
                self.wb_label_numParticionesWBFS, self.wb_label_juegosConInfoWiiTDB,
                self.wb_label_juegosSinCaratula, self.wb_label_juegosSinDiscArt,
                self.wb_estadoTrabajo)
            
        # Animacion que define si hay actividad de la pool batch
        self.animar = Animador(     self.wb_estadoBatch,
                                    self.poolBash,
                                    self.poolTrabajo,
                                    self.mostrarHBoxProgreso,
                                    self.ocultarHBoxProgreso)
        self.animar.setDaemon(True)
        self.animar.start()
                   
        # reffresco inicial en busca de particiones wbfs
        self.refrescarParticionesWBFS()
        
        # seleccionados preferidas.
        if backup_preferencia_device != "":
            self.seleccionarFilaConValor(self.wb_tv_partitions, 0 , backup_preferencia_device)
        if backup_preferencia_idgame != "":
            self.seleccionarFilaConValor(self.wb_tv_games, 0 , backup_preferencia_idgame)

        # pongo el foco en el buscador
        if( len(self.lJuegos)>0 ):
            self.wb_busqueda.grab_focus()
        else:
            self.wb_tb_refrescar_wbfs.grab_focus()

    def main(self , opciones , argumentos):
        
        listaISO = NonRepeatList()
        listaRAR = NonRepeatList()
        listaDirectorios = NonRepeatList()
        
        for arg in argumentos:
            fichero = os.path.abspath(arg)
            if(util.getExtension(fichero)=="iso"):
                listaISO.append(fichero)
            elif(util.getExtension(fichero)=="rar"):
                listaRAR.append(fichero)
            elif( os.path.isdir( fichero ) ):
                listaDirectorios.append(fichero)
                        
        if len(listaISO) > 0 or len(listaRAR) > 0 or len(listaDirectorios) > 0:

            if self.isSelectedPartition():

                if len(listaISO) > 0:
                    listaISO.sort()
                    self.poolTrabajo.nuevoTrabajoAnadir( listaISO , self.sel_parti.obj.device)
                    
                if len(listaRAR) > 0:
                    listaRAR.sort()
                    self.poolTrabajo.nuevoTrabajoDescomprimirRAR( listaRAR , self.sel_parti.obj)

                if len(listaDirectorios) > 0:
                    listaDirectorios.sort()
                    self.poolTrabajo.nuevoTrabajoRecorrerDirectorio( listaDirectorios , self.sel_parti.obj)                
                    
            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

        # cerrar carga
        self.cerrar_loading()
        
        # GO
        gtk.main()


    def cerrar_loading(self):
        if not self.loading_cerrado:
            self.loading_cerrado = True
            os.kill(self.loading.pid, signal.SIGINT)

    def refrescarParticionesWBFS(self, verbose = True):
        
        if config.DEBUG:
            print "refrescarParticionesWBFS"
        
        if not self.poolTrabajo.estaOcupado():
            
            ##################################################################################
            # No hay particion seleccionada
            self.sel_parti.obj = None
            #
            # autodeteccion de particiones wbfs
            self.lParti = self.core.sincronizarParticiones()
            #
            # carga particiones al treeview
            self.cargarParticionesModelo(self.tv_partitions_modelo , self.lParti)
            #
            # leer juegos de las aparticiones y guardar en la BDD
            self.leer_juegos_de_las_particiones(self.lParti)
            #
            # Buscar juego en la bdd
            self.lJuegos = self.buscar_juego_bdd(self.buscar)
            #                    
            # Selecciona el primer juego
            self.seleccionarPrimeraFila(self.wb_tv_partitions)
            #
            # refrescar num juegos con info
            self.refrescarInfoWiiTDB()
            #            
            # clean png corrupts
            query = session.query(Juego).group_by('idgame')
            for juego in query:
                self.core.existeCaratula(juego.idgame, True)
                self.core.existeDisco(juego.idgame, True)
            #
            # refrescar num caratulas
            self.refrescarNumCaratulas()
            #
            # descargar caratulas y discos
            query = session.query(Juego).order_by('idParticion, lower(title)').group_by('idgame')
            for juego in query:

                if not self.core.existeCaratula(juego.idgame):
                    self.poolBash.nuevoTrabajoDescargaCaratula(juego.idgame)

                if not self.core.existeDisco(juego.idgame):
                    self.poolBash.nuevoTrabajoDescargaDisco(juego.idgame)
            #
            ##################################################################################
            
            # si no hay particion -> modal que da 2 opciones:
            # 1º Ver base de datos
            # 2º Salir

            if (self.core.prefs.ADVERTENCIA_NO_WBFS and len(self.lParti) == 0):
                
                self.cerrar_loading()
                
                if util.check_gids():
                    self.alert("warning" , _("No hay particiones WBFS, se muestran los juegos de la ultima sesion."))
                else:
                    self.alert("warning" , _("No puede acceder a las particiones porque el usuario que se puso en marcha wiithon no pertenecen al grupo \"disk\", se muestran los juegos de la ultima sesion."))

            elif (self.core.prefs.ADVERTENCIA_ACTUALIZAR_WIITDB and (len(self.lJuegos) > 0) and self.info.abajo_num_juegos_wiitdb == 0):

                self.cerrar_loading()

                if (self.question("""
                    <b>
                        <pr>%s</pr>
                        <br />
                        <br />
                        <pr>%s</pr>
                        <br />
                        <br />
                        <azul><pr>%s</pr></azul>
                    </b>
                    """ % (
                            _("Se ha detectado que ninguno de tus juegos disponen de informacion extra, descargada de Internet."),
                            _("Deseas descargar informacion de los juegos desde WiiTDB?"),
                            self.core.prefs.URL_ZIP_WIITDB
                            ),
                            xml = True) ):
                    self.poolTrabajo.nuevoTrabajoActualizarWiiTDB(self.core.prefs.URL_ZIP_WIITDB)                
            
        else:
            if verbose:
                self.alert("warning" , _("No puedes refrescar las particiones mientras hay tareas sin finalizar"))

    def excepthook(self, exctype, excvalue, exctb):
        self.cerrar_loading()
        tbtext = ''.join(traceback.format_exception(exctype, excvalue, exctb))
        mensaje_xml = """
        <negro><pr>%s</pr></negro><br />
        <br />
        <rojo><pr>%s</pr></rojo><br />
        <negro><pr>%s</pr></negro><br />
        <u><azul><pr>%s</pr></azul></u><br />
        """  % (    _("Por favor. Informe a los desarrolladores de este error."),
                    util.parsear_a_XML(tbtext),
                    _('Utitice la siguiente URL para el reporte de bugs:'),
                    config.URL_BUGS)
        self.alert('error' , mensaje_xml, excvalue, xml=True)

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
        
    def getEstilo_Mediano(self):

        #Creo una lista de atributos
        atributos = pango.AttrList()

        #inserto el tamaño (tamaño_en_puntos * 1000)
        #el 0,-1 indica que se aplica a todo el texto del label.
        atributos.insert(pango.AttrSize(10000,0,-1))

        #inserto el grosor
        #200=ultra-light, 300=light, 400=normal, 700=bold, 800=ultra-bold, 900=heavy
        atributos.insert(pango.AttrWeight(700,0,-1))

        return atributos

    def menu_contextual_renombrar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_renombrar )

    def menu_contextual_extraer(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_extraer )

    def menu_contextual_copiar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_copiar_1_1 )

    def menu_contextual_borrar(self, action):
        self.on_tb_toolbar_clicked( self.wb_tb_borrar )

    def menu_contextual_ver_juego_wiitdb(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina("http://wiitdb.com/Game/%s" % self.sel_juego.obj.idgame)
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
        
    def menu_contextual_editar_juego_wiitdb(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoEditarJuegoWiiTDB(self.sel_juego.obj)
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
            
    def menu_contextual_buscar_google(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_GOOGLE % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
        
    def menu_contextual_buscar_wikipedia(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_WIKIPEDIA % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
        
    def menu_contextual_buscar_youtube(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_YOUTUBE % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
        
    def menu_contextual_buscar_ign(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_IGN % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
            
    def menu_contextual_buscar_gamespot(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_GAMESPOT % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))
            
    def menu_contextual_buscar_vgchartz(self, action):
        if self.isSelectedGame():
            self.poolBash.nuevoTrabajoVerPagina(self.core.prefs.BUSCAR_URL_VGCHARTZ % ("wii %s" % util.get_title_for_search(self.sel_juego.obj)))
        else:
            self.alert("warning" , _("No has seleccionado ningun juego"))

    def cargarParticionesVista(self, treeview, callback_cursor_changed):
        
        if config.DEBUG:
            print "cargarParticionesVista"
        
        renderDevice = gtk.CellRendererText()
        renderTotal = gtk.CellRendererText()
        renderDevice.set_property("attributes", self.getEstilo_Mediano())

        columna1 = gtk.TreeViewColumn(_('Dispositivo'), renderDevice , text=0, foreground=2, background=3)
        columna2 = gtk.TreeViewColumn(_('Total'), renderTotal , text=1, foreground=2, background=3)

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
                                    gobject.TYPE_STRING,    # device
                                    gobject.TYPE_STRING,    # total
                                    gobject.TYPE_STRING,    # Color letra
                                    gobject.TYPE_STRING,    # Color fondo
                                )

        treeview.set_model(modelo)

        return modelo
        
    def cargarParticionesModelo(self , modelo , listaParticiones, filtrarTodo = False):
        
        if config.DEBUG:
            print "cargarParticionesModelo"
        
        modelo.clear()

        # me salto el 0
        i = 1
        for particion in listaParticiones:
            if( self.sel_parti == None or particion != self.sel_parti.obj ):
                iterador = modelo.insert(               i                           )
                modelo.set_value(iterador,0,            particion.device            )
                modelo.set_value(iterador,1,            "%.2f GB" % particion.total )
                modelo.set_value(iterador,2, particion.getColorForeground())
                modelo.set_value(iterador,3, particion.getColorBackground())
            # el contador esta fuera del if debido a:
            # si lo metemos la numeracion es secuencial, pero cuando insertarDeviceSeleccionado sea False
            # quiero reflejar los huecos. Esto permite un alineamiento con la lista del core
            i = i + 1

        # cuando hay mas de una particion y no se filtra el todo
        if (len(listaParticiones) != 1) and not filtrarTodo:
            # Añadir TODOS
            iterador = modelo.insert(0)
            if len(listaParticiones) == 0:
                label_primera_linea = _("BDD")
                tam_primera_linea = _("WBFS?")
            else:
                label_primera_linea = _("TODOS")
                tam_primera_linea = ""
            modelo.set_value(iterador,0,        label_primera_linea )
            modelo.set_value(iterador,1,        tam_primera_linea   )

    def cargarJuegosVista(self):
        
        if config.DEBUG:
            print "cargarJuegosVista"
        
        # Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
        tv_games = self.wb_tv_games

        self.renderEditableIDGAME = gtk.CellRendererText()
        self.renderEditableNombre = gtk.CellRendererText()
        self.renderEditableIDGAME.connect ("edited", self.editar_idgame)
        self.renderEditableNombre.connect ("edited", self.editar_nombre)
        render = gtk.CellRendererText()

        # prox versión meter background ----> foreground ... etc
        # http://www.pygtk.org/docs/pygtk/class-gtkcellrenderertext.html
        self.columna1 = columna1 = gtk.TreeViewColumn(_('IDGAME'), self.renderEditableIDGAME , text=0, foreground=8, background=9)
        self.columna2 = columna2 = gtk.TreeViewColumn(_('Nombre'), self.renderEditableNombre , text=1, foreground=8, background=9)
        self.columna3 = columna3 = gtk.TreeViewColumn(_('Size'), render , text=2, foreground=8, background=9)
        self.columna4 = columna4 = gtk.TreeViewColumn(_('Online?'), render , text=3, foreground=8, background=9)
        self.columna5 = columna5 = gtk.TreeViewColumn(_('Local'), render , text=4, foreground=8, background=9)
        self.columna6 = columna6 = gtk.TreeViewColumn(_('Fecha'), render , text=5, foreground=8, background=9)
        self.columna7 = columna7 = gtk.TreeViewColumn(_('Rating'), render , text=6, foreground=8, background=9)
        self.columna8 = columna8 = gtk.TreeViewColumn(_('Particion'), render , text=7, foreground=8, background=9)

        columna1.set_expand(False)
        columna1.set_min_width(79)
        columna1.set_reorderable(True)
        columna1.set_sort_order(gtk.SORT_DESCENDING)
        columna1.set_sort_column_id(0)

        columna2.set_expand(True)
        columna2.set_reorderable(True)
        columna2.set_sort_indicator(True)
        columna2.set_sort_order(gtk.SORT_DESCENDING)
        columna2.set_sort_column_id(1)

        columna3.set_expand(False)
        columna3.set_min_width(59)
        columna3.set_reorderable(True)
        columna3.set_sort_order(gtk.SORT_DESCENDING)
        columna3.set_sort_column_id(2)
        
        columna4.set_expand(False)
        columna4.set_min_width(80)
        columna4.set_reorderable(True)
        columna4.set_sort_order(gtk.SORT_ASCENDING)
        columna4.set_sort_column_id(3)
        
        columna5.set_expand(False)
        columna5.set_min_width(53)
        columna5.set_reorderable(True)
        columna5.set_sort_order(gtk.SORT_ASCENDING)
        columna5.set_sort_column_id(4)
        
        columna6.set_expand(False)
        columna6.set_min_width(66)
        columna6.set_reorderable(True)
        columna6.set_sort_order(gtk.SORT_ASCENDING)
        columna6.set_sort_column_id(5)
        
        columna7.set_expand(False)
        columna7.set_min_width(99)
        columna7.set_reorderable(True)
        columna7.set_sort_order(gtk.SORT_ASCENDING)
        columna7.set_sort_column_id(6)
        
        columna8.set_expand(False)
        columna8.set_min_width(84)
        columna8.set_reorderable(True)
        columna8.set_sort_order(gtk.SORT_ASCENDING)
        columna8.set_sort_column_id(7)

        tv_games.append_column(columna1)# IDGAME
        tv_games.append_column(columna2)# Nombre
        tv_games.append_column(columna4)# Online?
        tv_games.append_column(columna5)# Local
        tv_games.append_column(columna6)# Fecha
        #tv_games.append_column(columna7)# Rating
        #tv_games.append_column(columna8)# Device
        tv_games.append_column(columna3)# Tamaño

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
                gobject.TYPE_STRING,                        # Color fondo
                gobject.TYPE_STRING,                        # Color INFO
                )
        tv_games.set_model(modelo)

        return modelo
        

    def cargarJuegosModelo(self , modelo , listaJuegos):
        
        if config.DEBUG:
            print "cargarJuegosModelo"
        
        modelo.clear()
        i = 0
        for juego in listaJuegos:
            iterador = modelo.insert(i)
            # El modelo tiene una columna más no representada
            modelo.set_value(iterador,0,                juego.idgame)
            modelo.set_value(iterador,1,                juego.title)
            modelo.set_value(iterador,2, "%.2f GB" %    juego.size)

            juegoWiiTDB = juego.getJuegoWIITDB()            
            if juegoWiiTDB != None:

                modelo.set_value(iterador,3, juegoWiiTDB.getTextPlayersWifi(True))
                modelo.set_value(iterador,4, juegoWiiTDB.getTextPlayersLocal(True))
                modelo.set_value(iterador,5, juegoWiiTDB.getTextFechaLanzamiento(self.core, True))
                modelo.set_value(iterador,6, juegoWiiTDB.getTextRating(True))
                modelo.set_value(iterador,10, _("+Info"))

            else:
                
                modelo.set_value(iterador,3,  _("??"))
                modelo.set_value(iterador,4,  _("??"))
                modelo.set_value(iterador,5,  _("??"))
                modelo.set_value(iterador,6,  _("??"))
                modelo.set_value(iterador,10, _("??"))
                
            modelo.set_value(iterador,7, juego.particion.device)
            modelo.set_value(iterador,8, juego.particion.getColorForeground())
            modelo.set_value(iterador,9, juego.particion.getColorBackground())

            i = i + 1

    def editar_idgame( self, renderEditable, i, nuevoIDGAME):
        # renderEditable no se utiliza
        # i no se utiliza
        self.editar_idgame_verificando(nuevoIDGAME)

    def editar_idgame_verificando( self, nuevoIDGAME):
        if self.isSelectedPartition() and self.isSelectedGame():
            nuevoIDGAME = nuevoIDGAME.upper()
            if(self.sel_juego.obj.idgame != nuevoIDGAME):
                exp_reg = "[A-Z0-9]{6}"
                if (len(nuevoIDGAME) == 6) and re.match(exp_reg,nuevoIDGAME):
                    sql = util.decode('idgame=="%s" and idParticion=="%d"' % (nuevoIDGAME , self.sel_parti.obj.idParticion))
                    juego = session.query(Juego).filter(sql).first()
                    if juego == None:
                        if ( self.question(_('TRADUCIR_ADVERTENCIA_SEGURIDAD_RENAME_IDGAME') , ('\n%s => %s') % (self.sel_juego.obj.idgame , nuevoIDGAME)) ):
                            if self.core.renombrarIDGAME( self.sel_juego.obj , nuevoIDGAME ):
                                # modificamos el juego modificado de la BDD
                                # cambiar idgame de la bdd
                                self.sel_juego.obj.idgame = nuevoIDGAME
                                session.commit()

                                # Refrescamos del modelo la columna modificada
                                self.tv_games_modelo.set_value(self.sel_juego.it , 0 ,nuevoIDGAME)
                            else:
                                self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Ya hay un juego con ese IDGAME"))
                else:
                    self.alert('error' , _("Error: La longitud del IDGAME debe ser 6, y solo puede contener letras y numeros"))

    def editar_nombre( self, renderEditable, i, nuevoNombre):
        # renderEditable no se utiliza
        # i no se utiliza
        self.editar_nombre_verificando( nuevoNombre)
        
    def editar_nombre_verificando( self, nuevoNombre):        
        if self.isSelectedPartition() and self.isSelectedGame():
            nombreActual = self.sel_juego.obj.title
            if(nombreActual != nuevoNombre):
                if len(nuevoNombre) < config.TITULO_LONGITUD_MAX:
                    if not util.tieneCaracteresRaros(nuevoNombre , util.BLACK_LIST2):
                        if self.core.renombrarNOMBRE(self.sel_juego.obj , nuevoNombre):
                            # cambiar nombre en la bdd
                            self.sel_juego.obj.title = nuevoNombre
                            session.commit()

                            # Refrescamos del modelo la columna modificada
                            self.tv_games_modelo.set_value(self.sel_juego.it , 1 , nuevoNombre)
                        else:
                            self.alert('error' , _("Error renombrando"))
                    else:
                        self.alert('error' , _("Se han detectado caracteres no validos: %s") % (util.BLACK_LIST2))
                else:
                    self.alert('error' , _("Nuevo nombre es demasiado largo, intente con un texto menor de %d caracteres") % (config.TITULO_LONGITUD_MAX))

    def salir(self , widget=None, data=None):
        
        # guardar particion y juego seleccionados
        if self.isSelectedGame():
            self.core.prefs.idgame_seleccionado = self.sel_juego.obj.idgame
        if self.isSelectedPartition():
            self.core.prefs.device_seleccionado = self.sel_parti.obj.device

        # cerrar gui
        gtk.main_quit()

        # cerrar hilos esperando
        try:
            self.poolTrabajo.interrumpir()
            self.poolBash.interrumpir()
            self.animar.interrumpir()
            self.poolTrabajo.join()
            self.poolBash.join()
            self.animar.join()
        except AttributeError:
            pass

    def dialog_select(self, lista, titulo, label, boton_text):
        
        botones = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, str(boton_text), gtk.RESPONSE_ACCEPT)
        default_response = gtk.RESPONSE_CANCEL
        
        confirmar = gtk.Dialog(titulo, None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        botones)           
        confirmar.set_default_response(default_response)
        confirmar.set_position(gtk.WIN_POS_CENTER)
        confirmar.set_border_width(12)
        confirmar.vbox.set_spacing(6)
        
        ################################################################
        
        h1 = gtk.HBox(homogeneous=False, spacing=10)

        etiqueta = gtk.Label()
        etiqueta.set_text("%s" % label)
        etiqueta.set_use_markup(True)
        etiqueta.set_alignment(0.0 , 0.5)
        etiqueta.set_padding(5, -1)
        etiqueta.show()
        h1.pack_start(etiqueta, expand=False, fill=False, padding=0)

        liststore = gtk.ListStore(str)
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)  
        for elem in lista:
            combobox.append_text("%s" % (elem))
        combobox.set_active(0)
        combobox.show()
        h1.pack_start(combobox, expand=False, fill=False, padding=0)
        
        ################################################################
        
        # poner el hbox (columnas) en el vbox reservado del dialogo
        confirmar.vbox.pack_start(h1, True, True, 10)

        # calculos del pintado
        confirmar.show_all()
        
        # modal, esperando respuesta
        respuesta  = confirmar.run()
        
        # devuelve el elemento de la lista elegido
        if respuesta == gtk.RESPONSE_ACCEPT:
            seleccionado = lista[combobox.get_active()]
        else:
            seleccionado = None
        
        # destruir dialogo
        confirmar.destroy()
        
        return seleccionado

    '''
    question
    warning
    info
    error
    '''
    def alert(self, level, message, titulo = '', xml = False):
        
        titulo = str(titulo)
        message = str(message)
        if level == 'question':
            botones = (gtk.STOCK_YES, gtk.RESPONSE_ACCEPT, gtk.STOCK_NO, gtk.RESPONSE_REJECT)
            const_stock_icon = gtk.STOCK_DIALOG_QUESTION
            default_response = gtk.RESPONSE_REJECT
            if titulo == '':
                titulo = _("PREGUNTA:")
        elif level == 'warning':
            botones = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            const_stock_icon = gtk.STOCK_DIALOG_WARNING
            default_response = gtk.RESPONSE_ACCEPT
            if titulo == '':
                titulo = _("WARNING:")
        elif level == 'error':
            botones = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            const_stock_icon = gtk.STOCK_DIALOG_ERROR
            default_response = gtk.RESPONSE_ACCEPT
            if titulo == '':
                titulo = _("ERROR:")
        elif level == 'auth':
            botones = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            const_stock_icon = gtk.STOCK_DIALOG_AUTHENTICATION
            default_response = gtk.RESPONSE_ACCEPT
            if titulo == '':
                titulo = _("AUTENTIFICACION:")
        else:
            botones = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            const_stock_icon = gtk.STOCK_DIALOG_INFO
            default_response = gtk.RESPONSE_ACCEPT
            if titulo == '':
                titulo = _("INFORMACION:")
        
        confirmar = gtk.Dialog(titulo, None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        botones)           
        confirmar.set_default_response(default_response)
        confirmar.set_position(gtk.WIN_POS_CENTER)
        confirmar.set_default_size(-1,500)
        confirmar.set_border_width(12)
        confirmar.vbox.set_spacing(6)

        # poner icono a la ventana
        # 2º parametro: http://www.pygtk.org/docs/pygtk/gtk-constants.html#gtk-icon-size-constants
        logo = gtk.Image()
        logo.set_from_stock(const_stock_icon, gtk.ICON_SIZE_DIALOG)
        icon = confirmar.render_icon(const_stock_icon, gtk.ICON_SIZE_DIALOG)
        confirmar.set_icon(icon)

        h1 = gtk.HBox(homogeneous=False, spacing=10)
        h1.pack_start(logo, expand=True, fill=True, padding=10)
       
        ###############################
        view = TextViewCustom()
        view.cargar_tags_html()

        if not xml:
            if level == 'warning':
                color = "naranja"
            elif level == 'error':
                color = "rojo"
            else: # question | auth
                color = "negro"
            message = "<%s><b><pr>%s</pr></b></%s>" % (color, util.parsear_a_XML(message), color)

        xml_plantilla = """<?xml version="1.0" encoding="UTF-8"?>
        <xhtml>
            <margin8>
                <azul>
                    <big>
                        <u>
                            <pr>%s</pr><br />
                        </u>
                    </big>
                </azul>
            </margin8>
            <br />
            <margin12>
                %s<br />
            </margin12>
        </xhtml>
        """ % (util.parsear_a_XML(titulo), message)

        view.render_xml(xml_plantilla)
        ###############################

        sw1 = gtk.ScrolledWindow()
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw1.set_size_request(600, -1)
        sw1.add(view)

        h1.pack_start(sw1, expand=True, fill=True, padding=10)

        ###############################

        # poner el hbox (columnas) en el vbox reservado del dialogo
        confirmar.vbox.pack_start(h1, True, True, 10)

        # calculos del pintado
        confirmar.show_all()
        
        # modal, esperando respuesta
        respuesta  = confirmar.run()
        
        # destruir dialogo
        confirmar.destroy()
            
        return respuesta == gtk.RESPONSE_ACCEPT

    def question(self, pregunta, titulo = '', xml = False):
        return self.alert('question', pregunta, titulo, xml)
        
    def personalizar_nombre_juego_seleccionado(self):
        if self.sel_parti.it != None:
            self.wb_tv_games.grab_focus()
            path = self.sel_juego.get_path(self.wb_tv_games)
            self.wb_tv_games.set_cursor(path , self.columna2 , True)

        else:
            self.alert("warning" , _("No has seleccionado ninguna particion"))
    
    def isSelectedGame(self):
        return (self.sel_juego != None) and (self.sel_juego.it != None) and (self.sel_juego.obj != None)

    def isSelectedPartition(self):
        return (self.sel_parti != None) and (self.sel_parti.it != None) and (self.sel_parti.obj != None)
    
    def proponer_nombre_juego(self, juego):
        if self.isSelectedGame():
            if juego.idgame == self.sel_juego.obj.idgame:
                juegoWiiTDB = juego.getJuegoWIITDB() 
                if juegoWiiTDB is not None:
                    lista_propuestas = NonRepeatList()
                    lista_propuestas.append("%s (%s)" % (juego.title, _("actual")))
                    for descripcion in juegoWiiTDB.descripciones:
                        lista_propuestas.append(descripcion)
                    lista_propuestas.append(_("Personalizable ..."))
                        
                    descripcion = self.dialog_select(lista_propuestas,
                                        _("Renombrar el juego %s.") % juego.title,
                                        "<b>%s</b>\n\n<small><i>%s</i></small>" % (_("Nombres propuestos por la informacion WiiTDB"), _("NOTA: Este es el nombre que aparecera en el USB Loader.")),
                                        _("Renombrar")
                                        )
                    if isinstance(descripcion, JuegoDescripcion):
                        descripcion_formateada = util.quitarCaracteresRaros(descripcion.title)
                        self.editar_nombre_verificando(descripcion_formateada)
                    elif descripcion == _("Personalizable ..."):
                        self.personalizar_nombre_juego_seleccionado()

                else:
                    self.personalizar_nombre_juego_seleccionado()

    # callback de la señal "changed" del buscador
    # Refresca de la base de datos y filtra según lo escrito.
    def on_busqueda_changed(self , widget):
        
        if config.DEBUG:
            print "on_busqueda_changed"
        
        self.buscar = widget.get_text()
        self.lJuegos = self.buscar_juego_bdd(self.buscar)
        self.refrescarModeloJuegos( self.lJuegos )

    def leer_juegos_de_las_particiones(self, particiones):
        
        if config.DEBUG:
            print "leer_juegos_de_las_particiones"

        for particion in particiones:
            self.core.syncronizarJuegos(particion)

    def buscar_juego_bdd(self, buscar):
        
        if config.DEBUG:
            print "buscar_juego_bdd"

        subListaJuegos = []

        if not self.isSelectedPartition():
            sql = util.decode('title like "%%%s%%" or idgame like "%s%%"' % (buscar , buscar))
        else:
            sql = util.decode('idParticion="%d" and (title like "%%%s%%" or idgame like "%s%%")' % (self.sel_parti.obj.idParticion , buscar , buscar))

        query = session.query(Juego).filter(sql).order_by('lower(title)')
        for juego in query:
            subListaJuegos.append(juego)
        
        return subListaJuegos

    def refrescarModeloJuegos(self, listaJuegos):
        if config.DEBUG:
            print "refrescarModeloJuegos"

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

    def seleccionarFilaConValor(self , treeview , columna, valor, callback = True):
        
        if config.DEBUG:
            print "seleccionarFilaConValor (%s)" % valor
        
        i = 0
        salir = encontrado = False
        while (not salir) and (not encontrado):
            try:
                iter = treeview.get_model().get_iter(i)
                iter_valor = treeview.get_model().get_value(iter , columna)
                encontrado = (iter_valor == valor)
                if not encontrado:
                    i += 1
            except ValueError:
                salir = True
        if encontrado:
            treeview.get_selection().select_path(i)

        if callback:
            self.callback_treeview(treeview)

    def seleccionarPrimeraFila(self , treeview, callback = True):
        if config.DEBUG:
            print "seleccionarPrimeraFila"
        
        # selecciono el primero y provoco el evento
        iter_primero = treeview.get_model().get_iter_first()
        if iter_primero != None:
            treeview.get_selection().select_iter( iter_primero )
        if callback:
            self.callback_treeview(treeview)

    def refrescarEspacio(self):
        if config.DEBUG:
            print "refrescarEspacio"
        
        if self.isSelectedPartition():
            
            particion = self.sel_parti.obj
            
            self.info.arriba_usado = particion.usado
            self.info.arriba_total = particion.total

            sql = util.decode('idParticion = %d' % particion.idParticion)
            self.info.arriba_num_juegos = session.query(Juego).filter(sql).count()
            self.info.abajo_num_particiones = session.query(Particion).count()

    def refrescarInfoWiiTDB(self):
        
        if config.DEBUG:
            print "refrescarInfoWiiTDB"
            
        numInfos = 0
        query = session.query(Juego).group_by('idgame')
        for juego in query:
            if juego.getJuegoWIITDB() is not None:
                numInfos += 1
                    
        self.info.abajo_num_juegos_wiitdb = numInfos

    def refrescarNumCaratulas(self):

        if config.DEBUG:
            print "refrescarNumCaratulas"        
        
        juegos_sin_caratula = 0
        juegos_sin_disc_art = 0
        
        for juego in self.lJuegos:
            if not self.core.existeCaratula(juego.idgame):
                juegos_sin_caratula += 1
            if not self.core.existeDisco(juego.idgame):
                juegos_sin_disc_art += 1
        
        self.info.abajo_juegos_sin_caratula = juegos_sin_caratula
        self.info.abajo_juegos_sin_discart = juegos_sin_disc_art

    def refrescarTareasPendientes(self):
        
        if config.DEBUG:
            print "refrescarTareasPendientes"
        
        self.info.arriba_num_tareas = self.poolTrabajo.numTrabajos

        # mostrar espacio barra progreso    
        #self.mostrarHBoxProgreso()

    def getBuscarJuego(self, listaJuegos, idgame):
        
        if config.DEBUG:
            print "getBuscarJuego"
        
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
        
        if config.DEBUG:
            print "getBuscarParticion"
        
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

        if config.DEBUG:
            print "on_tv_games_cursor_changed"

        if self.sel_juego != None:
            self.sel_juego.actualizar_columna(treeview)
            if self.sel_juego.it != None:
                self.sel_juego.obj = self.getBuscarJuego(self.lJuegos, self.sel_juego.clave)
            else:
                self.sel_juego.obj = None
                
            # info wiitdb
            self.actualizar_textview_info_wiitdb()
            
            # caratulas
            self.ponerCaratula(self.sel_juego.clave, self.wb_img_caratula1)
            self.ponerDisco(self.sel_juego.clave , self.wb_img_disco1)

    # Click en particiones --> refresca la lista de juegos
    def on_tv_partitions_cursor_changed(self , treeview):
        
        if config.DEBUG:
            print "on_tv_partitions_cursor_changed"
        
        if self.sel_parti != None:
            self.sel_parti.actualizar_columna(treeview)
            if self.sel_parti.it != None:

                # selecciono la particion actual
                self.sel_parti.obj = self.getBuscarParticion(self.lParti, self.sel_parti.clave)
                
                # oculta partes del gui cuando esta en todo
                self.toggle_todo_particion()

                # refrescamos el modelo de particiones para la copia 1on1
                self.cargarParticionesModelo(self.tv_partitions2_modelo , self.lParti, True)
                
                #seleccionar primero
                self.seleccionarPrimeraFila( self.wb_tv_partitions2 )
                
                # refrescamos la lista de juegos, leyendo del core
                self.lJuegos = self.buscar_juego_bdd(self.buscar)
                
                # actualizar el modelo de juegos
                self.refrescarModeloJuegos( self.lJuegos )
                
                # refrescar espacio
                self.refrescarEspacio()

    def toggle_todo_particion(self):

        if not self.isSelectedPartition():

            # poner la columna titulo desactivada
            self.renderEditableIDGAME.set_property("editable", False)
            self.renderEditableNombre.set_property("editable", False)
            self.renderEditableNombre.set_property("attributes", self.getEstilo_grisGrande())

            self.wb_vboxProgresoEspacio.hide()
            self.wb_labelEspacio.hide()

            if config.REV != '':
                self.wb_principal.set_title('Wiithon %s (rev %s)' % (config.VER, config.REV))
                self.wb_aboutdialog.set_version("%s (rev %s)" % (config.VER, config.REV))
            else:
                self.wb_principal.set_title('Wiithon %s' % (config.VER))
                self.wb_aboutdialog.set_version("%s" % (config.VER))            
        else:
            
            # poner la columna titulo activada
            self.renderEditableIDGAME.set_property("editable", True)
            self.renderEditableNombre.set_property("editable", True)
            self.renderEditableNombre.set_property("attributes", self.getEstilo_azulGrande())
            
            self.wb_vboxProgresoEspacio.show()
            self.wb_labelEspacio.show()
            
            if config.REV != '':
                self.wb_principal.set_title('Wiithon %s (rev %s) %s' % (config.VER, config.REV, self.sel_parti.obj.fabricante))
                self.wb_aboutdialog.set_version("%s (rev %s)" % (config.VER, config.REV))
            else:
                self.wb_principal.set_title('Wiithon %s %s' % (config.VER, self.sel_parti.obj.fabricante))
                self.wb_aboutdialog.set_version("%s" % (config.VER))

    def on_tv_partitions2_cursor_changed(self , treeview):
        
        if config.DEBUG:
            print "on_tv_partitions2_cursor_changed"
        
        self.sel_parti_1on1.actualizar_columna(treeview)

        if self.sel_parti_1on1.it != None:
            
            # le selecciono la particion actual al 1on1
            self.sel_parti_1on1.obj = self.getBuscarParticion(self.lParti, self.sel_parti_1on1.clave)

    def ponerCaratula(self, IDGAME, widget_imagen):
        
        destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
        
        if IDGAME is not None:

            # existe            
            if self.core.existeCaratula(IDGAME):
                destinoCaratula = self.core.getRutaCaratula(IDGAME)
                #   existe y esta descargando
                if not util.esPNG(destinoCaratula):
                    destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
                #else:   existe y esta descargado
            # no existe        
            else:
                self.poolBash.nuevoTrabajoDescargaCaratula( IDGAME )
                destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")

        widget_imagen.set_from_file( destinoCaratula )

    def ponerDisco(self, IDGAME, widget_imagen):     

        destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")

        if IDGAME is not None:

            # existe            
            if self.core.existeDisco(IDGAME):
                destinoDisco = self.core.getRutaDisco(IDGAME)
                #   existe y esta descargando
                if not util.esPNG(destinoDisco):
                    destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
                #else:   existe y esta descargado
            # no existe        
            else:
                self.poolBash.nuevoTrabajoDescargaDisco( IDGAME )
                destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")

        widget_imagen.set_from_file( destinoDisco )

    def actualizar_textview_info_wiitdb(self):
        
        error = False

        if self.isSelectedGame():
            
            if not self.wiitdb_mutex:

                juego = self.sel_juego.obj.getJuegoWIITDB()
                if juego != None:

                    # titulo y synopsis
                    hayPrincipal = False
                    haySecundario = False
                    i = 0
                    while not hayPrincipal and i<len(juego.descripciones):
                        descripcion = juego.descripciones[i]
                        hayPrincipal = descripcion.lang == self.core.prefs.LANG_PRINCIPAL and (descripcion.synopsis != "")
                        if hayPrincipal:
                            title = descripcion.title
                            synopsis = descripcion.synopsis
                        i += 1

                    if not hayPrincipal:
                        haySecundario = False
                        i = 0
                        while not haySecundario and i<len(juego.descripciones):
                            descripcion = juego.descripciones[i]
                            haySecundario = descripcion.lang == self.core.prefs.LANG_SECUNDARIO and (descripcion.synopsis != "")
                            if haySecundario:
                                title = descripcion.title
                                synopsis = descripcion.synopsis
                            i += 1

                    if not hayPrincipal and not haySecundario:
                        title = juego.name
                        synopsis = _('No se ha encontrado synopsis')

                    # generos
                    muestra =   [    [],[]     ]
                    for genero in session.query(Genero).order_by('idGenero'):
                        muestra[0].append(genero.idGenero)
                        muestra[1].append(len(genero.juego_wiitdb))
                    s = MuestraEstadistica(muestra[0], muestra[1])
                    letra_media = 16
                    amplitud = 20
                    generos = ""
                    i = 0
                    for genero in juego.genero:
                        tam = letra_media * 1 + ((len(genero.juego_wiitdb) - s.media()) * amplitud / 100)
                        if tam > 63:
                            tam = 63
                        generos += "<font%d><pr>%s</pr></font%d>" % (tam, util.parsear_a_XML(genero.nombre), tam)
                        i += 1
                        if i != len(juego.genero):
                            generos += "<rojo><b><pr>, </pr></b></rojo>"
                    
                    # accesorios obligatorios
                    xml_inject_accesorios_obligatorios = ""
                    for accesorio in juego.obligatorio:
                        xml_inject_accesorios_obligatorios += "<img>%s</img>" % (os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO, "%s.jpg" % accesorio.nombre))

                    # accesorios opcionales
                    xml_inject_accesorios_opcionales = ""
                    for accesorio in juego.opcional:
                        xml_inject_accesorios_opcionales += "<img>%s</img>" % (os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO, "%s.jpg" % accesorio.nombre))
                    
                    xml_inject = ""
                    if xml_inject_accesorios_obligatorios != "":
                        xml_inject += "<b><big><azul><pr>%s</pr></azul></big></b><br />" % _("ACCESORIOS: ")
                        xml_inject += "%s" % xml_inject_accesorios_obligatorios
                        xml_inject += "<br />"
                        
                    if xml_inject_accesorios_opcionales != "":
                        xml_inject += "<b><big><verde><pr>%s</pr></verde></big></b><br />" % _("OPCIONALES: ")
                        xml_inject += "%s" % xml_inject_accesorios_opcionales
                        xml_inject += "<br />"
                    

                    xml_plantilla = """<?xml version="1.0" encoding="UTF-8"?>
    <xhtml>
        <margin8>
            <superbig>
                <b>
                    <verde><pr>%s</pr></verde>
                </b>
            </superbig>
            <br />
            <big>
                <azul>
                    <pr>%s</pr>
                </azul>
            </big>
            %s
            <br />
            <b><i><pr>%s</pr></i></b>
                <i><pr>%s</pr></i><br />
            <b><i><pr>%s</pr></i></b>
                <i><pr>%s/%s</pr></i>
            <br />
            <b><i><pr>%s</pr></i></b>
                <i><pr>%s</pr></i>
            <br />
            <b><i><pr>%s</pr></i></b>
                <i><pr>%s</pr></i>
            <br />
            <b><i><pr>%s</pr></i></b>
                <i><pr>%s</pr></i>
            <br />
            %s
            </margin8>
    </xhtml>
                    """ % (
                    util.parsear_a_XML(title),
                    _("GENERO: "), generos,
                    _("Fecha de lanzamiento: "), juego.getTextFechaLanzamiento(self.core),
                    _("Desarrolador/Editorial: "), util.parsear_a_XML(juego.developer), util.parsear_a_XML(juego.publisher),
                    _("Num. jugadores en off-line: "), util.parsear_a_XML(juego.getTextPlayersLocal()),
                    _("Capacidad On-line: "), util.parsear_a_XML(juego.getTextPlayersWifi()),
                    _("Clasificacion parental: "), util.parsear_a_XML(juego.getTextRating()),
                    xml_inject
                    )
                    
                    xml_plantilla_descripcion = """<?xml version="1.0" encoding="UTF-8"?>
    <xhtml>                
        <margin8>
            <big>
                <verde>
                    <pr>%s</pr>
                </verde>
            </big>
            <justificar>
                <pr>%s</pr><br />
            </justificar>
        </margin8>
    </xhtml>
                    """ % (_("DESCRIPCION: "), util.parsear_a_XML(synopsis))

                else:
                    xml_plantilla_descripcion = """<?xml version="1.0" encoding="UTF-8"?>
    <xhtml>                
        <margin8>
            <big>
                <verde>
                    <pr>%s</pr>
                </verde>
            </big>
            <justificar>
                <pr>%s</pr><br />
            </justificar>
        </margin8>
    </xhtml>
                    """ % (_("DESCRIPCION: "), _("Sin descripcion."))
                    xml_plantilla = """<?xml version="1.0" encoding="UTF-8"?>
    <xhtml>
        <margin8>
            <superbig>
                <b>
                    <verde><pr>%s</pr></verde>
                </b>
            </superbig>
            <br />
            <h1><pr>%s</pr></h1>
        </margin8>
    </xhtml>
                    """ % ( util.parsear_a_XML(self.sel_juego.obj.title),
                            _('No hay datos de este juego. Intente actualizar la base de datos de WiiTDB.')
                            )
                            
            else:
                error = True

        else:
            error = True

        if error:
            xml_plantilla_descripcion = """<?xml version="1.0" encoding="UTF-8"?>
<xhtml>                
    <margin8>
        <big>
            <verde>
                <pr>%s</pr>
            </verde>
        </big>
        <justificar>
            <pr>%s</pr><br />
        </justificar>
    </margin8>
</xhtml>
            """ % (_("DESCRIPCION: "), _("Sin descripcion."))
            xml_plantilla = """<?xml version="1.0" encoding="UTF-8"?>
<xhtml>
    <margin8>
        <h1><pr>%s</pr></h1>
    </margin8>
</xhtml>
                """ % (_("No has seleccionado ningun juego"))

        self.tvc_info_juego.render_xml(xml_plantilla)
        self.tvc_descripcion.render_xml(xml_plantilla_descripcion)


    def on_tv_games_click_event(self, widget, event):
        if event.button == 3:
            popup = self.uimgr.get_widget('/GamePopup')
            popup.popup(None, None, None, event.button, event.time)

    def on_tb_toolbar_clicked(self , id_tb):
        
        if config.DEBUG:
            print "on_tb_toolbar_clicked"
        
        if(not self.isSelectedPartition() and id_tb != self.wb_tb_copiar_SD and id_tb != self.wb_tb_acerca_de and id_tb != self.wb_tb_refrescar_wbfs and id_tb != self.wb_tb_preferencias):
            self.alert("warning" , _("Tienes que seleccionar una particion WBFS para realizar esta accion"))

        elif(id_tb == self.wb_tb_acerca_de):
            self.wb_aboutdialog.run()
            self.wb_aboutdialog.hide()
            
        elif(id_tb == self.wb_tb_refrescar_wbfs):
            self.refrescarParticionesWBFS()

        elif(id_tb == self.wb_tb_copiar_1_1):
            
            if self.isSelectedPartition():
                if len(self.lParti) > 1:                
                    res = self.wb_dialogo_copia_1on1.run()
                    self.wb_dialogo_copia_1on1.hide()
                    parti_origen = self.sel_parti.obj
                    parti_destino = self.sel_parti_1on1.obj

                    # salir por Cancelar ---> 0
                    # salir por Escape ---> -4
                    if(res > 0):
                        
                        juegosParaClonar = []
                        juegosExistentesEnDestino = []

                        if(res == 1):
                            if self.isSelectedGame():

                                juegosParaClonar.append( self.sel_juego.obj )
                                pregunta = _("Desea copiar el juego %s a la particion %s?") % (self.sel_juego.obj, parti_destino)

                            else:
                                self.alert("warning" , _("No has seleccionado ningun juego"))

                        elif(res == 2):
                            
                            # cada juego del origen se busca en la lista de juegos de destino
                            sql = util.decode('idParticion = %d' % parti_origen.idParticion)
                            for juego in session.query(Juego).filter(sql):
                                sql = util.decode('idgame = "%s" and idParticion = %d' % (juego.idgame, parti_destino.idParticion))
                                juegoDestino = session.query(Juego).filter(sql).first()
                                if juegoDestino is None:
                                    juegosParaClonar.append( juego )
                                else:
                                    juegosExistentesEnDestino.append(juegoDestino)
                                    
                            pregunta  = "%s %s:\n\n" % (_("Se van a copiar los siguientes juegos a"), parti_destino)
                            
                            i = 0
                            for juego in juegosParaClonar:
                                pregunta += "%s\n" % (juego)
                                i += 1
                                if i >= config.MAX_LISTA_COPIA_1on1:
                                    pregunta += "[...] (%d %s)\n" % (len(juegosParaClonar)-config.MAX_LISTA_COPIA_1on1, _("juegos mas"))
                                    break
                            pregunta += "\n\n%s %s:\n\n" % (_("A continuacion se listan los juego que NO van a ser copiados por ya estar en la particion de destino"),parti_destino)
                            i = 0
                            for juego in juegosExistentesEnDestino:
                                pregunta += "%s\n" % (juego)
                                i += 1
                                if i >= config.MAX_LISTA_COPIA_1on1:
                                    pregunta += "[...] (%d %s)\n" % (len(juegosExistentesEnDestino)-config.MAX_LISTA_COPIA_1on1, _("juegos mas"))
                                    break
                            pregunta += "\n%s" % _("Empezar a copiar?")
                            
                        if len(juegosParaClonar) > 0:
                            if((self.question(pregunta))):
                                self.poolTrabajo.nuevoTrabajoClonar( juegosParaClonar, parti_destino )
                        else:
                            self.alert('info',_("No hay nada que copiar a %s") % (parti_destino))
                else:
                    self.alert("warning" , _("Debes tener al menos 2 particiones WBFS para hacer copias 1:1"))
            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

        elif(id_tb == self.wb_tb_borrar):

            if self.isSelectedPartition():
                
                if self.isSelectedGame():
                    
                    if( self.question(_('Quieres borrar el juego: %s?') % (self.sel_juego.obj)) ):
                        # borrar del HD
                        if self.core.borrarJuego( self.sel_juego.obj ):
                            
                            # borrar de la bdd
                            session.delete(self.sel_juego.obj)
                            
                            # go
                            session.commit()
                            
                            # borrar caratulas no usadas
                            sql = util.decode('idgame=="%s"' % self.sel_juego.obj.idgame)
                            if session.query(Juego).filter(sql).count() == 0:

                                # borrar disco
                                self.core.borrarDisco( self.sel_juego.obj )

                                # borrar caratula
                                self.core.borrarCaratula( self.sel_juego.obj )
                            
                            # actualizar valores de usado/libre/total
                            self.sel_parti.obj.refrescarEspacioLibreUsado(self.core)
                            
                            # restar la info wiitdb
                            self.refrescarInfoWiiTDB()
                            
                            # Selecciona el primer juego
                            self.seleccionarFilaConValor(self.wb_tv_partitions, 0 , self.sel_parti.obj.device)

                        else:
                            self.alert("warning" , _("Error borrando el juego %s") % self.sel_juego.obj)

                else:
                    self.alert("warning" , _("No has seleccionado ningun juego"))

            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

        elif(id_tb == self.wb_tb_extraer):

            if self.isSelectedGame():

                fc_extraer = SelectorFicheros(
                    _('Elige un directorio donde extraer la ISO de %s') \
                        % (self.sel_juego.obj.idgame), gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
                fc_extraer.addFavorite( self.core.prefs.ruta_extraer_iso )
                
                res = fc_extraer.run()
                if(res == gtk.RESPONSE_OK):

                    ruta_selec = fc_extraer.get_current_folder()

                    extraer = False
                    if self.core.existeExtraido(self.sel_juego.obj , ruta_selec):
                        extraer = self.question(_('Desea reemplazar la iso del juego %s?') % (self.sel_juego.obj))
                    else:
                        if not util.space_for_dvd_iso_wii(ruta_selec):
                            self.alert("warning" , _("Espacio libre insuficiente para extraer la ISO"))
                        else:
                            extraer = True
                        
                    if extraer:
                        # nueva ruta favorita
                        self.core.prefs.ruta_extraer_iso = ruta_selec

                        # extraer *juego* en la ruta seleccionada
                        self.poolTrabajo.nuevoTrabajoExtraer(self.sel_juego.obj , fc_extraer.get_filename())

                fc_extraer.destroy()
            else:
                self.alert("warning" , _("No has seleccionado ningun juego"))

        elif(id_tb == self.wb_tb_renombrar):
            self.proponer_nombre_juego( self.sel_juego.obj )

        elif(id_tb == self.wb_tb_anadir or id_tb == self.wb_tb_anadir_directorio):

            if self.isSelectedPartition():

                if(id_tb == self.wb_tb_anadir):
                    fc_anadir = SelectorFicheros(_("Elige una imagen ISO valida para Wii"))
                    fc_anadir.set_select_multiple(True)
                    fc_anadir.crearFiltrosISOyRAR()
                    fc_anadir.addFavorite( self.core.prefs.ruta_anadir )

                elif(id_tb == self.wb_tb_anadir_directorio):
                    fc_anadir = SelectorFicheros(_("Elige un directorio"), gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
                    fc_anadir.addFavorite( self.core.prefs.ruta_anadir_directorio )

                if fc_anadir.run() == gtk.RESPONSE_OK:

                    if(id_tb == self.wb_tb_anadir):
                        self.core.prefs.ruta_anadir = fc_anadir.get_current_folder()
                    elif(id_tb == self.wb_tb_anadir_directorio):
                        self.core.prefs.ruta_anadir_directorio = fc_anadir.get_current_folder()

                    listaISO = []
                    listaRAR = []
                    listaDirectorios = []
                    buffer_errorNoMetidos = _("Algunos juegos no se han introducido:\n\n")
                    hayNoMetidos = False
                    for fichero in fc_anadir.get_filenames():
                        if( os.path.isdir( fichero ) ):
                            listaDirectorios.append(fichero)
                        elif( util.getExtension(fichero) == "rar" ):
                            listaRAR.append(fichero)
                        elif( util.getExtension(fichero) == "iso" ):
                            idgame = util.getMagicISO(fichero)
                            if idgame is not None:
                                sql = util.decode("idgame=='%s' and idParticion=='%d'" % (idgame , self.sel_parti.obj.idParticion))
                                juego = session.query(Juego).filter(sql).first()
                                if juego is None:
                                    listaISO.append(fichero)

                                else:
                                    hayNoMetidos = True
                                    buffer_errorNoMetidos += _("%s ya existe en %s\n") % (juego.title, juego.particion.device)
                            else:
                                hayNoMetidos = True
                                buffer_errorNoMetidos += _("%s no es un ISO de Wii.\n") % (fichero)

                    if hayNoMetidos:
                        self.alert('warning', buffer_errorNoMetidos)

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

                fc_copiar_SD = SelectorFicheros(_('Paso 1 de 2: Elige un directorio para las CARATULAS'), gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
                fc_copiar_SD.addFavorite( self.core.prefs.ruta_copiar_caratulas )

                if ( fc_copiar_SD.run() == gtk.RESPONSE_OK ):
                    fc_copiar_discos_SD = SelectorFicheros(_('Paso 2 de 2: Elige un directorio para los DISCOS'), gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
                    fc_copiar_discos_SD.addFavorite(self.core.prefs.ruta_copiar_discos)

                    if(fc_copiar_discos_SD.run() == gtk.RESPONSE_OK):
                        self.core.prefs.ruta_copiar_caratulas = fc_copiar_SD.get_current_folder()
                        self.core.prefs.ruta_copiar_discos = fc_copiar_discos_SD.get_current_folder()

                        # copiar toda la lista de juegos
                        query = session.query(Juego).order_by('idParticion, lower(title)').group_by('idgame')
                        for juego in query:
                            self.poolBash.nuevoTrabajoCopiarCaratula(juego , fc_copiar_SD.get_filename())
                            self.poolBash.nuevoTrabajoCopiarDisco(juego, fc_copiar_discos_SD.get_filename())

                    fc_copiar_discos_SD.destroy()

                fc_copiar_SD.destroy()

            else:
                self.alert("warning" , _("No tienes ningun juego"))

        elif(id_tb == self.wb_tb_preferencias):
            if not self.wiitdb_mutex:
                self.wb_prefs.run()
                self.ocultar_preferencias()
            else:
                self.alert("error" , _("Hay una tarea que esta bloqueando las preferencias.\n\nEspere a que finalize."))
                
    def ocultar_preferencias(self, actualizar_preferencias = True):
        if actualizar_preferencias:
            self.poolTrabajo.actualizarPreferencias()
            self.poolBash.actualizarPreferencias()
        self.wb_prefs.hide()
        
######### HERRAMIENTAS Y UTILIDADES #################

    def on_formatear_bdd_clicked(self, boton):
        
        if self.question(_('Estas seguro de querer formatear la BDD? Se borraran tus preferencias y la informacion de los juegos')):
            util.borrarBDD(wiitdb_schema.Base.metadata)
            util.crearBDD(wiitdb_schema.Base.metadata)
            self.core.prefs.cargarPreferenciasPorDefecto()
            self.ocultar_preferencias()
            self.alert("warning" , _("La BDD ha sido formateada.") + '\n' + _("Es recomendable que reinicie la aplicacion"))
            self.refrescarParticionesWBFS()

    def on_button_formatear_wbfs_clicked(self, boton):
        listaParticiones = self.core.sincronizarParticiones(config.DETECTOR_WBFS_FAT32)
        if len(listaParticiones) == 0:
            self.alert("warning" , "%s\n%s" % (_("Has conectado el disco duro? No se ha encontrado ninguna particion valida."), _("Comprueba que tienes la particion FAT32 montada.")))
        else:
            particion = self.dialog_select( listaParticiones, _("Elige la particion WBFS con la que va a trabajar : "), "<b>%s</b>" % _("Lista de particiones autodetectadas : "), _("Formatear a WBFS"))
            if particion is not None:
                try:
                    if self.question(_("Realmente, desea formatear a WBFS la particion %s? (S/N) ") % particion):
                        if self.core.formatearWBFS(particion):
                            self.ocultar_preferencias()
                            self.refrescarParticionesWBFS()
                            self.alert("info" , _("%s se ha formateado correctamente") % particion)
                        else:
                            self.alert("error" , _("Error al formatear %s") % particion)
                    else:
                        self.alert("info" , _("No se ha formateado %s") % particion)

                except KeyboardInterrupt:
                    self.alert("warning" , "%s\n%s" % (_("Interrumpido por el usuario."), _("No se ha formateado %s") % particion))

    def on_button_abrir_carpeta_caratulas_clicked(self, boton):
        comando = '%s "%s"' % (self.core.prefs.COMANDO_ABRIR_CARPETA, config.HOME_WIITHON_CARATULAS)
        util.call_out_null(comando)
        
    def on_button_abrir_carpeta_discart_clicked(self, boton):
        comando = '%s "%s"' % (self.core.prefs.COMANDO_ABRIR_CARPETA, config.HOME_WIITHON_DISCOS)
        util.call_out_null(comando)
                
########## WIITDB ###########
                
    def on_tb_actualizar_wiitdb_clicked(self, boton):
        
        if not self.wiitdb_mutex:
            
            if (self.question("""
                    <b>
                        <pr>%s</pr>
                        <br />
                        <br />
                        <azul><pr>%s</pr></azul>
                    </b>
                """ % (
                        _("Seguro que deseas descargar informacion de los juegos de WiiTDB?"),
                        self.core.prefs.URL_ZIP_WIITDB
                        ),
                        xml = True) ):
                self.poolTrabajo.nuevoTrabajoActualizarWiiTDB(self.core.prefs.URL_ZIP_WIITDB)
        else:
            self.alert("warning" , _("Ya estas descargando la informacion WiiTDB ..."))
        
    def callback_empieza_importar(self, xml):
        self.juegos = 0
        self.descripciones = 0
        self.generos = 0
        self.online_features = 0
        self.accesorios = 0
        self.companies = 0
        self.actualizarLabel(_("Empezando a obtener datos de juegos desde WiiTDB"))
        self.actualizarFraccion(0.0)
        
        # evitar usar preferencias mientras mete datos
        self.wiitdb_mutex = True
        # cerrar preferencias sin guardar cambios
        self.ocultar_preferencias(False)

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
        self.wiitdb_mutex = False
        self.mostrarError(_("Error importando %s: %s") % (xml, motivo))
        
    def callback_empieza_descarga(self, url):
        self.actualizarLabel(_("Descargando WiiTDB desde %s, espere unos minutos ...") % url)
        self.actualizarFraccion(0.01)
        
    def callback_empieza_descomprimir(self, zip):
        self.actualizarLabel(_("Empezando a descomprimir la informacion WiiTDB"))
        self.actualizarFraccion(0.99)

    def callback_termina_importar(self, xml, todos):
        if todos:
            self.wiitdb_mutex = False
            self.actualizarLabel(_("Finalizada satisfactoriamente la importacion de datos desde WiiTDB"))
            self.actualizarFraccion(1.0)
            gobject.idle_add(self.refrescarModeloJuegos, self.lJuegos)
            gobject.idle_add(self.refrescarInfoWiiTDB)

############# METODOS que modifican el GUI, si se llaman desde hilos, se hacen con gobject

    def borrar_archivo_preguntando(self, archivo):
        if self.question(_('Deseas borrar el archivo %s?') % archivo):
            if os.path.exists(archivo):
                os.remove(archivo)

    def mostrarHBoxProgreso(self):
        self.wb_box_progreso.show()
        return False

    def ocultarHBoxProgreso(self):
        self.wb_box_progreso.hide()
        return False
        
    def mostrarError(self, mensaje):
        self.alert('error' , mensaje)

    def actualizarOrientation(self, orientation):
        self.wb_progreso1.set_orientation(orientation) 

    def actualizarLabel( self, etiqueta ):
        self.wb_progreso1.set_text( etiqueta )

    def actualizarFraccion( self , fraccion ):
        self.wb_progreso1.set_fraction( fraccion )

    def termina_trabajo_anadir(self, fichero, DEVICE):
        
        # leer IDGAME del juego añadido
        IDGAME = util.getMagicISO(fichero)

        # consultamos al wiithon wrapper info sobre el juego con nueva IDGAME
        # lo añadimos a la lista
        juegoNuevo = self.core.new_game_from_HDD(DEVICE, IDGAME)
        
        # refrescar su espacio uso/libre/total
        juegoNuevo.particion.refrescarEspacioLibreUsado(self.core)
        
        # limpio el filtro antes de seleccionar
        self.wb_busqueda.set_text('')

        # seleccionamos la particion y la fila del juego añadido       
        self.seleccionarFilaConValor(self.wb_tv_partitions, 0 , juegoNuevo.particion.device)
        self.seleccionarFilaConValor(self.wb_tv_games, 0 , juegoNuevo.idgame)
        
        # refrescar num juegos con info wiitdb
        self.refrescarInfoWiiTDB()
        
        # pregunta arreglar nombre
        if self.core.prefs.proponer_nombre:
            self.proponer_nombre_juego(juegoNuevo)

    def termina_trabajo_copiar(self, juego , particion):

        # consultamos al wiithon wrapper info sobre el juego con nueva IDGAME
        # lo añadimos a la lista
        juegoNuevo = self.core.new_game_from_HDD(particion.device, juego.idgame)

        # refrescar su espacio uso/libre/total
        particion.refrescarEspacioLibreUsado(self.core)
        
        # limpio el filtro antes de seleccionar
        self.wb_busqueda.set_text('')
        
        # seleccionamos la particion y la fila del juego añadido
        self.seleccionarFilaConValor(self.wb_tv_partitions, 0 , juegoNuevo.particion.device)
        self.seleccionarFilaConValor(self.wb_tv_games, 0 , juegoNuevo.idgame)

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
        listaISO = NonRepeatList()
        listaRAR = NonRepeatList()
        listaDirectorios = NonRepeatList()
        for fichero in tuplaArrastrados:
            if fichero.startswith("file://"):
                fichero = fichero.replace("file://" , "")
                if os.path.exists(fichero):
                    if(util.getExtension(fichero)=="iso") and self.core.prefs.DRAG_AND_DROP_JUEGOS:
                        listaISO.append(fichero)
                    elif(util.getExtension(fichero)=="rar") and self.core.prefs.DRAG_AND_DROP_JUEGOS:
                        listaRAR.append(fichero)
                    elif( os.path.isdir( fichero ) ) and self.core.prefs.DRAG_AND_DROP_JUEGOS:
                        listaDirectorios.append(fichero)
                    elif(util.esImagen(fichero) and self.core.prefs.DRAG_AND_DROP_LOCAL): # Arrastrar imagenes (png, jpg, gif) desde el escritorio

                        if self.isSelectedGame():

                            if self.core.prefs.DESTINO_ARRASTRE == 'C':
                                ruta = self.core.getRutaCaratula(self.sel_juego.obj.idgame)
                                shutil.copy(fichero, ruta)
                                comando = 'mogrify -resize %dx%d! "%s"' % (self.core.prefs.WIDTH_COVERS, self.core.prefs.HEIGHT_COVERS, ruta)
                                util.call_out_null(comando)
                                self.ponerCaratula(self.sel_juego.obj.idgame, self.wb_img_caratula1)
                            elif self.core.prefs.DESTINO_ARRASTRE == 'D':
                                ruta = self.core.getRutaDisco(self.sel_juego.obj.idgame)
                                shutil.copy(fichero, ruta)
                                comando = 'mogrify -resize %dx%d! "%s"' % (self.core.prefs.WIDTH_DISCS, self.core.prefs.HEIGHT_DISCS, ruta)
                                util.call_out_null(comando)
                                self.ponerDisco(self.sel_juego.obj.idgame, self.wb_img_disco1)

            elif fichero.startswith("http://"):
                # Arrastrar imagenes (png, jpg, gif) desde el navegador
                if(util.esImagen(fichero) and self.core.prefs.DRAG_AND_DROP_HTTP):
                    
                    if self.isSelectedGame():
                        
                        if self.core.prefs.DESTINO_ARRASTRE == 'C':
                            ruta = self.core.getRutaCaratula(self.sel_juego.obj.idgame)
                            util.descargar(fichero, ruta)
                            comando = 'mogrify -resize %dx%d! "%s"' % (self.core.prefs.WIDTH_COVERS, self.core.prefs.HEIGHT_COVERS, ruta)
                            util.call_out_null(comando)
                            self.ponerCaratula(self.sel_juego.obj.idgame, self.wb_img_caratula1)
                        elif self.core.prefs.DESTINO_ARRASTRE == 'D':
                            ruta = self.core.getRutaDisco(self.sel_juego.obj.idgame)
                            util.descargar(fichero, ruta)
                            comando = 'mogrify -resize %dx%d! "%s"' % (self.core.prefs.WIDTH_DISCS, self.core.prefs.HEIGHT_DISCS, ruta)
                            util.call_out_null(comando)
                            self.ponerDisco(self.sel_juego.obj.idgame, self.wb_img_disco1)

        if len(listaISO) > 0 or len(listaRAR) > 0 or len(listaDirectorios) > 0:

            if self.isSelectedPartition():

                if len(listaISO) > 0:
                    listaISO.sort()
                    self.poolTrabajo.nuevoTrabajoAnadir( listaISO , self.sel_parti.obj.device)
                    
                if len(listaRAR) > 0:
                    listaRAR.sort()
                    self.poolTrabajo.nuevoTrabajoDescomprimirRAR( listaRAR , self.sel_parti.obj)

                if len(listaDirectorios) > 0:
                    listaDirectorios.sort()
                    self.poolTrabajo.nuevoTrabajoRecorrerDirectorio( listaDirectorios , self.sel_parti.obj)                
                    
            else:
                self.alert("warning" , _("No has seleccionado ninguna particion"))

    def callback_empieza_progreso(self, trabajo):
        self.hiloCalcularProgreso = HiloCalcularProgreso( trabajo, self.actualizarLabel , self.actualizarFraccion )
        self.hiloCalcularProgreso.start()
        gobject.idle_add(self.actualizarFraccion , 0.0 )

    def callback_termina_progreso(self, trabajo):
        gobject.idle_add(self.actualizarFraccion , 1.0 )

    def callback_empieza_trabajo_anadir(self, trabajo):
        pass

    def callback_termina_trabajo_anadir(self, core, trabajo , fichero, device, rar_preguntar_borrar_iso = True, rar_preguntar_borrar_rar = False):
        if trabajo.exito:
            gobject.idle_add( self.termina_trabajo_anadir , fichero , device)
        if trabajo.padre is not None:
            if trabajo.padre.tipo == str(8): # DESCOMPRIMIR_RAR = str(8)
                if rar_preguntar_borrar_iso:
                    gobject.idle_add( self.borrar_archivo_preguntando , fichero)
                if rar_preguntar_borrar_rar:
                    gobject.idle_add( self.borrar_archivo_preguntando , trabajo.padre.origen)

    # Al terminar hay que seleccionar la partición destino y el juego copiado
    def callback_termina_trabajo_copiar(self, trabajo, juego, particion):
        if trabajo.exito:
            gobject.idle_add( self.termina_trabajo_copiar , juego , particion)

    def callback_nuevo_trabajo(self, trabajo):
        gobject.idle_add( self.refrescarTareasPendientes )

    def callback_empieza_trabajo(self, trabajo):
        if config.DEBUG:
            print _("Empieza %s") % trabajo

        gobject.idle_add( self.refrescarTareasPendientes )
        
        if not self.poolTrabajo.estaOcupado():
            gobject.idle_add(self.actualizarFraccion , 1.0 )
            gobject.idle_add(self.actualizarLabel , "%s" % trabajo )

    def callback_termina_trabajo(self, trabajo):
        # No hay trabajo cuando el contador este a 1, que es el propio trabajo que da la señal
        '''
        if(self.poolTrabajo.numTrabajos <= 1):
            gobject.timeout_add( 5000, self.ocultarHBoxProgreso )
        '''

        # al final, por ser bloqueante
        if not trabajo.exito:
            gobject.idle_add( self.mostrarError , trabajo.error )
        
        if config.DEBUG:
            print _("Termina: %s") % trabajo

    def callback_empieza_trabajo_extraer(self, trabajo):
        pass

    def callback_termina_trabajo_extraer(self, trabajo):
        pass

    def callback_empieza_trabajo_copiar(self, trabajo):
        pass

    def callback_termina_trabajo_descargar_caratula(self, trabajo, idgame):
        if trabajo.exito:
            if self.isSelectedGame():
                if idgame == self.sel_juego.obj.idgame:
                    gobject.idle_add( self.ponerCaratula , idgame , self.wb_img_caratula1)
        else:
            print _("Falla la descarga de la caratula de %s") % idgame
            
        gobject.idle_add( self.refrescarNumCaratulas )            

    def callback_termina_trabajo_descargar_disco(self, trabajo, idgame):
        if trabajo.exito:
            if self.isSelectedGame():
                if idgame == self.sel_juego.obj.idgame:
                    gobject.idle_add( self.ponerDisco , idgame , self.wb_img_disco1)
        else:
            print _("Falla la descarga del disco de %s") % idgame
        
        gobject.idle_add( self.refrescarNumCaratulas )

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
