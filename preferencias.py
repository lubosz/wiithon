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
        
class CheckRelacionado(gtk.CheckButton):

    def __init__(self, name_pref, defecto, label):
        gtk.CheckButton.__init__(self, label)
        self.name_pref = str(name_pref)
        self.defecto = defecto

class Preferencias:

    def cargarPreferenciasPorDefecto(self,  prefs_vbox_general = None,
                                            prefs_vbox_caratulas = None,
                                            prefs_vbox_wiitdb = None,
                                            prefs_vbox_buscadores = None,
                                            cargarWidget = False):
        
        # Data type: 'bool', 'int', 'float', 'string', 'password' , 'memo', 'select'
        self.iniciarPreferencia('string', 'device_seleccionado')
        self.iniciarPreferencia('string', 'idgame_seleccionado')
        self.iniciarPreferencia('string', 'ruta_anadir', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_anadir_directorio', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_extraer_iso', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_copiar_caratulas', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'ruta_copiar_discos', defecto=os.getcwd())
        self.iniciarPreferencia('string', 'tipo_caratula', defecto=util.COVER_NORMAL)
        self.iniciarPreferencia('string', 'tipo_disc_art', defecto=util.DISC_ORIGINAL)
        
        # general
        APP_LANGUAGE_LISTA    =    [('en', _('English')),
                                     ('es', _('Spanish')),
                                     ('it', _('Italian')),
                                     ('fr', _('French')),
                                     ('de', _('German')),
                                     ('nl_NL', _('Dutch')),
                                     ('ca_ES', _('Catalan')),
                                     ('pt_BR', _('Brazilian Portuguese')),
                                     ('pt_PT', _('Portuguese')),
                                     ('sv_SE', _('Swedish')),
                                     ('gl_ES', _('Galician')),
                                     ('eu_ES', _('Euskera')),
                                     ('da_DK', _('Danish'))
                                     ]
        self.iniciarPreferencia('select', 'APPLICATION_LANGUAGE', defecto=util.get_lang_default(APP_LANGUAGE_LISTA), mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Idioma de wiithon'), datos_lista = APP_LANGUAGE_LISTA)
        self.iniciarPreferencia('string', 'ruta_extraer_rar', defecto='/tmp', mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Ruta para extraer ficheros .rar. Para descomprimir junto al .rar escriba .'))
        self.iniciarPreferencia('int', 'NUM_HILOS', defecto=16, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Num. Hilos para tareas de fondo'))
        self.iniciarPreferencia('string', 'COMANDO_ABRIR_CARPETA', defecto='gnome-open', mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Comando para abrir carpetas'))
        self.iniciarPreferencia('string', 'COMANDO_ABRIR_WEB', defecto='gnome-open', mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Comando para abrir paginas Web'))
        self.iniciarPreferencia('bool', 'ADVERTENCIA_ACTUALIZAR_WIITDB', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Mostrar una advertencia cuando no hay ninguna informacion WiiTDB'))
        self.iniciarPreferencia('bool', 'ADVERTENCIA_NO_WBFS', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Mostrar una advertencia cuando no hay particiones WBFS'))
        self.iniciarPreferencia('bool', 'init_minimize', defecto=False, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Iniciar maximizado'))
        self.iniciarPreferencia('bool', 'DRAG_AND_DROP_LOCAL', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Permitir establecer caratulas locales por arrastre'))
        self.iniciarPreferencia('bool', 'DRAG_AND_DROP_HTTP', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Permitir establecer caratulas desde http por arrastre'))
        self.iniciarPreferencia('bool', 'DRAG_AND_DROP_JUEGOS', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Permitir arrastrar juegos en ISO, RAR o directorios.'))
        self.iniciarPreferencia('bool', 'rar_overwrite_iso', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Los isos descomprimidos desde el rar remplaza imagenes iso sin preguntar.'))
        self.iniciarPreferencia('bool', 'rar_preguntar_borrar_iso', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Pregunta borrar el .iso (cuando aniamos un rar)'))
        self.iniciarPreferencia('bool', 'rar_preguntar_borrar_rar', defecto=False, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Pregunta borrar el .rar (cuando aniamos un rar)'))
        self.iniciarPreferencia('bool', 'proponer_nombre', defecto=True, mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Proponer un nombre de wiitdb tras anadir el juego'))
        DESTINO_DRAG_AND_DROP =    [('C', _('Caratula')),
                                    ('D', _('Disc-art'))]
        self.iniciarPreferencia('select', 'DESTINO_ARRASTRE', defecto='C', mostrar=cargarWidget, vbox=prefs_vbox_general, label=_('Destino del arrastre de una imagen'), datos_lista = DESTINO_DRAG_AND_DROP)
        
        # It dont work for Chinese / Chinese-Taiwan
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

        defecto_principal = util.get_lang_default(WIITDB_LANGUAGE_LISTA).upper()
        if defecto_principal == 'EN':
            defecto_secundario = 'ES'
        else:
            defecto_secundario = 'EN'
        
        # wiitdb
        self.iniciarPreferencia('string', 'URL_ZIP_WIITDB', defecto='http://wiitdb.com/wiitdb.zip', mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('URL principal para WiiTDB'))
        self.iniciarPreferencia('string', 'FORMATO_FECHA_WIITDB', defecto='%d/%m/%Y', mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Formato fecha'))
        self.iniciarPreferencia('string', 'FORMATO_FECHA_CORTA_WIITDB', defecto='%Y/%m', mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Formato fecha corto'))        
        self.iniciarPreferencia('select', 'LANG_PRINCIPAL', defecto=defecto_principal, mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Idioma principal para el synopsis'), datos_lista = WIITDB_LANGUAGE_LISTA)
        self.iniciarPreferencia('select', 'LANG_SECUNDARIO', defecto=defecto_secundario, mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Idioma auxiliar para el synopsis'), datos_lista = WIITDB_LANGUAGE_LISTA)
        self.iniciarPreferencia('string', 'USER_WIITDB', defecto='', mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Usuario (para editar informacion en wiitdb.com)'))
        self.iniciarPreferencia('password', 'PASS_WIITDB', defecto='', mostrar=cargarWidget, vbox=prefs_vbox_wiitdb, label=_('Password (para editar informacion en wiitdb.com)'))
        
        # caratulas
        self.iniciarPreferencia('int', 'WIDTH_COVERS', defecto=160, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Ancho imagen caratula'))
        self.iniciarPreferencia('int', 'HEIGHT_COVERS', defecto=224, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Altura imagen caratula'))
        self.iniciarPreferencia('int', 'WIDTH_DISCS', defecto=160, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Ancho imagen disc-art'))
        self.iniciarPreferencia('int', 'HEIGHT_DISCS', defecto=160, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Altura imagen disc-art'))

        cycle_covers = ""
        #   - flat
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/ES/%s.png\n"    # 0
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/EN/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/pal/%s.png\n"
        cycle_covers += "http://boxart.rowdyruff.net/flat/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/FR/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/DE/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/IT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/NL/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/PT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/AU/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/US/%s.png\n"    # 10
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover/JA/%s.png\n"
        cycle_covers += "http://wiiboxart.t35.com/wiiboxart/images/2d/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/ntsc/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/ntscj/%s.png\n"
        
        #   - 3d
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/ES/%s.png\n"  # 15
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/EN/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/3d/160/225/%s.png\n"
        cycle_covers += "http://wiiboxart.t35.com/wiiboxart/images/3d/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/FR/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/DE/%s.png\n"  # 20
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/IT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/NL/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/PT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/AU/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/US/%s.png\n"  # 25
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/cover3D/JA/%s.png\n"
        cycle_covers += "http://boxart.rowdyruff.net/3d/%s.png\n"
              
        #   - hq
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/ES/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/EN/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/FR/%s.png\n"  # 30
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/DE/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/IT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/NL/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/PT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/AU/%s.png\n" # 35
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/US/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfullHQ/JA/%s.png\n"
        
        #   - widescreen
        cycle_covers += "http://wiiboxart.t35.com/wiiboxart/images/widescreen/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/widescreen/pal/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/widescreen/ntsc/%s.png\n"         # 40
        cycle_covers += "http://www.wiiboxart.com/widescreen/ntscj/%s.png\n"
        
        #   - full
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/ES/%s.png\n"    # 42
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/EN/%s.png\n"
        cycle_covers += "http://www.wiiboxart.com/fullcover/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/FR/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/DE/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/IT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/NL/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/PT/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/AU/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/US/%s.png\n"
        cycle_covers += "http://wiitdb.com/wiitdb/artwork/coverfull/JA/%s.png\n"
        cycle_covers += "http://wiiboxart.t35.com/wiiboxart/images/full/%s.png\n"

        self.iniciarPreferencia('memo', 'PROVIDER_COVERS', defecto=cycle_covers, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Proveedor de caratulas'))

        cycle_discs = ""
        #   - disc & disccustom
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/ES/%s.png\n"                  # 0
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/EN/%s.png\n"
        cycle_discs += "http://www.wiiboxart.com/diskart/160/160/%.3s.png\n"
        cycle_discs += "http://wiiboxart.t35.com/wiiboxart/images/disc/hidef/%s.png\n"
        cycle_discs += "http://wiiboxart.t35.com/wiiboxart/images/disc/standard/%s.png\n"
        cycle_discs += "http://wiiboxart.t35.com/wiiboxart/images/disc/regional/%s.png\n"   # 5
        cycle_discs += "http://boxart.rowdyruff.net/fulldisc/%s.png\n"
        cycle_discs += "http://www.wiiboxart.com/discs/%.3s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/FR/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/DE/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/IT/%s.png\n"                  # 10
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/NL/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/PT/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/AU/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/US/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disc/JA/%s.png\n"                  # 15
        cycle_discs += "http://boxart.rowdyruff.net/disc/%.3s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/ES/%s.png\n"            # 17
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/EN/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/FR/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/DE/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/IT/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/NL/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/PT/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/AU/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/US/%s.png\n"
        cycle_discs += "http://wiitdb.com/wiitdb/artwork/disccustom/JA/%s.png\n"
        self.iniciarPreferencia('memo', 'PROVIDER_DISCS', defecto=cycle_discs, mostrar=cargarWidget, vbox=prefs_vbox_caratulas, label=_('Proveedor de discos'))
        
        # Buscadores
        self.iniciarPreferencia('string', 'BUSCAR_URL_GOOGLE', defecto="http://www.google.es/#hl=es&q=%s&meta=&aq=f&oq=&fp=5251967318b7af98", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en Google. (%s es el nombre del juego)'))
        self.iniciarPreferencia('string', 'BUSCAR_URL_WIKIPEDIA', defecto="http://es.wikipedia.org/w/index.php?title=Especial:Buscar&search=%s&fulltext=Buscar", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en Wikipedia. (%s es el nombre del juego)'))
        self.iniciarPreferencia('string', 'BUSCAR_URL_YOUTUBE', defecto="http://www.youtube.com/results?search_query=%s&search_type=&aq=f", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en Youtube. (%s es el nombre del juego)'))
        self.iniciarPreferencia('string', 'BUSCAR_URL_IGN', defecto="http://search.ign.com/products?query=%s", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en IGN. (%s es el nombre del juego)'))
        self.iniciarPreferencia('string', 'BUSCAR_URL_GAMESPOT', defecto="http://www.gamespot.com/search.html?qs=%s&om_act=convert&om_clk=search", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en GameSpot. (%s es el nombre del juego)'))
        self.iniciarPreferencia('string', 'BUSCAR_URL_VGCHARTZ', defecto="http://www.vgchartz.com/games/index.php?name=&keyword=%s&console=Wii&region=All&developer=&publisher=&genre=&boxart=Both&results=50&order=Hits", mostrar=cargarWidget, vbox=prefs_vbox_buscadores, label=_('URL de busqueda en VGChartz. (%s es el nombre del juego)'))

    # indicar el vbox que inicia la preferencia
    def iniciarPreferencia(self, tipo, name, defecto = '', mostrar = False, vbox = None, label = '', datos_lista = None):
        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()
        if preferencia == None:
            preferencia = Preferencia(tipo, name, defecto)
            # for compatibility with sqlalchemy
            try:
                session.add(preferencia)
            except:
                session.save(preferencia)
            session.commit()

        if mostrar:
            h1 = gtk.HBox(homogeneous=False, spacing=0)
            
            etiqueta = gtk.Label()
            etiqueta.set_text("%s : " % label)
            etiqueta.set_use_markup(True)
            # 1 line
            etiqueta.set_alignment(0.0 , 0.5)
            etiqueta.set_padding(5, -1)
            # > 1 linea
            #etiqueta.set_justify(gtk.JUSTIFY_LEFT)
            etiqueta.show()
            
            # renderizar preferencia
            if tipo == 'memo':
                
                h2 = gtk.HBox(homogeneous=False, spacing=0)
                v1 = gtk.VBox(homogeneous=False, spacing=5)
                
                textview = TextViewRelacionado(name, defecto)
                buffer = gtk.TextBuffer()
                buffer.set_text(preferencia.valor)
                buffer.connect("changed", self.memoModificado, textview)
                textview.set_buffer(buffer)
                textview.show()                
                sw1 = gtk.ScrolledWindow()
                sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                sw1.set_size_request(-1, 120)
                sw1.set_shadow_type(gtk.SHADOW_IN)
                sw1.add(textview)
                sw1.show()
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_textview, buffer, textview)
                boton.show()
                
                etiqueta.set_alignment(0.0 , 1.0)
                
                h2.show()
                v1.show()
                
                h2.pack_start(etiqueta, expand=True, fill=True, padding=0)
                h2.pack_start(boton, expand=False, fill=False, padding=0)
                
                v1.pack_start(h2, expand=True, fill=True, padding=0)
                v1.pack_start(sw1, expand=True, fill=True, padding=0)
                
                h1.pack_start(v1, expand=True, fill=True, padding=0)

            elif tipo == 'select':
                if config.DEBUG:
                    print "creando combobox"
                
                # ponemos la etiqueta en la izquierda    
                h1.pack_start(etiqueta, expand=False, fill=False, padding=0)

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
                h1.pack_start(combobox, expand=False, fill=False, padding=0)
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_combo, combobox, datos_lista)
                boton.show()
                h1.pack_start(boton, expand=False, fill=False, padding=0)

            elif tipo == 'bool':
                
                if config.DEBUG:
                    print "creando check"

                check_button = CheckRelacionado(name, defecto, label)
                check_button.set_active(preferencia.valor == "True")
                check_button.connect("toggled", self.checkModificado)
                check_button.show()
                
                # ponemos la etiqueta en la izquierda    
                h1.pack_start(check_button, expand=False, fill=False, padding=0)
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_check, check_button)
                boton.show()
                h1.pack_start(boton, expand=False, fill=False, padding=0)

            else:
                
                # ponemos la etiqueta en la izquierda    
                h1.pack_start(etiqueta, expand=False, fill=False, padding=0)
                
                entry = EntryRelacionado(name, defecto)
                entry.set_text(preferencia.valor)
                entry.set_max_length(255)
                entry.set_editable(True)
                entry.set_size_request(250, -1)
                if tipo == 'password':
                    entry.set_visibility(False)
                    
                entry.connect('changed' , self.entryModificado)
                entry.show()
                h1.pack_start(entry, expand=True, fill=True, padding=0)
                
                boton = gtk.Button(_('Por defecto'))
                boton.connect('clicked', self.click_por_defecto_entry, entry)
                boton.show()
                h1.pack_start(boton, expand=False, fill=False, padding=0)
            
            h1.show()

            vbox.pack_start(h1, expand=False, fill=False, padding=0)
        
    def entryModificado(self, entry):
        #try:
        self.__setattr__(entry.name_pref, entry.get_text())
        #except AssertionError:
        entry.set_text(str(self.__getattr__(entry.name_pref)))
        
    def comboModificado(self, combo, datos_lista):
        self.__setattr__(combo.name_pref, util.get_code_by_index(datos_lista, combo.get_active()))
        
    def memoModificado(self, buffer, textview):
        nuevoValor = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        self.__setattr__(textview.name_pref, nuevoValor)
        
    def checkModificado(self, check):
        self.__setattr__(check.name_pref, check.get_active())

    def click_por_defecto_entry(self, boton, entry):
        entry.set_text(entry.defecto)

    def click_por_defecto_combo(self, boton, combo, datos_lista):
        combo.set_active(util.get_index_by_code(datos_lista, combo.defecto))

    def click_por_defecto_textview(self, boton, buffer, textview):
        buffer.set_text(textview.defecto)
        
    def click_por_defecto_check(self, boton, check):
        check.set_active(check.defecto)

    def __setattr__(self, name, value):

        sql = util.decode("preferencias.campo=='%s'" % name)
        preferencia = session.query(Preferencia).filter(sql).first()

        if preferencia != None:
            
            tipo = preferencia.tipo
            
            try:
            
                # Data type: 'bool', 'int', 'float', 'string', 'password' , 'memo', 'select'
                if tipo == 'int':
                    preferencia.valor = int(value)
                elif tipo == 'float':
                    preferencia.valor = float(value)
                else:# string | password | memo | select | bool
                    preferencia.valor = str(value)

                session.commit()
            except:
                session.rollback()
                if config.DEBUG:
                    print "%s ignored" % value
                

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

            # Data type: 'bool', 'int', 'float', 'string', 'password', 'memo', 'select'
            if tipo == 'bool':
                retorno = valor == "True"
            elif tipo == 'int':
                retorno = int(valor)
            elif tipo == 'float':
                retorno = float(valor)
            elif tipo == 'memo':
                retorno = valor.strip().split('\n')
            else:# string | password | select | bool
                retorno = str(valor)

        return retorno
