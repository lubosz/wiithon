'''
    *  The nautilus-column-provider interface allows you to add columns to list views and add details to icon views.
    * The nautilus-menu-provider interface enables you to add context menu entries for files.
    * The nautilus-property-page-provider interface allows you to add property pages to property dialogs.
    * The nautilus-location-widget-provider interface allows you to add extra location widgets for a particular location.
    * The nautilus-info-provider interface provides extra information about files.

    http://www.linux.com/archive/feature/114134?page=3
'''
import os

import gtk
import nautilus

class OpenTerminalExtension(nautilus.MenuProvider):
    def __init__(self):
        pass
        
    def _open_terminal(self, file):
        os.system("gksudo 'gnome-open %s'" % file.get_uri())
	    
        
    def menu_activate_cb(self, menu, file):
        self._open_terminal(file)
        
       
    def get_file_items(self, window, files):
        if len(files) != 1:
            return
        
        file = files[0]
        if file.is_directory() or file.get_uri_scheme() != 'file':
            return
        
        item = nautilus.MenuItem('NautilusPython::openterminal_file_item',
                                 'Open As Root' ,
                                 'Open File %s As Root' % file.get_name())
        item.connect('activate', self.menu_activate_cb, file)
        return item,
