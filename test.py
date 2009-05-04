#!/usr/bin/env python
#-*-coding: utf-8-*-

import sys

import gtk
import gui

global wt_gui

def cb(widget, *args):
    global wt_gui
    print 'exit'
    #wt_gui.alert_off()


wt_gui = gui.WiithonGUI()
res = wt_gui.alert('question', 'hola')

if res == gtk.RESPONSE_APPLY:
    print 'gtk.RESPONSE_APPY'

elif res == gtk.RESPONSE_YES:
    print 'gtk.RESPONSE_YES'

elif res == gtk.RESPONSE_NO:
    print 'gtk.RESPONSE_NO'

elif res == gtk.RESPONSE_NONE:
    print 'gtk.RESPONSE_NONE'

else:
    print 'another'
    print res


gtk.main()


