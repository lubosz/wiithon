#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import config
import util
import gtk

botones = (
        gtk.STOCK_CANCEL,
        gtk.RESPONSE_CANCEL,
        gtk.STOCK_OPEN,
        gtk.RESPONSE_OK,
        )

class SelectorFicheros(gtk.FileChooserDialog):
            
    def __init__(self, titulo, tipo = gtk.FILE_CHOOSER_ACTION_OPEN ):
        gtk.FileChooserDialog.__init__(self, titulo, None , tipo , botones)
        # Add location popup info
        self.set_extra_widget(gtk.Label(titulo))
        self.set_default_response(gtk.RESPONSE_OK)
        self.set_local_only(True)
        
    def addFavorite(self, ruta):
        try:
            self.add_shortcut_folder( ruta )
        except:
            pass

    def crearFiltrosISOyRAR(self):
        filter = gtk.FileFilter()
        filter.set_name(_('Imagen Wii (ISO o RAR)'))
        filter.add_pattern('*.iso')
        filter.add_pattern('*.rar')
        self.add_filter(filter)
