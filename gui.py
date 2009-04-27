#-*-coding: utf-8-*-

import gtk
from glade_wrapper import GladeWrapper

class WiithonGUI(GladeWrapper):
    def __init__(self):
        def cb(treeview, path, view_column):
            self.wg_caratula.set_from_file('glade/images/rock2.jpg')

        GladeWrapper.__init__(self, 'glade/me_gusta_tipo_rythimbox.glade')

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

        treeview = self.wg_TablaJuegos
        treeview.append_column(tvcolumn1)
        treeview.append_column(tvcolumn2)
        treeview.append_column(tvcolumn3)
        treeview.append_column(tvcolumn4)
        treeview.append_column(tvcolumn5)
        treeview.set_model(ls)
        treeview.connect('row-activated', cb)

        ls2 = gtk.ListStore(str)
        ls3 = gtk.ListStore(str)
        ls2.append(('Accion',))
        ls2.append(('Futbol',))
        ls3.append(('2009',))
        ls3.append(('2008',))
        cell2 = gtk.CellRendererText()
        cell3 = gtk.CellRendererText()
        col2 = gtk.TreeViewColumn('Tipo de Juego', cell2, text=0)
        col3 = gtk.TreeViewColumn('Año', cell3, text=0)
        treeview2 = self.wg_ListaTipoJuego
        treeview2.append_column(col2)
        treeview3 = self.wg_ListaAnio
        treeview3.append_column(col3)
        treeview2.set_model(ls2)
        treeview3.set_model(ls3)

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
