#!/usr/bin/python
# vim: set fileencoding=utf-8 :

# local
import util
from builder_wrapper import GtkBuilderWrapper
from trabajo import PoolTrabajo

# externo
import gtk , gobject , pango 
import os , time
import config , sys
from threading import Thread

class WiithonGUI(GtkBuilderWrapper):

	def __init__(self, core):				
		# Constructor padre
		
		GtkBuilderWrapper.__init__(self, config.WIITHON_FILES + '/recursos/glade/wiithon.ui')
		
		self.core = core
				
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
		self.wb_principal.show()

		self.wb_tb_anadir.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_anadir_directorio.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_extraer.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_renombrar.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_clasificar1.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_borrar.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_copiar_SD.connect('clicked' , self.on_tb_toolbar_clicked)
		self.wb_tb_preferencias1.connect('clicked' , self.on_tb_toolbar_clicked)

		# oculto la fila de la progreso
		self.wb_box_progreso.hide()
		
		#ocultar buscador (de momento)
		self.wb_hbox6.hide()
		self.wb_hbox7.hide()
		self.wb_expander1.hide()

		'''
		# No necesitamos la señal, para esta versión
		try:
			self.wb_entry1.connect('icon-release', self.clear_search_cb)
		except TypeError:
			print "Cuidado: Necesitas una versión GTK >= 2.16 para visualizar algunas opciones."
		
		self.wb_titulo_categorias.set_attributes( self.getEstilo_azulGrande() )
		self.wb_titulo_etiquetas.set_attributes( self.getEstilo_azulGrande() )
		'''

		self.wb_principal.connect('destroy', self.salir)

		# carga la vista del TreeView de particiones
		self.tv_partitions_modelo = self.cargarParticionesVista()

		# carga la vista del TreeView de juegos
		self.tv_games_modelo = self.cargarJuegosVista()

		listaParticiones = self.core.getListaParticiones()
		
		if(len(listaParticiones) == 0):
			destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
			self.wb_img_caratula1.set_from_file( destinoCaratula )

			destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
			self.wb_img_disco1.set_from_file( destinoDisco )
			
			self.alert("warning" , _("No se han encontrado particiones WBFS"))
		else:
			# carga el modelo de datos del TreeView de particiones
			self.cargarParticionesModelo(self.tv_partitions_modelo , listaParticiones)

			# selecciono la primera partición
			# indirectamente se carga:
			# lee el modelo de datos de la partición seleccionada
			# tambien refresca la lista de juegos del CORE
			self.seleccionarPrimeraFila( self.wb_tv_partitions , self.on_tv_partitions_cursor_changed)

			# descargar caratulas desde un hilo
			self.poolBash = PoolTrabajo( self.core , 6)
			self.poolBash.setDaemon(True)
			self.poolBash.start()
			
			for IDGAME in self.listaJuegos:
				self.poolBash.nuevoTrabajoDescargaCaratula( IDGAME )
				self.poolBash.nuevoTrabajoDescargaDisco( IDGAME )
				self.poolBash.nuevoTrabajoVerificarJuego( IDGAME )

			# Trabajador, se le mandan trabajos de barra de progreso		
			self.poolTrabajo = PoolTrabajo( self.core )
			self.poolTrabajo.setDaemon(True)
			self.poolTrabajo.start()

			# Para atender mensajes
			self.hiloAtenderMensajes = HiloAtenderMensajes( self.core , self.poolTrabajo , self.wb_progreso1 , self )
			self.hiloAtenderMensajes.setDaemon(True)
			self.hiloAtenderMensajes.start()

		# pongo el foco en los TreeView de juegos
		self.wb_tv_games.grab_focus()
		
	def getEstilo_azulGrandeFondoRojo(self):
		atributos = self.getEstilo_azulGrande()
		
		atributos.insert(pango.AttrBackground(0xFFFF,0x1111,0x1111,0,-1))	
		
		return atributos
	
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
		
	'''
	def clear_search_cb(self, widget, position, event):
		if event.button == 1:
			widget.set_text('')
	'''

	def cargarParticionesVista(self):
		tv_partitions = self.wb_tv_partitions

		render = gtk.CellRendererText()

		columna1 = gtk.TreeViewColumn(_('Dispositivo'), render , text=1)
		columna2 = gtk.TreeViewColumn(_('Fabricante'), render , text=2)

		tv_partitions.append_column(columna1)
		tv_partitions.append_column(columna2)

		tv_partitions.connect('cursor-changed', self.on_tv_partitions_cursor_changed)

		modelo = gtk.ListStore (gobject.TYPE_INT , gobject.TYPE_STRING, gobject.TYPE_STRING)
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

	def edit_amount( self, renderEditable, i, nuevoNombre ):
		if self.iteradorJuegoSeleccionado != None:
			nombreActual = self.seleccionJuegoSeleccionado.get_value(self.iteradorJuegoSeleccionado,2)
			if(nombreActual != nuevoNombre):
				if self.core.renombrarISO(self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado , nuevoNombre):
					self.tv_games_modelo.set_value(self.iteradorJuegoSeleccionado,2,nuevoNombre)
				else:
					print "Error renombrando"

	def cargarJuegosVista(self):
		# Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
		tv_games = self.wb_tv_games
		
		# ¿Como aplico propiedades style?
		#tv_games.set_property("even-row-color" , gtk.gdk.Color(0xFFFF,0x0,0x0) )
		#tv_games.set_property("odd-row-color" ,   gtk.gdk.Color(0x0 , 0x0 , 0x0) )

		renderEditable = gtk.CellRendererText()
		renderEditable.set_property("editable", True)
		renderEditable.set_property("attributes", self.getEstilo_azulGrande() )
		renderEditable.connect ("edited", self.edit_amount)
		render = gtk.CellRendererText()
		#check = gtk.CellRendererToggle()

		self.columna1 = columna1 = gtk.TreeViewColumn(_('IDGAME'), render , text=1)
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

		modelo = gtk.ListStore (	gobject.TYPE_INT ,	# orden (campo oculto)
						gobject.TYPE_STRING,	# IDGAME
						gobject.TYPE_STRING,	# Nombre
						gobject.TYPE_STRING,	# Tamaño
						)
		tv_games.set_model(modelo)

		return modelo

	def cargarJuegosModelo(self , modelo , listaJuegos):
		if listaJuegos:
			modelo.clear()
			i = 0			
			for juego in listaJuegos:
				iterador = modelo.insert(i)
				# El modelo tiene una columna más no representada
				modelo.set_value(iterador,0, i )
				modelo.set_value(iterador,1, juego[0])
				modelo.set_value(iterador,2, juego[1])
				modelo.set_value(iterador,3, "%.2f GB" % float(juego[2]))
				i = i + 1

	def salir(self , widget=None, data=None):
		try:
			self.hiloAtenderMensajes.interrumpir()
			self.poolTrabajo.interrumpir()
			self.poolBash.interrumpir()
		except AttributeError:
			pass
		gtk.main_quit()

	def alert(self, level, message):
		alert_glade = gtk.Builder()
		alert_glade.add_from_file( config.WIITHON_FILES + '/recursos/glade/alerta.ui' )
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

	def refrescarListaJuegos(self):
		# recargar el modelo de datos la lista de juegos
		self.listaJuegos = self.core.getListaJuegos( self.DEVICEParticionSeleccionada )
		self.cargarJuegosModelo( self.tv_games_modelo , self.listaJuegos )
		self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed)

	def seleccionarPrimeraFila(self , treeview , callback):
		# selecciono el primero y provoco el evento
		iter_primero = treeview.get_model().get_iter_first()
		if iter_primero != None:
			treeview.get_selection().select_iter( iter_primero )
		callback( treeview )

	# Click en particiones --> refresca la lista de juegos
	def on_tv_partitions_cursor_changed(self , treeview):
		# particion seleccionado
		self.seleccionParticionSeleccionada, self.iteradorParticionSeleccionada  = self.wb_tv_partitions.get_selection().get_selected()
		if self.iteradorParticionSeleccionada != None:		
			# establece en el core la nueva partición seleccionada
			self.core.setParticionSeleccionada( self.seleccionParticionSeleccionada.get_value(self.iteradorParticionSeleccionada,0) )
						
			# sincroniza la variable DEVICE con el core
			self.DEVICEParticionSeleccionada = self.core.getDeviceSeleccionado()

			# refrescamos la lista de juegos
			self.refrescarListaJuegos()

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
		if(id_tb == self.wb_tb_borrar):
			if self.iteradorJuegoSeleccionado != None:
				if (self.question(_('¿Quieres borrar el juego con ID = "%s"?' % self.IDGAMEJuegoSeleccionado)) == 1):
					# borrar del HD
					self.core.borrarJuego( self.DEVICEParticionSeleccionada , self.IDGAMEJuegoSeleccionado )

					# borrar de la tabla
					self.tv_games_modelo.remove( self.iteradorJuegoSeleccionado )

					# seleccionar el primero
					self.seleccionarPrimeraFila( self.wb_tv_games , self.on_tv_games_cursor_changed)
			else:
				self.alert("warning" , _("No has seleccionado ningun juego"))
		elif(id_tb == self.wb_tb_extraer):
			if self.iteradorJuegoSeleccionado != None:
				'''
				Tarea EXTRAER JUEGO
				'''
				self.poolTrabajo.nuevoTrabajoExtraer( self.IDGAMEJuegoSeleccionado )

			else:
				self.alert("warning" , _("No has seleccionado ningun juego"))
		elif(id_tb == self.wb_tb_copiar_SD):

			if self.iteradorJuegoSeleccionado != None:		
				botones = (
						gtk.STOCK_CANCEL,
					   	gtk.RESPONSE_CANCEL,
					   	gtk.STOCK_OPEN,
					   	gtk.RESPONSE_OK,
					   )
		
				fc_copiar_SD = gtk.FileChooserDialog(_('Elige un directorio para las caratulas'), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
				fc_copiar_SD.set_local_only(True)
				fc_copiar_SD.show()
				
				fc_copiar_discos_SD = gtk.FileChooserDialog(_('Elige un directorio para los discos'), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)
				fc_copiar_discos_SD.set_local_only(True)
				fc_copiar_discos_SD.show()
			
				if 	fc_copiar_SD.run() == gtk.RESPONSE_OK and
					fc_copiar_discos_SD.run() == gtk.RESPONSE_OK:
					
					self.core.setDestinoCopiarCaratula( fc_copiar_SD.get_filenames() )
					
					for IDGAME in self.listaJuegos:
						self.poolBash.nuevoTrabajoCopiarCaratula( IDGAME )
						self.poolBash.nuevoTrabajoCopiarDisco( IDGAME )
				
				fc_copiar_SD.destroy()
				fc_copiar_discos_SD.destroy()
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

				elif(id_tb == self.wb_tb_anadir_directorio):
					fc_anadir = gtk.FileChooserDialog(_("Elige un directorio"), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)

				fc_anadir.set_local_only(True)

				if fc_anadir.run() == gtk.RESPONSE_OK:				
					'''
					Tarea AÑADIR JUEGO
					'''
					self.wb_box_progreso.show()
					self.wb_progreso1.set_text(_("Espere ..."))
					self.poolTrabajo.nuevoTrabajoAnadir( fc_anadir.get_filenames() )

				fc_anadir.destroy()
			else:
				self.alert("warning" , _("No has seleccionado ninguna particion"))
		else:
			self.alert("info" , _("Sin implementar aún"))

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
			if cola.qsize() > 0:
				objMensaje = cola.get()

				tipo = objMensaje.getTipo()
				mensaje = objMensaje.getMensaje()
				
				print tipo + " - " + mensaje
				
				if( tipo == "INFO" ):
					gobject.idle_add(self.actualizarLabel , mensaje)
				elif( tipo == "WARNING" ):
					gobject.idle_add(self.actualizarLabel ,_( "CUIDADO: %s" % mensaje ))
				elif( tipo == "ERROR" ):
					gobject.idle_add(self.actualizarLabel , _( "ERROR: %s" % mensaje ))
				elif( tipo == "COMANDO" ):
					if(mensaje == "EMPIEZA"):
						gobject.idle_add(self.actualizarLabel , _("Empezando ...") )
						gobject.idle_add(self.actualizarFraccion , 0.0 )
					elif(mensaje == "PROGRESO_INICIA"):
						hiloCalcularProgreso = HiloCalcularProgreso( self.actualizarLabel , self.actualizarFraccion )
						hiloCalcularProgreso.setDaemon(True)
						hiloCalcularProgreso.start()
						gobject.idle_add( self.mostrarHBoxProgreso )
					elif(mensaje == "PROGRESO_FIN"):
						if self.hiloCalcularProgreso!= None and self.hiloCalcularProgreso.isAlive():
							hiloCalcularProgreso.interrumpir()
							hiloCalcularProgreso.join()
						gobject.idle_add( self.ocultarHBoxProgreso )
					elif(mensaje == "TERMINA_OK"):
						gobject.idle_add(self.actualizarFraccion , 1.0 )
						gobject.idle_add(self.refrescarJuegos)
					elif(mensaje == "TERMINA_ERROR"):
						gobject.idle_add(self.actualizarFraccion , 1.0 )
					else:
						raise AssertionError, _("Comando desconocido")
				cola.task_done()
			else:
				time.sleep(3)

	def actualizarLabel( self, etiqueta ):
		self.progreso.set_text( etiqueta )

	def actualizarFraccion( self , fraccion ):
		self.progreso.set_fraction( fraccion )
		
	def ocultarHBoxProgreso(self):
		self.gui.wb_box_progreso.hide()
		
	def mostrarHBoxProgreso(self):
		self.gui.wb_box_progreso.show()
		
	# el callback de AÑADIR un juego es refrescar
	# FIXME: quitar gui como parametro, pasar mejor un callback para cada vez que acaba un trabajo
	def refrescarJuegos(self):
		self.gui.refrescarListaJuegos()

	def interrumpir(self):
		self.interrumpido = True

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

	def interrumpir(self):
		self.interrumpido = True

