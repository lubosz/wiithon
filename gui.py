#-*-coding: utf-8-*-

import gtk , os , time , gobject

from glade_wrapper import GladeWrapper
import config

class WiithonGUI(GladeWrapper):

	def __init__(self, core):

		def on_tb_anadir_clicked(id_tb):
			def anadir(progreso):
				nuevo_valor = progreso.get_fraction() + 0.01
				if nuevo_valor > 1.0:
					nuevo_valor = 0.0
				progreso.set_fraction( nuevo_valor )
				return True


			botones = (gtk.STOCK_CANCEL,
				   gtk.RESPONSE_CANCEL,
				   gtk.STOCK_OPEN,
				   gtk.RESPONSE_OK,
				   )

			if(id_tb == self.wg_tb_anadir):
				fc_anadir = gtk.FileChooserDialog("Elige una ISO o un RAR", None , gtk.FILE_CHOOSER_ACTION_OPEN , botones)

			elif(id_tb == self.wg_tb_anadir_directorio):
				fc_anadir = gtk.FileChooserDialog("Elige un directorio", None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)

			fc_anadir.set_local_only(True)
			fc_anadir.set_select_multiple(True)
			fc_anadir.show()

			if fc_anadir.run() == gtk.RESPONSE_OK:
				self.core.encolar( fc_anadir.get_filenames() )

				self.timer = gobject.timeout_add (100, anadir , self.wg_progreso1)

			fc_anadir.destroy()

			#self.core.procesar( self.wg_progreso1 )

		GladeWrapper.__init__(self, config.WIITHON_FILES + '/recursos/glade/gui.glade' , 'principal')
		self.core = core
		self.core.subscribe(config.topics, self.alert)

		self.wg_principal.set_title('Wiithon')

		# Lo necesita el GUI para cargar la lista de particiones
		self.core.refrescarParticionWBFS()

		botonbarra1 = self.wg_tb_anadir
		botonbarra1.connect('clicked' , on_tb_anadir_clicked)

		botonbarra2 = self.wg_tb_anadir_directorio
		botonbarra2.connect('clicked' , on_tb_anadir_clicked)

		self.tv_games_modelo = self.cargarJuegosVista()

		self.tv_partitions_modelo = self.cargarParticionesVista()
		self.cargarParticionesModelo(self.tv_partitions_modelo , core.getListaParticiones())

		# selecciono el primero y provoco el evento
		iter_primero = self.wg_tv_partitions.get_model().get_iter_first()
		if iter_primero != None:
			self.wg_tv_partitions.get_selection().select_iter( iter_primero )
			self.on_tv_partitions_cursor_changed( self.wg_tv_partitions )

		# selecciono el primero y provoco el evento
		iter_primero = self.wg_tv_games.get_model().get_iter_first()
		if iter_primero != None:
			self.wg_tv_games.get_selection().select_iter( iter_primero )
			self.on_tv_games_cursor_changed( self.wg_tv_games )

		# pongo el foco en los TreeView de juegos
		self.wg_tv_games.grab_focus()

		self.wg_principal.connect('destroy', self.salir)

	def cargarParticionesVista(self):
		tv_partitions = self.wg_tv_partitions

		render = gtk.CellRendererText()

		columna1 = gtk.TreeViewColumn('Dispositivo', render , text=1)
		columna2 = gtk.TreeViewColumn('Fabricante', render , text=2)

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
				modelo.set_value(iterador,1,particion.split(":")[0])
				modelo.set_value(iterador,2,particion.split(":")[1])
				i = i + 1

	def cargarJuegosVista(self):
		# Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
		tv_games = self.wg_tv_games

		render = gtk.CellRendererText()

		columna1 = gtk.TreeViewColumn('ID', render , text=1)
		columna2 = gtk.TreeViewColumn('Nombre', render , text=2)
		columna3 = gtk.TreeViewColumn('Tamaño', render , text=3)
		columna4 = gtk.TreeViewColumn('Tipo de Juego', render , text=4)
		columna5 = gtk.TreeViewColumn('Año', render , text=5)

		tv_games.append_column(columna1)
		tv_games.append_column(columna2)
		tv_games.append_column(columna3)
		tv_games.append_column(columna4)
		tv_games.append_column(columna5)

		tv_games.connect('cursor-changed', self.on_tv_games_cursor_changed)

		modelo = gtk.ListStore (gobject.TYPE_INT , gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)
		tv_games.set_model(modelo)

		return modelo

	def cargarJuegosModelo(self , modelo , listaJuegos):
		if listaJuegos:
			modelo.clear()
			i = 0
			for juego in listaJuegos:
				iterador = modelo.insert(i)
				modelo.set_value(iterador,0, i )
				modelo.set_value(iterador,1, juego[0])
				modelo.set_value(iterador,2, juego[1])
				modelo.set_value(iterador,3, "%.2f GB" % float(juego[2]))
				modelo.set_value(iterador,4, "??")
				modelo.set_value(iterador,5, "??")
				i = i + 1

	def salir(self , widget, data=None):
		try:
			gobject.source_remove(self.timer)
			self.timer = 0
		except:
			pass
		gtk.main_quit()

	def alert(self, level, message):
		alert_glade = gtk.glade.XML(config.WIITHON_FILES + '/recursos/glade/gui.glade', 'alert_dialog')

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
		alert_msg = alert_glade.get_widget('lbl_message')
		alert_msg.set_text(message)

		# configure the icon to display
		img = alert_glade.get_widget('img_alert')

		try:
			img.set_from_stock(level_icons[level], gtk.ICON_SIZE_DIALOG)
		except IndexError:
			img.set_from_stock(level_icons['info'], gtk.ICON_SIZE_DIALOG)

		# configure the buttons
		btn_ok = alert_glade.get_widget('btn_ok')
		btn_no = alert_glade.get_widget('btn_no')

		if level_buttons[level][0]:
			btn_ok.set_label(level_buttons[level][0])
		else:
			btn_ok.set_visible(False)

		if level_buttons[level][1]:
			btn_no.set_label(level_buttons[level][1])
		else:
			btn_no.hide()

		alert_glade.get_widget('alert_dialog').set_title(level)
		res = alert_glade.get_widget('alert_dialog').run()
		alert_glade.get_widget('alert_dialog').hide()

		return res

	def question(self, pregunta):
		return self.alert('question', pregunta)

	def on_tv_partitions_cursor_changed(self , treeview):
		seleccion,iterador = treeview.get_selection().get_selected()
		if iterador != None:
			self.core.setParticionSeleccionada( seleccion.get_value(iterador,0) )

			# recargar la lista de juegos
			DEVICE = self.core.getDeviceSeleccionado()
			listaJuegos = self.core.getListaJuegos( DEVICE )
			self.cargarJuegosModelo( self.tv_games_modelo , listaJuegos )

			self.core.descargarTodasLasCaratulaYDiscos( DEVICE , listaJuegos )

	def on_tv_games_cursor_changed(self , treeview):
		seleccion,iterador = treeview.get_selection().get_selected()
		if iterador != None:
			IDGAME = seleccion.get_value(iterador,1)

			destinoCaratula = os.path.join(config.HOME_WIITHON_CARATULAS , IDGAME+".png")
			self.wg_img_caratula.set_from_file( destinoCaratula )

			destinoDisco = os.path.join(config.HOME_WIITHON_DISCOS , IDGAME+".png")
			self.wg_img_disco.set_from_file( destinoDisco )

