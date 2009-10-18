#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import gtk

import util
import config
from wiitdb_schema import Preferencia

db =        util.getBDD()
session =   util.getSesionBDD(db)

class EntryRelacionado(gtk.Entry):
    
    def __init__(self, name_pref, defecto):
        gtk.Entry.__init__(self)
        self.name_pref = str(name_pref)
        self.defecto = str(defecto)

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
        self.iniciarPreferencia('URL_ZIP_WIITDB', defecto='http://wiitdb.com/wiitdb.zip', mostrar=True, vbox=prefs_vbox, label=_('URL Base de datos WiiTDB'))
        self.iniciarPreferencia('FORMATO_FECHA_WIITDB', defecto='%d/%m/%Y', mostrar=True, vbox=prefs_vbox, label=_('Formato fecha'))
        self.iniciarPreferencia('FORMATO_FECHA_CORTA_WIITDB', defecto='%Y/%m', mostrar=True, vbox=prefs_vbox, label=_('Formato fecha corto'))
        self.iniciarPreferencia('WIDTH_COVERS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Ancho imagen caratula'))
        self.iniciarPreferencia('HEIGHT_COVERS', defecto=224, mostrar=True, vbox=prefs_vbox, label=_('Altura imagen caratula'))
        self.iniciarPreferencia('WIDTH_DISCS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Ancho imagen disc-art'))
        self.iniciarPreferencia('HEIGHT_DISCS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Altura imagen disc-art'))
        self.iniciarPreferencia('NUM_HILOS', defecto=15, mostrar=True, vbox=prefs_vbox, label=_('Num. Hilos para tareas de fondo'))
        self.iniciarPreferencia('LANG_PRINCIPAL', defecto='ES', mostrar=True, vbox=prefs_vbox, label=_('Idioma principal para el synopsis'))
        self.iniciarPreferencia('LANG_SECUNDARIO', defecto='EN', mostrar=True, vbox=prefs_vbox, label=_('Idioma auxiliar para el synopsis'))
        
        PROVIDER_COVERS = []
        a = PROVIDER_COVERS.append
        a("http://wiitdb.com/wiitdb/artwork/cover/ES/%s.png")
        a("http://wiitdb.com/wiitdb/artwork/cover/EN/%s.png")
        a("http://wiitdb.com/wiitdb/artwork/cover3D/ES/%s.png")
        a("http://wiitdb.com/wiitdb/artwork/cover3D/EN/%s.png")
        a("http://wiitdb.com/wiitdb/artwork/coverfull/FR/%s.png")
        a("http://www.wiiboxart.com/pal/%s.png")
        a("http://www.wiiboxart.com/ntsc/%s.png")
        a("http://www.wiiboxart.com/ntscj/%s.png")
        a("http://www.wiiboxart.com/3d/160/225/%s.png")
        a("http://www.wiiboxart.com/widescreen/pal/%s.png")
        a("http://www.wiiboxart.com/widescreen/ntsc/%s.png")
        a("http://www.wiiboxart.com/widescreen/ntscj/%s.png")
        a("http://www.wiiboxart.com/fullcover/%s.png")
        self.iniciarPreferencia('PROVIDER_COVERS', defecto=PROVIDER_COVERS, mostrar=True, vbox=prefs_vbox, label=_('Proveedor de caratulas'), multiple=True)

    # indicar el vbox que inicia la preferencia
    def iniciarPreferencia(self, name, defecto = '', mostrar = False, vbox = None, label = '', multiple=False):
        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()
        if preferencia == None:
            preferencia = Preferencia(name, defecto)
            session.save(preferencia)
            session.commit()
        
        if config.DEBUG:
            print preferencia

        if mostrar:
            h1 = gtk.HBox(homogeneous=False, spacing=0)
            
            etiqueta = gtk.Label()
            etiqueta.set_text("<b>%s: </b>" % label)
            etiqueta.set_use_markup(True)
            etiqueta.set_justify(gtk.JUSTIFY_LEFT)
            etiqueta.show()
            h1.pack_start(etiqueta, expand=False, fill=False, padding=5)
            
            # renderizar preferencia
            if isinstance(defecto, list):
                
                if multiple:
                    textview = gtk.TextView()
                    buffer = gtk.TextBuffer()
                    for d in defecto:
                        buffer.insert_at_cursor("%s\n" % d)
                    textview.set_buffer(buffer)
                    textview.show()                
                    sw1 = gtk.ScrolledWindow()
                    sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                    sw1.set_size_request(-1, 140)
                    sw1.set_shadow_type(gtk.SHADOW_IN)
                    sw1.add(textview)
                    sw1.show()
                    h1.pack_start(sw1, expand=True, fill=True, padding=5)
                    
                    boton = gtk.Button(_('Por defecto'))
                    boton.connect('clicked', self.click_por_defecto_textview, textview)
                    boton.show()
                    h1.pack_start(boton, expand=False, fill=False, padding=5)

                else:
                    if config.DEBUG:
                        print "creando combobox"
                    liststore = gtk.ListStore(str)
                    combobox = gtk.ComboBox(liststore)
                    cell = gtk.CellRendererText()
                    combobox.pack_start(cell, True)
                    combobox.add_attribute(cell, 'text', 0)  
                    for d in defecto:
                        print d
                        combobox.append_text(d)
                    combobox.show()
                    entry = combobox
                    h1.pack_start(combobox, expand=False, fill=False, padding=5)
                    
                    boton = gtk.Button(_('Por defecto'))
                    boton.connect('clicked', self.click_por_defecto_combo, combobox)
                    boton.show()
                    h1.pack_start(boton, expand=False, fill=False, padding=5)

            else:
                entry = EntryRelacionado(name, defecto)
                entry.set_text(preferencia.valor)
                entry.set_max_length(255)
                entry.set_editable(True)
                entry.set_size_request(250, -1)
                entry.connect('changed' , self.entryModificado)
                entry.show()
                h1.pack_start(entry, expand=True, fill=True, padding=5)
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_entry, entry)
                boton.show()
                h1.pack_start(boton, expand=False, fill=False, padding=5)
            
            h1.show()

            vbox.pack_start(h1, expand=False, fill=False, padding=5)
            vbox.show()
        
    def entryModificado(self, entry):
        self.__setattr__(entry.name_pref, entry.get_text())
        
    def click_por_defecto_entry(self, boton, entry):
        entry.set_text(entry.defecto)
        
    def click_por_defecto_combo(self, boton, combo):
        pass
        
    def click_por_defecto_textview(self, boton, textview):
        pass

    # escribir en la BDD
    # escribir en el texbox
    def __setattr__(self, name, value):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            if config.DEBUG:
                print "guardando %s" % value
            preferencia.valor = str(value)
            session.commit()

    # leer del textbox
    # self.__getattribute__(self, "name")
    # http://pyref.infogami.com/__getattribute__
    def __getattr__(self, name):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            return str(preferencia.valor)
        
        return None
