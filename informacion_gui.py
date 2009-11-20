#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import gtk

class InformacionGuiDatos(object):

    def __init__(self):
        self.arriba_usado = 0.0
        self.arriba_total = 0.0
        self.arriba_num_juegos = 0
        self.arriba_num_juegos_rel = 0.0
        self.arriba_num_tareas = 0
        
        self.abajo_num_particiones = 0
        self.abajo_num_juegos_wiitdb = 0
        self.abajo_juegos_sin_caratula = 0
        self.abajo_juegos_sin_discart = 0
        
    def __setattr__(self, name, value):
       
        # aplicamos el nuevo atributo
        object.__setattr__(self, name, value)
        
        # puede que se ejecute desde un hilo
        gtk.gdk.threads_enter()
        
        # representamos el nuevo dato en el gui
        self.representarDato(name, value)
        
        # termina de ejecutarse desde un hilo
        gtk.gdk.threads_leave()
        
    def representarDato(self, name, value):
        # Metodo abstracto, debes sobreescribirlo.
        raise AssertionError

class InformacionGuiPresentacion(InformacionGuiDatos):

    def __init__(self, wb_labelEspacio, wb_progresoEspacio, 
                wb_label_numParticionesWBFS, wb_label_juegosConInfoWiiTDB,
                wb_label_juegosSinCaratula, wb_label_juegosSinDiscArt,
                wb_estadoTrabajo):

        self.wb_labelEspacio = wb_labelEspacio
        self.wb_progresoEspacio = wb_progresoEspacio
        self.wb_label_numParticionesWBFS = wb_label_numParticionesWBFS
        self.wb_label_juegosConInfoWiiTDB = wb_label_juegosConInfoWiiTDB
        self.wb_label_juegosSinCaratula = wb_label_juegosSinCaratula
        self.wb_label_juegosSinDiscArt = wb_label_juegosSinDiscArt
        self.wb_estadoTrabajo = wb_estadoTrabajo

    # FIXME: hay ejecuciones desde hilo que puede que requieran idle_add para ser Thread-secure
    def representarDato(self, name, value):

        if name == 'arriba_total':
            self.wb_labelEspacio.set_text("%.2f GB / %.2f GB" % (self.arriba_usado , self.arriba_total))
            try:
                self.arriba_num_juegos_rel = (self.arriba_usado * 100.0 / self.arriba_total) / 100.0
            except ZeroDivisionError:
                self.arriba_num_juegos_rel = 0.0
            self.wb_progresoEspacio.set_fraction( self.arriba_num_juegos_rel )
            
        elif name == 'arriba_num_juegos':
            self.wb_progresoEspacio.set_text(_("%d juegos") % (self.arriba_num_juegos))
            
        elif name == 'abajo_num_particiones':
            if value == 0:
                self.wb_label_numParticionesWBFS.set_label(_("No hay particiones WBFS"))
            elif value == 1:
                self.wb_label_numParticionesWBFS.set_label(_("1 particion WBFS"))
            else:
                self.wb_label_numParticionesWBFS.set_label(_("%d particiones WBFS") % (self.abajo_num_particiones))

        elif name == 'abajo_num_juegos_wiitdb':    
            self.wb_label_juegosConInfoWiiTDB.set_text(_("Hay %d juegos con informacion WiiTDB") % self.abajo_num_juegos_wiitdb)

        elif name == 'abajo_juegos_sin_caratula':
            if value == 0:
                self.wb_label_juegosSinCaratula.set_text(_("No faltan caratulas"))
            elif value == 1:
                self.wb_label_juegosSinCaratula.set_text(_("1 juego sin caratula"))
            else:
                self.wb_label_juegosSinCaratula.set_text(_("%d juegos sin caratula") % self.abajo_juegos_sin_caratula)

        elif name == 'abajo_juegos_sin_discart':
            if value == 0:
                self.wb_label_juegosSinDiscArt.set_text(_("No faltan disc-art"))
            elif value == 1:
                self.wb_label_juegosSinDiscArt.set_text(_("1 juego sin disc-art"))
            else:
                self.wb_label_juegosSinDiscArt.set_text(_("%d juegos sin disc-art") % self.abajo_juegos_sin_discart)
                
        elif name == 'arriba_num_tareas':
            if value <= 1:
                self.wb_estadoTrabajo.hide()
            else:
                etiqueta = _("Hay %d tareas") % (self.arriba_num_tareas)
                self.wb_estadoTrabajo.set_label(etiqueta)
                self.wb_estadoTrabajo.show()
