#-*-coding: utf-8-*-

import gtk , os
from glade_wrapper import GladeWrapper

class WiithonGUI(GladeWrapper):

	core = None
	
	RUTA = "/usr/local/share/wiithon"
	HOME = os.path.expanduser("~")

	def __init__(self):
		def cb(treeview, path, view_column):
			self.wg_img_caratula.set_from_file(self.RUTA+'/recursos/imagenes/re4.png')

		def on_tb_anadir_clicked(id_tb):
			botones = (	gtk.STOCK_CANCEL,
					gtk.RESPONSE_CANCEL,
					gtk.STOCK_OPEN,
					gtk.RESPONSE_OK )
			if(id_tb == self.wg_tb_anadir):
				fc_anadir = gtk.FileChooserDialog("Elige una ISO o un RAR", None , gtk.FILE_CHOOSER_ACTION_OPEN , botones)
			elif(id_tb == self.wg_tb_anadir_directorio):
				fc_anadir = gtk.FileChooserDialog("Elige un directorio", None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)

			fc_anadir.set_local_only(True)
			fc_anadir.set_select_multiple(True)
			fc_anadir.show()
							
			if fc_anadir.run() == gtk.RESPONSE_OK:
				self.core.anadirListaFicheros( fc_anadir.get_filenames() )
			
			fc_anadir.destroy()
			self.core.procesar()

		GladeWrapper.__init__(self, self.RUTA+'/'+'recursos/glade/gui.glade' , 'principal')
		self.wg_principal.hide() # hack

		ls = gtk.ListStore(str,)
		ls.append(('Rock Band 2',))
		ls.append(('Animal Crossing',))
		ls.append(('Resident EVIL 4',))

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
		treeview.set_model(ls)
		treeview.connect('row-activated', cb)

		botonbarra1 = self.wg_tb_anadir
		botonbarra1.connect('clicked' , on_tb_anadir_clicked)
		
		botonbarra2 = self.wg_tb_anadir_directorio
		botonbarra2.connect('clicked' , on_tb_anadir_clicked)

		self.wg_principal.connect('destroy', gtk.main_quit)

	def alert(self, level, message):	
		alert_glade = gtk.glade.XML(self.RUTA + '/recursos/glade/gui.glade', 'alert_dialog')

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

		#def alert_off(self):
		#    alert_glade = gtk.glade.XML(self.RUTA + '/recursos/glade/gui.glade', 'alert_dialog')
		#    alert_glade.get_widget('alert_dialog').hide()

	def setCore(self , core):
		self.core = core


