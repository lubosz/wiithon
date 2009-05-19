#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import gtk , os , time , gobject , util

from glade_wrapper import GladeWrapper
import config , sys

from threading import Thread

from core import HiloPoolAnadir
from core import HiloDescargarTodasLasCaratulaYDiscos
from core import Mensaje

class WiithonGUI(GladeWrapper):

	######### PUNTEROS ##############
	
	# Referencia copia a la lista de juegos
	listaJuegos = None
	
	# Juego seleccionado
	iteradorJuegoSeleccionado = None
	
	# IDGAME Juego seleccionado
	IDGAMEJuegoSeleccionado = ""
	
	# Copia del DEVICE seleccionado
	DEVICE = ""
	
	########### HILOS ###############
	
	# Trabajador para Atender Mensajes
	hiloPoolAnadir = None
	
	# Para atender mensajes
	hiloAtenderMensajes = None
	
	# Hilo para descarga de caratulas
	hiloCaratulas = None

	def __init__(self, core):
		global _

		GladeWrapper.__init__(self, config.WIITHON_FILES + '/recursos/glade/wiithon.glade' , 'principal')
		self.core = core
		
		# permite usar hilos con PyGTK http://faq.pygtk.org/index.py?req=show&file=faq20.006.htp
		# modo seguro con hilos
		gobject.threads_init()

		self.wg_principal.set_title('Wiithon')
		self.wg_principal.show()
		
		botonbarra1 = self.wg_tb_anadir
		botonbarra2 = self.wg_tb_anadir_directorio
		botonbarra3 = self.wg_tb_borrar
		botonbarra4 = self.wg_tb_extraer
		botonbarra6 = self.wg_tb_preferencias
		botonbarra1.connect('clicked' , self.on_tb_toolbar_clicked)
		botonbarra2.connect('clicked' , self.on_tb_toolbar_clicked)
		botonbarra3.connect('clicked' , self.on_tb_toolbar_clicked)
		botonbarra4.connect('clicked' , self.on_tb_toolbar_clicked)
		botonbarra6.connect('clicked' , self.on_tb_toolbar_clicked)
		
		# de momento no hay preferencias
		botonbarra6.hide()

		# oculto la fila de la progreso		
		self.wg_box_progreso.hide()
		
		self.wg_principal.connect('destroy', self.salir)
		
		# carga la vista del TreeView de particiones
		self.tv_partitions_modelo = self.cargarParticionesVista()
					
		# carga la vista del TreeView de juegos
		self.tv_games_modelo = self.cargarJuegosVista()

		listaParticiones = self.core.getListaParticiones()
		if(len(listaParticiones) == 0):
			destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
			self.wg_img_caratula1.set_from_file( destinoCaratula )

			destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
			self.wg_img_disco1.set_from_file( destinoDisco )
		else:
			# carga el modelo de datos del TreeView de particiones
			self.cargarParticionesModelo(self.tv_partitions_modelo , listaParticiones)

			# selecciono la primera partición
			# indirectamente se carga:
			# lee el modelo de datos de la partición seleccionada
			# tambien refresca la lista de juegos del CORE
			self.seleccionarPrimeraFila( self.wg_tv_partitions , self.on_tv_partitions_cursor_changed)
	
			# descargar caratulas desde un hilo		
			if( len(self.listaJuegos) > 0 ):
				self.hiloCaratulas = HiloDescargarTodasLasCaratulaYDiscos(self.core , self.listaJuegos)
				self.hiloCaratulas.setDaemon(True)
				self.hiloCaratulas.start()
			
		# pongo el foco en los TreeView de juegos
		self.wg_tv_games.grab_focus()


	def cargarParticionesVista(self):
		tv_partitions = self.wg_tv_partitions

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
				modelo.set_value(iterador,1,particion.split(":")[0])
				modelo.set_value(iterador,2,particion.split(":")[1])
				i = i + 1

	def cargarJuegosVista(self):
		# Documentacion útil: http://blog.rastersoft.com/index.php/2007/01/27/trabajando-con-gtktreeview-en-python/
		tv_games = self.wg_tv_games

		render = gtk.CellRendererText()

		columna1 = gtk.TreeViewColumn(_('ID'), render , text=1)
		columna2 = gtk.TreeViewColumn(_('Nombre'), render , text=2)
		columna3 = gtk.TreeViewColumn(_('Tamaño'), render , text=3)
		columna4 = gtk.TreeViewColumn(_('Tipo de Juego'), render , text=4)
		columna5 = gtk.TreeViewColumn(_('Año'), render , text=5)

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
		if self.hiloCaratulas != None and self.hiloCaratulas.isAlive():
			self.hiloCaratulas.interrumpir()
		if self.hiloAtenderMensajes != None and self.hiloAtenderMensajes.isAlive():
			self.hiloAtenderMensajes.interrumpir()
		if self.hiloPoolAnadir != None and self.hiloPoolAnadir.isAlive():
			self.hiloPoolAnadir.interrumpir()
		gtk.main_quit()

	def alert(self, level, message):
		#alert_glade = gtk.glade.XML(config.WIITHON_FILES + '/recursos/glade/wiithon.glade', config.GLADE_ALERTA)
		alert_glade = gtk.Builder()
		alert_glade.add_from_file( config.WIITHON_FILES + '/recursos/glade/wiithon.glade' )
		alert_glade.get_object('principal').hide()

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
		self.DEVICE = self.core.getDeviceSeleccionado()
		self.listaJuegos = self.core.getListaJuegos( self.DEVICE )
		self.cargarJuegosModelo( self.tv_games_modelo , self.listaJuegos )
		self.seleccionarPrimeraFila( self.wg_tv_games , self.on_tv_games_cursor_changed)

	def seleccionarPrimeraFila(self , treeview , callback):
		# selecciono el primero y provoco el evento
		iter_primero = treeview.get_model().get_iter_first()
		if iter_primero != None:
			treeview.get_selection().select_iter( iter_primero )
		callback( treeview )
		
		
	# Click en particiones --> refresca la lista de juegos
	def on_tv_partitions_cursor_changed(self , treeview):
		seleccion,iterador = treeview.get_selection().get_selected()
		if iterador != None:
			self.core.setParticionSeleccionada( seleccion.get_value(iterador,0) )

			self.refrescarListaJuegos()

	def on_tv_games_cursor_changed(self , treeview):
		seleccion,self.iteradorJuegoSeleccionado = treeview.get_selection().get_selected()
		if self.iteradorJuegoSeleccionado != None:
			self.IDGAMEJuegoSeleccionado = seleccion.get_value(self.iteradorJuegoSeleccionado,1)

			destinoCaratula = os.path.join(config.HOME_WIITHON_CARATULAS , self.IDGAMEJuegoSeleccionado+".png")
			self.wg_img_caratula1.set_from_file( destinoCaratula )

			destinoDisco = os.path.join(config.HOME_WIITHON_DISCOS , self.IDGAMEJuegoSeleccionado+".png")
			self.wg_img_disco1.set_from_file( destinoDisco )
		else:
			destinoCaratula = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "caratula.png")
			self.wg_img_caratula1.set_from_file( destinoCaratula )

			destinoDisco = os.path.join(config.WIITHON_FILES_RECURSOS_IMAGENES , "disco.png")
			self.wg_img_disco1.set_from_file( destinoDisco )
			

	def on_tb_toolbar_clicked(self , id_tb):
		if(id_tb == self.wg_tb_borrar):
			if (self.question(_('¿Quieres borrar el juego con ID = "%s"?' % self.IDGAMEJuegoSeleccionado)) == 1):
				if self.iteradorJuegoSeleccionado != None:		
					# borrar del HD
					self.core.borrarJuego( self.core.getDeviceSeleccionado() , self.IDGAMEJuegoSeleccionado )
				
					# borrar de la tabla
					self.tv_games_modelo.remove( self.iteradorJuegoSeleccionado )
				
					# seleccionar el primero
					self.seleccionarPrimeraFila( self.wg_tv_games , self.on_tv_games_cursor_changed)
		elif(id_tb == self.wg_tb_extraer):
			seleccion,iterador = self.wg_tv_games.get_selection().get_selected()
			if iterador != None:
				DEVICE = self.core.getDeviceSeleccionado()
				IDGAME = seleccion.get_value(iterador,1)
				self.core.extraerJuego( DEVICE , IDGAME )
		else:
			botones = (gtk.STOCK_CANCEL,
				   gtk.RESPONSE_CANCEL,
				   gtk.STOCK_OPEN,
				   gtk.RESPONSE_OK,
				   )

			if(id_tb == self.wg_tb_anadir):
				fc_anadir = gtk.FileChooserDialog(_("Elige una ISO o un RAR"), None , gtk.FILE_CHOOSER_ACTION_OPEN , botones)

			elif(id_tb == self.wg_tb_anadir_directorio):
				fc_anadir = gtk.FileChooserDialog(_("Elige un directorio"), None , gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER , botones)

			fc_anadir.set_local_only(True)
			fc_anadir.set_select_multiple(True)
			fc_anadir.show()

			if fc_anadir.run() == gtk.RESPONSE_OK:
				
				self.hiloPoolAnadir = HiloPoolAnadir( self.core )
				self.hiloPoolAnadir.setDaemon(True)
				self.hiloPoolAnadir.anadir( fc_anadir.get_filenames() )
				self.hiloPoolAnadir.start()
				
				self.hiloAtenderMensajes = HiloAtenderMensajes( self.core , self.hiloPoolAnadir , self.wg_progreso1 , self )
				self.hiloAtenderMensajes.setDaemon(True)
				self.hiloAtenderMensajes.start()

			fc_anadir.destroy()
			
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
		print "init"

	def run(self):
		cola = self.core.getMensajes()
		while not self.interrumpido:
			sys.stdout.flush()
			objMensaje = cola.get(  )

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
					hiloCalcularProgreso.start()
					self.gui.wg_box_progreso.show()
				elif(mensaje == "PROGRESO_FIN"):
					# se ha podido "autodestruir"
					if self.hiloCalcularProgreso!= None and self.hiloCalcularProgreso.isAlive():
						hiloCalcularProgreso.interrumpir()
						hiloCalcularProgreso.join()
					self.gui.wg_box_progreso.hide()
				elif(mensaje == "TERMINA_OK"):
					gobject.idle_add(self.actualizarFraccion , 1.0 )
					self.gui.refrescarListaJuegos()
				elif(mensaje == "TERMINA_ERROR"):
					gobject.idle_add(self.actualizarFraccion , 1.0 )
				else:
					raise AssertionError, _("Comando desconocido")
			cola.task_done()
			
	def actualizarLabel( self, etiqueta ):
		self.progreso.set_text( etiqueta )
		
	def actualizarFraccion( self , fraccion ):
		self.progreso.set_fraction( fraccion )
		
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
			ultimaLinea = util.getSTDOUT("tail %s -n 1" % config.HOME_WIITHON_LOGS_PROCESO)
			try:
				cachos = ultimaLinea.split(";")

				if cachos[0] == "FIN":
					porcentaje = 100
					informativo = _("Finalizando. Hecho en")
					self.interrumpir()
				else:				
					porcentaje = self.porcentaje = float(cachos[0])		
					informativo = _("quedan")
					
				#sys.stdout
					
				hora = int(cachos[1])
				minutos = int(cachos[2])
				segundos = int(cachos[3])

				if(hora > 0):
					gobject.idle_add(self.actualizarLabel , "%d%% - %s %dh%dm%ds" % ( porcentaje , informativo , hora , minutos , segundos ))
				elif(minutos > 0):
					gobject.idle_add(self.actualizarLabel , "%d%% - %s %dm%ds" % ( porcentaje , informativo , minutos , segundos ))
				else:
					gobject.idle_add(self.actualizarLabel , "%d%% - %s %ds" % ( porcentaje, informativo , segundos ))

				porcentual = porcentaje / 100
				gobject.idle_add(self.actualizarFraccion , porcentual )
			except ValueError:
				pass
			
	def interrumpir(self):
		self.interrumpido = True

