#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import gtk
import gettext
from gettext import gettext as _

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
        
class ComboBoxRelacionado(gtk.ComboBox):
    
    def __init__(self, liststore, name_pref, defecto):
        gtk.ComboBox.__init__(self, liststore)
        self.name_pref = str(name_pref)
        self.defecto = str(defecto)    
        
class TextViewRelacionado(gtk.TextView):

    def __init__(self, name_pref, defecto):
        gtk.TextView.__init__(self)
        self.name_pref = str(name_pref)
        self.defecto = str(defecto)

class Preferencias:
    
    def __init__(self):
        pass

    def cargarPreferenciasPorDefecto(self, prefs_vbox):
        
        # Data type: 'bool', 'int', 'float', 'string', 'memo', 'select'        
        self.iniciarPreferencia('string', 'device_seleccionado')
        self.iniciarPreferencia('string', 'idgame_seleccionado')
        self.iniciarPreferencia('string', 'ruta_anadir', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_anadir_directorio', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_extraer_iso', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_copiar_caratulas', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_copiar_discos', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'URL_ZIP_WIITDB', defecto='http://wiitdb.com/wiitdb.zip', mostrar=True, vbox=prefs_vbox, label=_('URL Base de datos WiiTDB'))
        self.iniciarPreferencia('string', 'FORMATO_FECHA_WIITDB', defecto='%d/%m/%Y', mostrar=True, vbox=prefs_vbox, label=_('Formato fecha'))
        self.iniciarPreferencia('string', 'FORMATO_FECHA_CORTA_WIITDB', defecto='%Y/%m', mostrar=True, vbox=prefs_vbox, label=_('Formato fecha corto'))
        self.iniciarPreferencia('int', 'WIDTH_COVERS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Ancho imagen caratula'))
        self.iniciarPreferencia('int', 'HEIGHT_COVERS', defecto=224, mostrar=True, vbox=prefs_vbox, label=_('Altura imagen caratula'))
        self.iniciarPreferencia('int', 'WIDTH_DISCS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Ancho imagen disc-art'))
        self.iniciarPreferencia('int', 'HEIGHT_DISCS', defecto=160, mostrar=True, vbox=prefs_vbox, label=_('Altura imagen disc-art'))
        self.iniciarPreferencia('int', 'NUM_HILOS', defecto=15, mostrar=True, vbox=prefs_vbox, label=_('Num. Hilos para tareas de fondo'))
        
        # Listas de idiomas wiitdb
        WIITDB_LANGUAGE_LISTA =    [('EN', _('English')),
                                    ('JA', _('Japanese')),
                                    ('FR', _('French')),
                                    ('DE', _('German')),
                                    ('ES', _('Spanish')),
                                    ('IT', _('Italian')),
                                    ('NL', _('Dutch')),
                                    ('PT', _('Portuguese')),
                                    ('ZHTW', _('Chinese-Taiwan')),
                                    ('ZHCN', _('Chinese')),
                                    ('KO', _('Korean'))]
        self.iniciarPreferencia('select', 'LANG_PRINCIPAL', defecto='ES', mostrar=True, vbox=prefs_vbox, label=_('Idioma principal para el synopsis'), datos_lista = WIITDB_LANGUAGE_LISTA)
        self.iniciarPreferencia('select', 'LANG_SECUNDARIO', defecto='EN', mostrar=True, vbox=prefs_vbox, label=_('Idioma auxiliar para el synopsis'), datos_lista = WIITDB_LANGUAGE_LISTA)
        
        cycle_covers = ""
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/ES/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/EN/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/ES/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/EN/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/FR/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/pal/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/ntsc/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/ntscj/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/3d/160/225/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/widescreen/pal/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/widescreen/ntsc/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/widescreen/ntscj/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/fullcover/%s.png\n"
        self.iniciarPreferencia('memo', 'PROVIDER_COVERS', defecto=cycle_covers, mostrar=True, vbox=prefs_vbox, label=_('Proveedor de caratulas'))

    # indicar el vbox que inicia la preferencia
    def iniciarPreferencia(self, tipo, name, defecto = '', mostrar = False, vbox = None, label = '', datos_lista = None):
        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()
        if preferencia == None:
            preferencia = Preferencia(tipo, name, defecto)
            session.save(preferencia)
            session.commit()

        if mostrar:
            h1 = gtk.HBox(homogeneous=False, spacing=0)
            
            etiqueta = gtk.Label()
            etiqueta.set_text("<b>%s: </b>" % label)
            etiqueta.set_use_markup(True)
            etiqueta.set_justify(gtk.JUSTIFY_LEFT)
            etiqueta.show()
            h1.pack_start(etiqueta, expand=False, fill=False, padding=5)
            
            # renderizar preferencia
            if tipo == 'memo':
                
                textview = TextViewRelacionado(name, defecto)
                buffer = gtk.TextBuffer()
                buffer.set_text(preferencia.valor)
                buffer.connect("changed", self.memoModificado, textview)
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
                boton.connect('clicked', self.click_por_defecto_textview, buffer, textview)
                boton.show()
                h1.pack_start(boton, expand=False, fill=False, padding=5)

            elif tipo == 'select':
                if config.DEBUG:
                    print "creando combobox"

                liststore = gtk.ListStore(str)
                combobox = ComboBoxRelacionado(liststore, name, defecto)
                cell = gtk.CellRendererText()
                combobox.pack_start(cell, True)
                combobox.add_attribute(cell, 'text', 0)  
                for code, language in datos_lista:
                    combobox.append_text("%s" % (language))
                combobox.set_active(util.get_index_by_code(datos_lista, preferencia.valor))
                combobox.connect('changed' , self.comboModificado, datos_lista)
                combobox.show()
                h1.pack_start(combobox, expand=False, fill=False, padding=5)
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_combo, combobox, datos_lista)
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
        
    def comboModificado(self, combo, datos_lista):
        self.__setattr__(combo.name_pref, util.get_code_by_index(datos_lista, combo.get_active()))
        
    def memoModificado(self, buffer, textview):
        nuevoValor = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        self.__setattr__(textview.name_pref, nuevoValor)

    def click_por_defecto_entry(self, boton, entry):
        entry.set_text(entry.defecto)

    def click_por_defecto_combo(self, boton, combo, datos_lista):
        combo.set_active(util.get_index_by_code(datos_lista, combo.defecto))

    def click_por_defecto_textview(self, boton, buffer, textview):
        buffer.set_text(textview.defecto)

    # escribir en la BDD
    # escribir en el texbox
    def __setattr__(self, name, value):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            
            tipo = preferencia.tipo
            
            # Data type: 'bool', 'int', 'float', 'string', 'memo', 'select'
            if tipo == 'bool':
                preferencia.valor = value.lower() == 'true'
            elif tipo == 'int':
                preferencia.valor = int(value)
            elif tipo == 'float':
                preferencia.valor = float(value)
            elif tipo == 'string':
                preferencia.valor = str(value)
            elif tipo == 'memo':
                preferencia.valor = str(value)
            elif tipo == 'select':
                preferencia.valor = str(value)
            else:
                preferencia.valor = value

            session.commit()

    # leer del textbox
    # self.__getattribute__(self, "name")
    # http://pyref.infogami.com/__getattribute__
    def __getattr__(self, name):

        retorno = None
        
        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            
            tipo = preferencia.tipo
            valor = preferencia.valor

            # Data type: 'bool', 'int', 'float', 'string', 'memo', 'select'
            if tipo == 'bool':
                retorno = valor.lower() == 'true'
            elif tipo == 'int':
                retorno = int(valor)
            elif tipo == 'float':
                retorno = float(valor)
            elif tipo == 'string':
                retorno = str(valor)
            elif tipo == 'memo':
                retorno = valor.strip().split('\n')
            elif tipo == 'select':
                retorno = str(valor)
            else:
                retorno = valor

        return retorno
