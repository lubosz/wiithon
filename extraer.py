#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import config
import util
from gtk import FileFilter
from trabajo import TrabajoDesc

class ActionExtraer:
    
    def __init__(self, padre):
        self.padre = padre
        
        self.todos = False
        self.salida = self.padre.core.prefs.ruta_extraer_iso
        self.formato_destino = 'iso'
        
        self.padre.wb_extraer_radio_uno.connect('toggled',self.cambio_juegos_seleccionados, False)
        self.padre.wb_extraer_radio_todos.connect('toggled',self.cambio_juegos_seleccionados, True)
        
        self.padre.wb_extraer_directorio_salida.connect("current-folder-changed", self.cambio_directorio_salida)
        
        self.padre.wb_extraer_radio_formato_iso.connect('toggled',self.cambio_formato_salida, 'iso')
        self.padre.wb_extraer_radio_formato_wbfs.connect('toggled',self.cambio_formato_salida, 'wbfs')
        self.padre.wb_extraer_radio_formato_wdf.connect('toggled',self.cambio_formato_salida, 'wdf')
        
        self.padre.wb_boton_extraer_empezar.connect("clicked", self.empieza_conversion)
        
        self.padre.wb_extraer_directorio_salida.set_current_folder( self.salida )
    
    def cambio_juegos_seleccionados(self, radio, todos):
        if radio.get_active():
            self.todos = todos

    def cambio_directorio_salida(self, boton):
        self.padre.core.prefs.ruta_extraer_iso = self.salida = boton.get_file().get_path()

    def cambio_formato_salida(self, radio, formato):
        if radio.get_active():
            self.formato_destino = formato
            
    def extraer_juego(self, juego):

        extraer = False
        if self.padre.core.existeExtraido(juego , self.salida, self.formato_destino):
            extraer = self.padre.question(_('Desea reemplazar la iso del juego %s?') % (juego))
        else:
            if self.formato_destino == 'iso':
                if not util.space_for_dvd_iso_wii(self.salida):
                    self.padre.alert("warning" , _("Espacio libre insuficiente para extraer la ISO"))
                else:
                    extraer = True
            else:
                extraer = True

        if extraer:
            
            if config.DEBUG:
                print "Extraer en %s" % self.salida

            # extraer *juego* en la ruta seleccionada
            trabajoDesc = TrabajoDesc()
            trabajoDesc.formato_extraer = self.formato_destino
            self.padre.poolTrabajo.nuevoTrabajoExtraer(juego , self.salida, trabajoDesc)


    def empieza_conversion(self, boton):
        
        if not self.todos:

            if self.padre.isSelectedGame():
                self.extraer_juego( self.padre.sel_juego.obj )
            else:
                self.padre.alert("warning" , _("No has seleccionado ningun juego"))
        else:

            for juego in self.padre.lJuegos:
                self.extraer_juego(juego[0])

        self.padre.wb_dialogo_extraer.hide()
