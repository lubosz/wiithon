#-*-coding: utf-8-*-

import gtk , os , time , gobject

from glade_wrapper import GladeWrapper
import config

class WiithonGUI(GladeWrapper):

	# No hace falta en python, cuando haces self.core = core ya se crea
	#core = None

	def __init__(self):
		def cb(treeview, path, view_column):
			self.wg_img_caratula.set_from_file(config.WIITHON_FILES+'/recursos/imagenes/re4.png')

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
				self.core.anadirListaFicheros( fc_anadir.get_filenames() )

				self.timer = gobject.timeout_add (100, anadir , self.wg_progreso1)

			fc_anadir.destroy()

			#self.core.procesar( self.wg_progreso1 )

		GladeWrapper.__init__(self, config.WIITHON_FILES + '/recursos/glade/gui.glade' , 'principal')

		self.wg_principal.set_title('Wiithon')

		self.model = gtk.ListStore(str,)

		cell = gtk.CellRendererText()
		tvcolumn1 = gtk.TreeViewColumn('ID', cell, text=0)
		tvcolumn2 = gtk.TreeViewColumn('Juego', cell, text=0)
		tvcolumn3 = gtk.TreeViewColumn('Tamaño', cell, text=0)
		tvcolumn4 = gtk.TreeViewColumn('Tipo de juego', cell, text=0)
		tvcolumn5 = gtk.TreeViewColumn('Año', cell, text=0)

		treeview = self.wg_tv_games
		treeview.append_column(tvcolumn1)
		treeview.append_column(tvcolumn2)
		treeview.append_column(tvcolumn3)
		treeview.append_column(tvcolumn4)
		treeview.append_column(tvcolumn5)
		treeview.set_model(self.model)

		treeview.connect('row-activated', cb)

		botonbarra1 = self.wg_tb_anadir
		botonbarra1.connect('clicked' , on_tb_anadir_clicked)

		botonbarra2 = self.wg_tb_anadir_directorio
		botonbarra2.connect('clicked' , on_tb_anadir_clicked)

		self.wg_principal.connect('destroy', self.salir)

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


	def setCore(self , core):
		self.core = core

		topics = ['error', 'warning', 'info']
		self.core.subscribe(topics, self.alert)

