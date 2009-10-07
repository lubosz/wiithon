#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# El objeto permite abstraer con él un objeto de usuario en el atributo 'obj'
# Este objeto será "Juego" para el treeview de juegos
# O será "Particion" para los treeviews de lista de particiones
class FilaTreeview:
    def __init__(self):
        self.sel = None                                 # gtk.ListStore
        self.it = None                                  # gtk.TreeIter
        self.clave = None                               # campo clave
        self.obj = None                                 # custom class user
        
    def actualizar_columna(self, treeview):
        self.sel, self.it  = treeview.get_selection().get_selected()
        if self.esSeleccionado():
            self.clave = self.sel.get_value(self.it,0)
        else:
            self.clave = None
            
    def get_path(self, treeview):
        return treeview.get_model().get_path(self.it)
        
    def esSeleccionado(self):
        return self.it != None
