#!/usr/bin/env python
#-*-coding: utf-8-*-

import sys

import gtk
import gui

global wt_gui

def cb(widget, *args):
    global wt_gui
    wt_gui.alert('info', 'Hola')

wt_gui = gui.WiithonGUI()
wt_gui.wg_button2.connect('clicked', cb)

gtk.main()

print 'salir'
