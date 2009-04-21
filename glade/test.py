#!/usr/bin/env python
#-*-coding: utf-8-*-

import sys

import gtk
import gtk.glade

def cb(treeview, path, view_column):
    global xml
    xml.get_widget('image1').set_from_file('images/rock2.jpg')

xml = gtk.glade.XML('test1_gui.glade')

ls = gtk.ListStore(str)

ls.append(('Rock Band 2',))
ls.append(('Animal Crossing', ))

# create a CellRenderer to render the data
cell = gtk.CellRendererText()
# create the TreeViewColumns to display the data
tvcolumn = gtk.TreeViewColumn('Game', cell, text=0)

# add columns to treeview
treeview = xml.get_widget('treeview1')
treeview.append_column(tvcolumn)
treeview.set_model(ls)

treeview.connect('row-activated', cb)

xml.get_widget('main_window').connect('destroy', gtk.main_quit)
gtk.main()
