#-*-coding: utf-8-*-

import gtk
from glade_wrapper import GladeWrapper

RUTA = "/usr/local/share/wiithon"

class WiithonGUI(GladeWrapper):
    def __init__(self):
        def cb(treeview, path, view_column):
            self.wg_img_caratula.set_from_file(RUTA+'/recursos/imagenes/re4.png')


        GladeWrapper.__init__(self, RUTA+'/'+'recursos/glade/gui.glade')
                # FIXME
        self.wg_main_window.hide()

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
        alert_glade = gtk.glade.XML(RUTA + '/recursos/glade/gui.glade', 'alert_dialog')

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
    #    alert_glade = gtk.glade.XML(RUTA + '/recursos/glade/gui.glade', 'alert_dialog')
    #    alert_glade.get_widget('alert_dialog').hide()



