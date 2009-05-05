#!/usr/bin/env python
#-*-coding: utf-8-*-

import gtk
import gui

def cb(widget, *args):
    global wt_gui
    print 'exit'
    #wt_gui.alert_off()


wt_gui = gui.WiithonGUI()
res = wt_gui.alert('question', 'hola')

if res == 1:
    print 'Botón de la derecha'

elif res == 0:
    print 'Botón de la izquierda'

else:
    print 'another'
    print res



gtk.main()


