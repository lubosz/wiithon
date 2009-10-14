#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import gtk

import util
import config
from wiitdb_schema import Preferencia

db =        util.getBDD()
session =   util.getSesionBDD(db)

class EntryPreferencia(gtk.Entry):
    
    def __init__(self, name_pref):
        gtk.Entry.__init__(self)
        self.name_pref = name_pref

class Preferencias:

    def __init__(self):
        pass

    def cargarPreferenciasPorDefecto(self, prefs_vbox):
        self.iniciarPreferencia('device_seleccionado')
        self.iniciarPreferencia('idgame_seleccionado')
        self.iniciarPreferencia('ruta_anadir', defecto=os.getcwd())
        self.iniciarPreferencia('ruta_anadir_directorio', defecto=os.getcwd())
        self.iniciarPreferencia('ruta_extraer_iso', defecto=os.getcwd())
        self.iniciarPreferencia('ruta_copiar_caratulas', defecto=os.getcwd())
        self.iniciarPreferencia('ruta_copiar_discos', defecto=os.getcwd())
        self.iniciarPreferencia('URL_ZIP_WIITDB', defecto='http://wiitdb.com/wiitdb.zip', mostrar=True, vbox=prefs_vbox)
        self.iniciarPreferencia('FORMATO_FECHA_WIITDB', defecto='%d-%m-%Y', mostrar=True, vbox=prefs_vbox)
        self.iniciarPreferencia('WIDTH_COVERS', defecto=160, mostrar=True, vbox=prefs_vbox)
        self.iniciarPreferencia('HEIGHT_COVERS', defecto=224, mostrar=True, vbox=prefs_vbox)

    # indicar el vbox que inicia la preferencia
    def iniciarPreferencia(self, name, defecto = '', mostrar = False, vbox = None):
        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()
        if preferencia == None:
            preferencia = Preferencia(name, defecto)
            session.save( preferencia )
            session.commit()
        
        if config.DEBUG:
            print preferencia

        if mostrar:
            h1 = gtk.HBox(homogeneous=False, spacing=10)
            
            etiqueta = gtk.Label()
            etiqueta.set_text("<b>%s: </b>" % preferencia.campo)
            etiqueta.set_use_markup(True)
            h1.pack_start(etiqueta, expand=True, fill=True, padding=10)
            
            # renderizar preferencia
            entry = EntryPreferencia(name)
            entry.set_text(preferencia.valor)
            entry.set_max_length(255)
            entry.set_editable(True)
            entry.connect('changed' , self.entryModificado)
            h1.pack_start(entry, expand=True, fill=True, padding=10)

            vbox.pack_start(h1)
            vbox.show_all()
        
    def entryModificado(self, entry):
        self.__setattr__(entry.name_pref, entry.get_text())

    # escribir en la BDD
    # escribir en el texbox
    def __setattr__(self, name, value):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            if config.DEBUG:
                print "guardando %s" % value
            preferencia.valor = value
            session.commit()

    # leer del textbox
    # self.__getattribute__(self, "name")
    # http://pyref.infogami.com/__getattribute__
    def __getattr__(self, name):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            return preferencia.valor
        
        return None
