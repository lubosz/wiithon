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
from preferencias import Preferencia
from animar import Animador
from fila_treeview import FilaTreeview
from wiitdb_schema import Juego, Particion, JuegoWIITDB, JuegoDescripcion

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

    # Union de la listas de juegos de cada particion
    lJuegos = None
    
    # subconjunto de la lista de juegos, filtrada por el core
    lJuegos_filtrada = None

    # Representación de la fila seleccionada en los distintos treeviews
    sel_juego = FilaTreeview()
    sel_parti = None
    sel_parti_1on1 = None
    
    # tiempo del ultimo click en tv_games
    ultimoClick = 0
    
    # builder para el glade
    alert_glade = None

    def __init__(self, core):
        GtkBuilderWrapper.__init__(self,
                                   os.path.join(config.WIITHON_FILES_RECURSOS_GLADE,
                                                'wiithon.ui'))
                                                
        self.alert_glade = gtk.Builder()
        self.alert_glade.add_from_file( os.path.join(config.WIITHON_FILES_RECURSOS_GLADE  , 'alerta.ui') )
        self.alert_glade.set_translation_domain( config.APP )

        self.core = core
        
        self.buscar = ""
        self.modo = "ver" # ver | manager
        
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

        # permite usar hilos con PyGTK http://faq.pygtk.org/index.py?req=show&file=faq20.006.htp
        # modo seguro con hilos
        gobject.threads_init()

        self.wb_principal.set_title('Wiithon')
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
                                    callback_termina_trabajo_descargar_caratula = self.callback_termina_trabajo_descargar_caratula,
                                    callback_termina_trabajo_descargar_disco = self.callback_termina_trabajo_descargar_disco
                                    )
        self.poolBash.setDaemon(True)
        self.poolBash.start()
        
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
            
        # Animación circulo
        destinoIcono = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "idle-icon.png")
        self.wb_estadoBatch.set_from_file( destinoIcono )

        # Animacion que define si hay actividad de la pool batch
        self.animar = Animador( self.wb_estadoBatch , self.poolBash , self.poolTrabajo)
        self.animar.setDaemon(True)
        self.animar.start()
            
        # reffresco inicial en busca de particiones wbfs
        self.refrescarParticionesWBFS()
        
        # advertencia si no encuentra
        if(len(self.lParti) == 0):
            if (os.geteuid() != 0) and (len(self.lJuegos)==0):
                self.alert("warning" , _("No se han detectado particiones WBFS.\nSi has conectado una particion WBFS y no ha sido detectada, es debido a que no hay permisos de lectura y escritura.\nPara solucionarlo siga los pasos de la guia de instalacion."))
            else:
                if(len(self.lJuegos)>0):
                    self.alert("warning" , _("No hay particiones WBFS, solo puede ver sus juegos acumuladas en %s") % (config.APP))
                else:
                    self.alert("warning" , _("No hay particiones WBFS, conecte y refresque"))
        
        # pongo el foco en el buscador
        if( len(self.lJuegos)>0 ):
            self.wb_busqueda.grab_focus()
        else:
            self.wb_tb_refrescar_wbfs.grab_focus()

    def refrescarParticionesWBFS(self):
        
        if not self.poolTrabajo.estaOcupado():
            
            # oculto la fila de progreso
            self.wb_box_progreso.hide()

            self.lParti = self.core.getListaParticiones()
            if(len(self.lParti) == 0):
                # establecemos el modo de wiithon
                self.modo = "ver"

                # poner la columna titulo desactivada
                self.renderEditableIDGAME.set_property("editable", False)
                self.renderEditableNombre.set_property("editable", False)
                self.renderEditableNombre.set_property("attributes", self.getEstilo_grisGrande())
                
                # limpiar particiones del modelo
                self.tv_partitions_modelo.clear()

                # No hay particion seleccionada
                self.sel_parti = None
                self.sel_parti_1on1 = None

                # cargar datos desde la base de datos
                self.lJuegos = []
                self.lJuegos_filtrada = self.refrescarListaJuegos()

                #ocultar algunas coasa
                self.wb_vboxProgresoEspacio.hide()
                self.wb_labelEspacio.hide()
                
                self.wb_label_numParticionesWBFS.set_label(_("¡No hay particiones WBFS!"))
            else:
                # establecemos el modo de wiithon, hay particiones que gestionar
                self.modo = "manager"
                
                # poner la columna titulo activada
                self.renderEditableIDGAME.set_property("editable", True)
                self.renderEditableNombre.set_property("editable", True)
                self.renderEditableNombre.set_property("attributes", self.getEstilo_azulGrande())
                
                # carga el modelo de datos del TreeView de particiones
                self.cargarParticionesModelo(self.tv_partitions_modelo , self.lParti)
                
                self.lJuegos = self.sincronizarParticionesWBFSconBDD(self.lParti)
                self.lJuegos_filtrada = None

                self.sel_parti = FilaTreeview()
                self.sel_parti.obj = self.lParti[0]               
                self.sel_parti_1on1 = FilaTreeview()
                
                # seleccionar primera fila de particiones y por tanto de juego
                self.seleccionarPrimeraFila(self.wb_tv_partitions)
                
                #mostrar algunas coasa
                self.wb_vboxProgresoEspacio.show()
                self.wb_labelEspacio.show()
                
                if len(self.lParti) == 1:
                    self.wb_label_numParticionesWBFS.set_label(_("1 particion WBFS"))
                else:
                    self.wb_label_numParticionesWBFS.set_label(_("%d particiones WBFS") % (len(self.lParti)))


            # 1º descargamos lo que vemos EN ORDEN
            # 2º despues descargamos el resto de juegos sin importar el orden
            i=0
            while i<2:
                if i==1:
                    lista = self.lJuegos_filtrada
                else:
                    lista = self.lJuegos
                if lista:
                    for juego in lista:
                        if not self.core.existeCaratula(juego.idgame):
                            self.poolBash.nuevoTrabajoDescargaCaratula( juego )
                        if not self.core.existeDisco(juego.idgame):
                            self.poolBash.nuevoTrabajoDescargaDisco( juego )
                i += 1
            
        else:
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
                gobject.TYPE_STRING,    # device
                gobject.TYPE_STRING    # total
                                )

        treeview.set_model(modelo)

        return modelo

    def cargarJuegosVista(self):
        # Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
        tv_games = self.wb_tv_games

        # FIXME
        #tv_games.set_enable_search(True)

        self.renderEditableIDGAME = gtk.CellRendererText()
        self.renderEditableNombre = gtk.CellRendererText()
        self.renderEditableIDGAME.connect ("edited", self.editar_idgame)
        self.renderEditableNombre.connect ("edited", self.editar_nombre)
        #self.renderEditableNombre.connect ("editing-started", self.empieza_editar)
        #self.renderEditableNombre.connect ("editing-canceled", self.cancela_editar)
        render = gtk.CellRendererText()

        # prox versión meter background ----> foreground ... etc
        # http://www.pygtk.org/docs/pygtk/class-gtkcellrenderertext.html
        self.columna1 = columna1 = gtk.TreeViewColumn(_('IDGAME'), self.renderEditableIDGAME , text=0)
        self.columna2 = columna2 = gtk.TreeViewColumn(_('Nombre'), self.renderEditableNombre , text=1)
        self.columna3 = columna3 = gtk.TreeViewColumn(_('Tamanio'), render , text=2)

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

        tv_games.append_column(columna1)
        tv_games.append_column(columna2)
        tv_games.append_column(columna3)

        tv_games.connect('cursor-changed', self.on_tv_games_cursor_changed)

        modelo = gtk.ListStore (
                gobject.TYPE_STRING,                        # IDGAME
                gobject.TYPE_STRING,                        # Nombre
                gobject.TYPE_STRING,                        # Tamaño
                )
        tv_games.set_model(modelo)

        return modelo


    def cargarParticionesModelo(self , modelo , listaParticiones , deviceActual = "$%&/()=!"):
        modelo.clear()
        i = 0
        for p in listaParticiones:
            if(p.device != deviceActual):
                iterador = modelo.insert(i)
                modelo.set_value(iterador,0,p.device)
                modelo.set_value(iterador,1,"%.2f GB" % p.total)
            # el contador esta fuera del if debido a:
            # si lo metemos la numeracion es secuencial, pero cuando insertarDeviceSeleccionado sea False
            # quiero reflejar los huecos. Esto permite un alineamiento con la lista del core
            i = i + 1

    def editar_idgame( self, renderEditable, i, nuevoIDGAME):
        if self.sel_juego.it != None:
            nuevoIDGAME = nuevoIDGAME.upper()
            if(self.sel_juego.obj.idgame != nuevoIDGAME):
                exp_reg = "[A-Z0-9]{6}"
                if re.match(exp_reg,nuevoIDGAME):
                    sql = util.decode('idgame=="%s" and device=="%s"' % (nuevoIDGAME , self.sel_parti.obj.device))
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


    def cargarJuegosModelo(self , modelo , listaJuegos):
        modelo.clear()
        i = 0
        for juego in listaJuegos:
            iterador = modelo.insert(i)
            # El modelo tiene una columna más no representada
            modelo.set_value(iterador,0,                juego.idgame)
            modelo.set_value(iterador,1,                juego.title)
            modelo.set_value(iterador,2, "%.2f GB" %    juego.size)
            i = i + 1

    def salir(self , widget=None, data=None):

        # guardar cambios en las preferencias
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

        # configure the label text:
        alert_msg = self.alert_glade.get_object('lbl_message')
        alert_msg.set_text(message)

        # configure the icon to display
        img = self.alert_glade.get_object('img_alert')

        try:
            img.set_from_stock(level_icons[level], gtk.ICON_SIZE_DIALOG)
        except IndexError:
            img.set_from_stock(level_icons['info'], gtk.ICON_SIZE_DIALOG)

        # configure the buttons
        btn_ok = self.alert_glade.get_object('btn_ok')
        btn_no = self.alert_glade.get_object('btn_no')

        if level_buttons[level][0]:
            btn_ok.set_label(level_buttons[level][0])
        else:
            btn_ok.set_visible(False)

        if level_buttons[level][1]:
            btn_no.set_label(level_buttons[level][1])
        else:
            btn_no.hide()

        self.alert_glade.get_object(config.GLADE_ALERTA).set_title(level)
        res = self.alert_glade.get_object(config.GLADE_ALERTA).run()
        self.alert_glade.get_object(config.GLADE_ALERTA).hide()

        return res

    def question(self, pregunta):
        return self.alert('question', pregunta)

    # callback de la señal "changed" del buscador
    # Refresca de la base de datos y filtra según lo escrito.
    def on_busqueda_changed(self , widget):
        self.buscar = widget.get_text()
        self.lJuegos_filtrada = self.refrescarListaJuegos()
        self.refrescarEspacio()

    # refresco desde el disco duro (lento)
    def sincronizarParticionesWBFSconBDD(self, particiones):

        # Borrar todas las relaciones juego-particion
    
        listaJuegosAcumulados = NonRepeatList()
        for particion in particiones:
            # obtener los juegos de esa particion
            listaJuegos = self.core.getListaJuegos(particion)

            i = 0
            # merge con la base de datos
            while i < len(listaJuegos):
                session.merge(listaJuegos[i])
                i += 1

            # union con el total
            listaJuegosAcumulados.extend(listaJuegos)

        # hacer efectivos los querys sql acumulados en el bucle
        session.commit()

        return listaJuegosAcumulados

    def refrescarListaJuegos(self):

        if self.sel_parti != None:
            sql = util.decode('juego.device="%s" and (juego.title like "%%%s%%" or juego.idgame like "%s%%")' % (self.sel_parti.obj.device , self.buscar , self.buscar))
            query = session.query(Juego).outerjoin(JuegoWIITDB).filter(sql).order_by('lower(title)')
        else:
            sql = util.decode('juego.title like "%%%s%%" or juego.idgame like "%s%%"' % (self.buscar , self.buscar))
            query = session.query(JuegoWIITDB).outerjoin(Juego).filter(sql).order_by('lower(title)')
            
        subListaJuegos = []
        # ordenado por nombre, insensible a mayusculas
        for juego in query:
            print juego.juego_wiitdb
            subListaJuegos.append(juego)

        # cargar la lista sobre el Treeview
        self.cargarJuegosModelo(self.tv_games_modelo , subListaJuegos)

        # seleccionar primera fila del treeview de juegos
        self.seleccionarPrimeraFila(self.wb_tv_games)
        
        return subListaJuegos

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
        if self.sel_parti == None:
            return
            
        info = self.core.getEspacioLibre(self.sel_parti.obj.device)
        usado = info[0]
        libre = info[1]
        total = info[2]

        self.wb_labelEspacio.set_text("%.2f GB / %.2f GB" % (usado , total))
        try:
            porcentaje = usado * 100.0 / total
        except ZeroDivisionError:
            porcentaje = 0.0
            
        numJuegos = len(self.lJuegos)
        numJuegos_filtrados = len(self.lJuegos_filtrada)
        if numJuegos_filtrados == numJuegos:
            self.wb_progresoEspacio.set_text(_("%d juegos") % (numJuegos))
        else:
            self.wb_progresoEspacio.set_text(_("%d/%d juegos") % (numJuegos_filtrados, numJuegos))
        self.wb_progresoEspacio.set_fraction( porcentaje / 100.0 )

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
        if idgame == None:
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
        if device == None:
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
                self.sel_juego.obj = self.getBuscarJuego(self.lJuegos, self.sel_juego.clave)
                self.ponerCaratula(self.sel_juego.clave, self.wb_img_caratula1)
                self.ponerDisco(self.sel_juego.clave , self.wb_img_disco1)

    # Click en particiones --> refresca la lista de juegos
    def on_tv_partitions_cursor_changed(self , treeview):
        if self.sel_parti != None:
            self.sel_parti.actualizar_columna(treeview)
            if self.sel_parti.it != None:

                # selecciono la particion actual
                self.sel_parti.obj = self.getBuscarParticion(self.lParti, self.sel_parti.clave)

                # refrescamos el modelo de particiones para la copia 1on1
                self.cargarParticionesModelo(self.tv_partitions2_modelo , self.lParti , self.sel_parti.obj.device)
                
                #seleccionar primero
                self.seleccionarPrimeraFila( self.wb_tv_partitions2 )
                
                # refrescamos la lista de juegos, leyendo del core
                self.lJuegos_filtrada = self.refrescarListaJuegos()

                # refrescar espacio
                self.refrescarEspacio()

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
                
                    juego = self.sel_juego.obj.juego_wiitdb
                    
                    if juego != None:
                        
                        self.ponerCaratula(juego.idgame, self.wb_img_caratula2)
                        self.ponerDisco(juego.idgame, self.wb_img_disco2)

                        self.wb_ficha_idgame.set_text( juego.idgame )
                        if juego.fecha_lanzamiento != None:
                            self.wb_ficha_fecha_lanzamiento.set_text( "%s" % (juego.fecha_lanzamiento) )
                        else:
                            self.wb_ficha_fecha_lanzamiento.set_text( _("Desconocido") )
                        self.wb_ficha_desarrollador.set_text( juego.developer )
                        self.wb_ficha_editor.set_text( juego.publisher )
                        
                        hayPrincipal = False
                        haySecundario = False
                        i = 0
                        while not hayPrincipal and i<len(juego.descripciones):
                            descripcion = juego.descripciones[i]
                            if descripcion.lang == "EN":
                                haySecundario = True
                            if descripcion.lang == "ES":
                                hayPrincipal = True
                            if hayPrincipal or haySecundario:
                                title = descripcion.title
                                synopsis = descripcion.synopsis
                                haySecundario = False
                            i += 1
                                
                        if hayPrincipal or haySecundario:
                            self.wb_ficha_titulo.set_text( title )
                            self.wb_ficha_synopsis_buffer.set_text( synopsis )
                        else:
                            self.wb_ficha_titulo.set_text( juego.name )
                            self.wb_ficha_synopsis_buffer.set_text( "" )
                        
                        buffer = ""
                        for genero in juego.genero:
                            buffer += genero.nombre + ", "
                        self.wb_ficha_genero.set_text( buffer )
                        
                        buffer = ""
                        for accesorio in juego.obligatorio:
                            buffer += "%s, " % accesorio.nombre
                            print os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO , "%s.jpg" % accesorio.nombre)
                        for accesorio in juego.opcional:
                            buffer += "%s (opcional), " % accesorio.nombre
                            print os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES_ACCESORIO , "%s.jpg" % accesorio.nombre)
                        self.wb_ficha_accesorio.set_text( buffer )
                        
                        buffer = ""    
                        for rating_content in juego.rating_contents:
                            buffer += "%s, " % rating_content.valor
                        self.wb_ficha_ranking.set_text( "%s (%s+): %s" % (juego.rating_type.tipo, juego.rating_value.valor , buffer) )
                        
                        if juego.wifi_players == 0:
                            self.wb_ficha_online.set_text( _("No") )
                        else:
                            buffer = ""
                            for feature_online in juego.features:
                                buffer += "%s, " % feature_online.valor
                            if juego.wifi_players == 1:
                                buffer = _("Sí, 1 jugador (%s)") % buffer
                            else:
                                buffer = _("Sí, %d jugadores (%s)") % (juego.wifi_players, buffer)
                            self.wb_ficha_online.set_text( buffer )
                            
                        if juego.input_players == 1:
                            self.wb_ficha_num_jugadores.set_text( _("1 jugador") )
                        else:
                            self.wb_ficha_num_jugadores.set_text( _("%d jugadores") % juego.input_players )
                                                
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
                
                if(res > 0):
                    device_destino = self.sel_parti_1on1.obj.device
                    juegosParaClonar = []
                    juegosExistentesEnDestino = []

                    if(res == 1):
                        if self.sel_juego.it != None:
                            juegosParaClonar.append( util.clonarOBJ(self.sel_juego.obj) )
                            
                            pregunta = _("Desea copiar el juego %s (%s) a la particion %s?") % (self.sel_juego.obj.title, self.sel_juego.obj.idgame, device_destino)

                        else:
                            self.alert("warning" , _("No has seleccionado ningun juego"))

                    elif(res == 2):
                        for juego in self.lJuegos_filtrada:
                            juegosParaClonar.append( util.clonarOBJ(juego) )
                    
                        self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 1 , self.sel_parti_1on1.obj.device)

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
                        self.alert('info',_("No hay nada que copiar en %s") % (device_destino))
                
                self.wb_dialogo_copia_1on1.hide()
            else:
                self.alert("warning" , _("Debes tener al menos 2 particiones WBFS para hacer copias 1:1"))

        elif(id_tb == self.wb_tb_borrar):
            if self.sel_juego.it != None:
                if self.modo == "ver":
                    if ( self.question(_('Advertencia de borrar %s en modo ver') % (self.sel_juego.obj)) == 1 ):
                        if self.sel_juego.obj != None:
                            
                            # borrar disco
                            self.core.borrarDisco( self.sel_juego.obj )

                            # borrar caratula
                            self.core.borrarCaratula( self.sel_juego.obj )

                            # borrar de la bdd
                            session.delete( self.sel_juego.obj )

                            # borrar de la tabla
                            self.tv_games_modelo.remove( self.sel_juego.it )
                            
                            # Borrar de las listas
                            self.lJuegos.remove( self.sel_juego.obj )
                            self.lJuegos_filtrada.remove( self.sel_juego.obj )

                            # seleccionar el primero
                            self.seleccionarPrimeraFila(self.wb_tv_games)

                else:
                    if( self.question(_('Quieres borrar el juego con %s?') % (self.sel_juego.obj.title)) == 1 ):
                        # borrar del HD
                        if self.core.borrarJuego( self.sel_parti.obj.device , self.sel_juego.obj.idgame ):
                            self.refrescarParticionesWBFS()
                        else:
                            self.alert("warning" , _("Error borrando"))

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
                fc_extraer.set_current_folder(self.preferencia.ruta_extraer_iso)

                if(fc_extraer.run() == gtk.RESPONSE_OK):

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
                    filter.set_name(_('Imagen ISO para Wii'))
                    filter.add_pattern('*.iso')
                    #filter.add_pattern('*.rar')
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

                    ficherosSeleccionados = []
                    for fichero in fc_anadir.get_filenames():
                        if( os.path.isdir( fichero ) ):
                            ficherosSeleccionados.append(fichero)
                        elif( util.getExtension(fichero) == "iso" ):
                            idgame = util.getMagicISO(fichero)
                            if idgame != None:
                                sql = util.decode('idgame=="%s" and device=="%s"' % (idgame , self.sel_parti.obj.device))
                                self.juegoNuevo = session.query(Juego).filter(sql).first()
                                if self.juegoNuevo == None:
                                    ficherosSeleccionados.append(fichero)
                                else:
                                    self.alert('warning',_("El juego ya esta metido, como %s") % (self.juegoNuevo))

                    if len(ficherosSeleccionados) > 0:
                        # ordenar la ruta de archivos
                        ficherosSeleccionados.sort()
                        #Meter los juegos
                        self.poolTrabajo.nuevoTrabajoAnadir( ficherosSeleccionados , self.sel_parti.obj.device)

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

############# METODOS que modifican el GUI, si se llaman desde hilos, se hacen con gobject

    def ocultarHBoxProgreso(self):
        self.wb_box_progreso.hide()
        return False

    def actualizarLabel( self, etiqueta ):
        self.wb_progreso1.set_text( etiqueta )

    def actualizarFraccion( self , fraccion ):
        self.wb_progreso1.set_fraction( fraccion )

    def refrescarParticionesYSeleccionarJuego(self, IDGAME, DEVICE):
        self.seleccionarFilaConValor(self.wb_tv_partitions, len(self.lParti) , 1 , DEVICE)
        self.seleccionarFilaConValor(self.wb_tv_games, len(self.lJuegos_filtrada) , 1 , IDGAME)
        
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
                        os.system("mogrify -resize 160x224! %s" % (ruta))
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

    def callback_termina_trabajo_anadir(self, trabajo , idgame, device):
        if trabajo.exito:
            gobject.idle_add( self.refrescarParticionesYSeleccionarJuego , idgame , device)
            
    # Al terminar hay que seleccionar la partición destino y el juego copiado
    def callback_termina_trabajo_copiar(self, trabajo, juego, device):
        if trabajo.exito:
            gobject.idle_add( self.refrescarParticionesYSeleccionarJuego , juego.idgame , device)

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
        if trabajo.exito:
            if juego.idgame == self.sel_juego.obj.idgame:
                gobject.idle_add( self.ponerCaratula , juego.idgame , self.wb_img_caratula1)
        else:
            print _("Falla la descarga de la caratula de %s") % juego
        
    def callback_termina_trabajo_descargar_disco(self, trabajo, juego):
        if trabajo.exito:
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
        while not self.interrumpido:
            try:
                # si aún no existe el fichero que contiene los mensajes, esperamos:
                # a) a que el fichero exista
                # b) desde otro hilo nos den orden de interrupción
                if os.path.exists(config.HOME_WIITHON_LOGS_PROCESO):

                    try:
                        for linea in file(config.HOME_WIITHON_LOGS_PROCESO):
                            ultimaLinea = linea

                        cachos = ultimaLinea.split(config.SEPARADOR)

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
