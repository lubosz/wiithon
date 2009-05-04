#-*-coding: utf-8-*-

import gtk
from glade_wrapper import GladeWrapper

RUTA = "/usr/local/share/wiithon"

class WiithonGUI(GladeWrapper):
    def __init__(self):
        def cb(treeview, path, view_column):
            self.wg_img_caratula.set_from_file(RUTA+'/'+'recursos/imagenes/re4.png')


        GladeWrapper.__init__(self, RUTA+'/'+'recursos/glade/gui.glade')

        ls = gtk.ListStore(str,str,str,str,str)
        ls.append(('Rock Band 2','asdas','asdas','asdas','asdas',))
        ls.append(('Animal Crossing','asdas','asdas','asdas','asdas', ))
        ls.append(('Resident EVIL 4','asdas','asdas','asdas','asdas', ))

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


        self.wg_main_window.connect('destroy', gtk.main_quit)


    def alert(self, level, message):
        level_icons = {
            'info':    gtk.STOCK_DIALOG_INFO,
            'warning': gtk.STOCK_DIALOG_WARNING,
            'error':   gtk.STOCK_DIALOG_ERROR,
            }

        al = self.wg_alertdialog
        self.wg_alert_message.set_text(message)

        try:
            self.wg_alert_image.set_from_stock(level_icons[level])

        except IndexError:
            self.wg_alert_image.set_from_stock(level_icons['info'])

        self.wg_alertdialog.show()
