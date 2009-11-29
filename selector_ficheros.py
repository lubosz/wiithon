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
        filter.set_name(_('Todos los formatos'))
        filter.add_pattern('*.iso')
        filter.add_pattern('*.rar')
        filter.add_pattern('*.wbfs')
        filter.add_pattern('*.wdf')
        self.add_filter(filter)

        filter2 = gtk.FileFilter()
        filter2.set_name(_('Imagen Wii en formato ISO'))
        filter2.add_pattern('*.iso')
        self.add_filter(filter2)
        
        filter3 = gtk.FileFilter()
        filter3.set_name(_('Imagen Wii comprimida en RAR'))
        filter3.add_pattern('*.rar')
        self.add_filter(filter3)
        
        filter4 = gtk.FileFilter()
        filter4.set_name(_('Imagen Wii en formato WBFS para FAT32'))
        filter4.add_pattern('*.wbfs')
        self.add_filter(filter4)
        
        filter5 = gtk.FileFilter()
        filter5.set_name(_('Imagen Wii en formato WDF'))
        filter5.add_pattern('*.wdf')
        self.add_filter(filter5)
