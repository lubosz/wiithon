#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import config
import util
from gtk import FileFilter

class ActionExtraer:
    
    def __init__(self, padre):
        self.padre = padre
        
        self.todos = False
        self.salida = config.HOME
        self.formato_destino = 'iso'
        
        self.padre.wb_extraer_radio_uno.connect('toggled',self.cambio_juegos_seleccionados, False)
        self.padre.wb_extraer_radio_todos.connect('toggled',self.cambio_juegos_seleccionados, True)

        self.padre.wb_extraer_directorio_salida.connect("current-folder-changed", self.cambio_directorio_salida)
        
        self.padre.wb_extraer_radio_formato_iso.connect('toggled',self.cambio_formato_salida, 'iso')
        self.padre.wb_extraer_radio_formato_wbfs.connect('toggled',self.cambio_formato_salida, 'wbfs')
        self.padre.wb_extraer_radio_formato_wdf.connect('toggled',self.cambio_formato_salida, 'wdf')
        
        self.padre.wb_boton_extraer_empezar.connect("clicked", self.empieza_conversion)
    
    def cambio_juegos_seleccionados(self, radio, todos):
        if radio.get_active():
            self.todos = todos

    def cambio_directorio_salida(self, boton):
        self.salida = boton.get_file().get_path()

    def cambio_formato_salida(self, radio, formato):
        if radio.get_active():
            self.formato_destino = formato

    def empieza_conversion(self, boton):
        if not self.todos:
            if self.padre.isSelectedGame():

                ruta_selec = self.salida
                self.padre.core.prefs.FORMATO_EXTRACT = self.formato_destino

                extraer = False
                if self.padre.core.existeExtraido(self.padre.sel_juego.obj , ruta_selec, self.padre.core.prefs.FORMATO_EXTRACT):
                    extraer = self.padre.question(_('Desea reemplazar la iso del juego %s?') % (self.padre.sel_juego.obj))
                else:
                    if self.padre.core.prefs.FORMATO_EXTRACT == 'iso':
                        if not util.space_for_dvd_iso_wii(ruta_selec):
                            self.padre.alert("warning" , _("Espacio libre insuficiente para extraer la ISO"))
                        else:
                            extraer = True
                    else:
                        extraer = True

                if extraer:
                    # nueva ruta favorita
                    self.padre.core.prefs.ruta_extraer_iso = ruta_selec
                    
                    print "Extraer en %s" % ruta_selec

                    # extraer *juego* en la ruta seleccionada
                    self.padre.poolTrabajo.nuevoTrabajoExtraer(self.padre.sel_juego.obj , ruta_selec)

            else:
                self.padre.alert("warning" , _("No has seleccionado ningun juego"))
        else:
            self.padre.alert("warning" , "Sin implementar")
            
        self.padre.wb_dialogo_extraer.hide()

