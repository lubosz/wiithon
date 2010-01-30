#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import config
import util
from gtk import FileFilter

class Action:
    pass
    
class ActionConversor(Action):
    
    def __init__(self, padre):
        self.padre = padre
        
        self.origen = ''
        self.salida = ''
        self.formato_origen = ''
        self.formato_destino = ''
        self.padre.wb_conversor_fichero_origen.connect("selection-changed", self.cambio_archivo_origen)
        self.padre.wb_conversor_directorio_salida.connect("current-folder-changed", self.cambio_directorio_salida)
        self.padre.wb_boton_conversor_empezar.connect("clicked", self.empieza_conversion)
        
        self.padre.wb_conversor_radio_formato_iso.connect('toggled',self.cambio_formato_salida, 'iso')
        self.padre.wb_conversor_radio_formato_wbfs.connect('toggled',self.cambio_formato_salida, 'wbfs')
        self.padre.wb_conversor_radio_formato_wdf.connect('toggled',self.cambio_formato_salida, 'wdf')
        
        filter = FileFilter()
        filter.set_name(_('ISO / WBFS / WDF'))
        filter.add_pattern('*.iso')
        filter.add_pattern('*.wbfs')
        filter.add_pattern('*.wdf')
        self.padre.wb_conversor_fichero_origen.add_filter(filter)
        
        self.ocultar_resto_formulario()
    
    # gtk.FileChooserButton
    def cambio_archivo_origen(self, boton):
        if boton.get_file() != None:

            self.origen = boton.get_file().get_path()
            self.formato_origen = self.padre.core.getAutodetectarFormato(self.origen)
            #self.padre.alert('info',self.formato_origen)
            esISO = self.formato_origen == 'iso'
            self.mostrar_resto_formulario(esISO)
            
            self.cambio_directorio_salida(self.padre.wb_conversor_directorio_salida)
        else:
            self.origen = ''

    # gtk.FileChooserButton
    def cambio_directorio_salida(self, boton):
        self.salida = boton.get_file().get_path()

    def cambio_formato_salida(self, radio, formato):
        if radio.get_active():
            self.formato_destino = formato

    def empieza_conversion(self, boton):
        if self.formato_destino == 'iso':
            if self.formato_origen == 'wbfs':
                self.padre.poolTrabajo.nuevoTrabajoConvertir_WBFS_ISO(self.origen, self.salida)
            elif self.formato_origen == 'wdf':
                self.padre.poolTrabajo.nuevoTrabajoConvertir_WDF_ISO(self.origen, self.salida)
        elif self.formato_destino == 'wbfs':
            if self.formato_origen == 'iso':
                self.padre.poolTrabajo.nuevoTrabajoConvertir_ISO_WBFS(self.origen, self.salida)
        elif self.formato_destino == 'wdf':
            if self.formato_origen == 'iso':
                self.padre.poolTrabajo.nuevoTrabajoConvertir_ISO_WDF(self.origen, self.salida)
            
        self.ocultar_resto_formulario()

    def mostrar_resto_formulario(self, esISO):

        self.padre.wb_frame_paso1.set_sensitive(True)
        self.padre.wb_frame_paso2.set_sensitive(True)
        self.padre.wb_frame_paso3.set_sensitive(True)
        
        if esISO:
            self.padre.wb_conversor_radio_formato_iso.set_active(False)
            self.padre.wb_conversor_radio_formato_wbfs.set_active(True)
            self.padre.wb_conversor_radio_formato_wdf.set_active(False)

            self.padre.wb_conversor_radio_formato_iso.set_sensitive(False)
            self.padre.wb_conversor_radio_formato_wbfs.set_sensitive(True)
            self.padre.wb_conversor_radio_formato_wdf.set_sensitive(True)
        else:
            self.padre.wb_conversor_radio_formato_iso.set_active(True)
            self.padre.wb_conversor_radio_formato_wbfs.set_active(False)
            self.padre.wb_conversor_radio_formato_wdf.set_active(False)
            
            self.padre.wb_conversor_radio_formato_iso.set_sensitive(True)
            self.padre.wb_conversor_radio_formato_wbfs.set_sensitive(False)
            self.padre.wb_conversor_radio_formato_wdf.set_sensitive(False)

        self.padre.wb_boton_conversor_empezar.set_sensitive(True)

    def ocultar_resto_formulario(self):
        self.padre.wb_conversor_fichero_origen.unselect_all()

        self.padre.wb_frame_paso1.set_sensitive(True)
        self.padre.wb_frame_paso2.set_sensitive(False)
        self.padre.wb_frame_paso3.set_sensitive(False)
        self.padre.wb_boton_conversor_empezar.set_sensitive(False)
