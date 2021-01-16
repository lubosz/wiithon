#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import fnmatch
import gtk
import subprocess
import copy
import httplib
import urllib
import re
import locale
import gettext
import statvfs
import random
import time
from threading import Thread
from gettext import gettext as _

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

import config

BLACK_LIST = "/\"$|[]"
BLACK_LIST2 = "\";$\\"

(DISC_ORIGINAL, DISC_CUSTOM)=([ "%d" % i for i in range(2) ])
(COVER_NORMAL, COVER_3D, COVER_FULL)=([ "%d" % i for i in range(3) ])

class NonRepeatList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def append(self, element):
        if not self.count(element):
            list.append(self, element)

    def extend(self, iterable):
        for i in iterable:
            self.append(i)

def getExtension(fichero):
    posPunto = fichero.rfind(".")
    if posPunto != -1:
        return fichero[posPunto+1:len(fichero)].lower()
    else:
        return fichero

# si es una ruta -> pasarla por os.path.basename
def getNombreFichero(fichero):
    posPunto = fichero.rfind(".")
    if posPunto != -1:
        return fichero[0:posPunto]
    else:
        return fichero

def getMagicISO(imagenISO, formato):

    magic = ''
    if formato == 'iso':
        if os.path.exists(imagenISO):
            f = open(imagenISO , "r")
            magic = f.read(6)
            f.close()

    elif formato == 'wbfs':
        comando = 'hexdump "%s" -s 0x200 -n 6 -e \'6/1 "%%_u"\'' % imagenISO
        magic = getSTDOUT(comando)

    elif formato == 'wdf':
        comando = 'hexdump "%s" -s 0x38 -n 6 -e \'6/1 "%%_u"\'' % imagenISO
        magic = getSTDOUT(comando)

    if len(magic) == 6 and re.match("[A-Z0-9]{6}",magic):
        return magic
    else:
        return None

def tieneCaracteresRaros(cadena , listaNegra = BLACK_LIST):
    # Nos dice si *cadena* tiene caracteres raros dados por una lista negra
    for i in range(len(cadena)):
        for j in range(len(listaNegra)):
            if (cadena[i]==listaNegra[j]):
                return True
    return False
    
def quitarCaracteresRaros(cadena, listaNegra = BLACK_LIST):
    for i in range(len(listaNegra)):
        cadena = cadena.replace(listaNegra[i],'')
    return cadena
    
# esta función la voy a evitar y acabaré por eliminarla
def getPopen( comando ):
    sp = subprocess
    return sp.Popen(comando.split() , stdout=sp.PIPE ,stderr=sp.STDOUT , close_fds=False , shell=False, universal_newlines= True)

def getSTDOUT_iterador(comando):
    p = subprocess.Popen(comando , shell=True , stdout=subprocess.PIPE , stderr=subprocess.STDOUT)
    out = p.stdout.readlines()
    return out

def getSTDOUT_NOERROR_iterador(comando):
    p = subprocess.Popen(comando , shell=True , stdout=subprocess.PIPE , stderr=open("/dev/null" , "w"))
    out = p.stdout.readlines()
    return out

def getSTDOUT(comando , mostrarError = False):
    if mostrarError:
        out = getSTDOUT_iterador(comando)
    else:
        out = getSTDOUT_NOERROR_iterador(comando)
    salida = ""
    for linea in out:
        salida = salida + linea.strip()
    return salida

def escribir(f , texto):
    f.write(texto + "\n")
    f.flush()

def try_mkdir(carpeta):
    if not os.path.exists(carpeta):
        os.mkdir(carpeta)

def clonarOBJ(x):
    return copy.deepcopy(x)

'''
Un ejemplo de las listas de python

import popen2
popen = popen2.Popen3("ls /etc/services noexiste", capturestderr=True)
stdout = popen.fromchild.read()
stderr = popen.childerr.read()
retcode = popen.wait() >> 8
'''

# Devuelve una lista de directorios del directorio "path"
# http://newspiritcompany.infogami.com/recursive_glob_py
def glob_get_dirs(path):
    d = []
    try:
        for i in os.listdir(path):
            if os.path.isdir(path+i):
                d.append(os.path.basename(i))

    except NameError, ne:
        print "NameError thrown=", ne
    except:
        pass
    return d

# Devuelve la lista de resultados que cumplen la Exp.Reg.
# Recorre a partir de "path" y recursivamente.
def rec_glob(path , mask):
    l = []

    if path[-1] != '/':
        path = path + '/'

    for i in glob_get_dirs(path):
        res = rec_glob(path + i, mask)
        l = l + res

    try:
        for i in os.listdir(path):
            ii = i
            i = path + i
            if os.path.isfile(i):
                if fnmatch.fnmatch( ii.lower() , mask.lower() ):
                    l.append(i)
    except NameError, ne:
        print "NameError=", ne
    except:
        pass
    return l

## demo de gtk.Entry con Sexy (o no, si lo tienes instalado)
## ENTRY: Use python sexy if available, gtk otherwise
try:
    import sexy
    class Entry(sexy.IconEntry):

        def __init__(self, clear=False, copy=False):
            sexy.IconEntry.__init__(self)
            self.__clipboard = gtk.Clipboard() # This is a singleton
            if clear:
                self.add_clear_button()

            if copy:
                icon = gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
                self.connect("icon_released", self.on_copy_clicked)

                self.set_icon(sexy.ICON_ENTRY_SECONDARY, icon)
                self.set_icon_highlight(sexy.ICON_ENTRY_SECONDARY, True)

        def on_copy_clicked(self, widget, icon_pos, button):
            if icon_pos != sexy.ICON_ENTRY_SECONDARY or button != 1:
                return True

            self.__clipboard.set_text(str(self.get_text()))

except:
    #logging.warning("There is no python-sexy available. fallback to standard gtk.")
    import gtk
    class Entry(gtk.Entry):
        def __init__(self, clear=False, copy=False):
            gtk.Entry.__init__(self)

'''

GET /diskart/160/160/RYX.png HTTP/1.1
Host: www.wiiboxart.com
User-Agent: Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.11) Gecko/2009060310 Ubuntu/8.10 (intrepid) Firefox/3.0.11
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: es-es,es;q=0.8,en-us;q=0.5,en;q=0.3
Accept-Encoding: gzip,deflate
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7
Keep-Alive: 300
Connection: keep-alive
Referer: http://www.wiiboxart.com/pal.php

HTTP/1.1 200 OK
Date: Tue, 30 Jun 2009 23:01:42 GMT
Server: Apache/1.3.41 (Unix) PHP/5.2.6 mod_log_bytes/1.2 mod_bwlimited/1.4 mod_auth_passthrough/1.8 FrontPage/5.0.2.2635 mod_ssl/2.8.31 OpenSSL/0.9.7a
X-Powered-By: PHP/5.2.6
Keep-Alive: timeout=15, max=100
Connection: Keep-Alive
Transfer-Encoding: chunked
Content-Type: image/png

'''

class ErrorDescargando(Exception):
    pass

class YaEstaDescargado(Exception):
    pass

def descargar(url, destino):
    '''
    try:
        webFile = urllib.urlopen(url)
        localFile = open(destino, 'w')
        buffer = webFile.read()
        localFile.write(buffer)
        webFile.close()
        localFile.close()
    except:
        raise ErrorDescargando
    '''
    if not call_out_null("wget %s -O %s" % (url, destino)):
        raise ErrorDescargando

def descargarImagen(url, destino, type = "image/png"):
    try:
        dominio, ruta_imagen = getDominioYRuta(url)
        
        conn = httplib.HTTPConnection(dominio)

        VER, REV = getVersionRevision()
        useragent = "wiithon %s r%s" % (VER, REV)

        params = None
        headers =   {
                        "Host": dominio,
                        "User-Agent": useragent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Encoding": "gzip,deflate",
                        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                    }
        
        conn.request ("GET", '/%s' % (ruta_imagen), params, headers)
        
        r = conn.getresponse()
        
        ###  BUSCAR MIME PNG ###
        headers = r.getheaders()
        i = 0
        encontrado = False
        while (not encontrado) and (i<len(headers)):
            if headers[i][0] == "content-type":
                encontrado = (headers[i][1] == type)
            if not encontrado:
                i = i + 1
        ### /BUSCAR MIME PNG ###
        
        if encontrado and r.status == 200 and r.reason == "OK":
            fichero = file( destino, "wb" )
            fichero.write(r.read())
            fichero.close()

            conn.close()
        else:
            conn.close()
            raise ErrorDescargando
    except:
        raise ErrorDescargando
        
def getDominioYRuta(url, protocolo = 'http://'):
    pos = url.find(protocolo)
    if(pos != -1):
        url = url[len(protocolo):]
    pos = url.find("/")
    if(pos != -1):
        return url[:pos], url[pos+1:]
    else:
        return url , ""

# Identifies APNGs
# Written by Foone/Popcorn Mariachi#!9i78bPeIxI
# This code is in the public domain
# identify_png returns:
# '?'   for non-png or corrupt PNG
# 'png'  for a standard png 
# 'apng' for an APNG
# takes one argument, a file handle. When the function reutrns it'll be positioned at the start of the file
# usage:
#  fop=open('tempfile.dat','rb')
#  type=identify_png(fop)
import struct
PNG_SIGNATURE='\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
def esPNG(ruta):
    if os.path.exists(ruta):
        f = file(ruta, "r")
        data=f.read(8)
        if data!=PNG_SIGNATURE:
            return False # not a PNG/APNG
        try:
            while True:
                buffer=f.read(8)
                if len(buffer)!=8:
                    return False # Early EOF
                length,type=struct.unpack('!L4s',buffer)
                if type in ('IDAT','IEND'):
                    # acTL must come before IDAT, so if we see an IDAT this is plain PNG
                    # IEND is end of file.
                    return True
                if type=='acTL':
                    return True
                f.seek(length+4,1) # +4 because of the CRC (not checked)
        finally:
            f.seek(0)
    else:
        return False

def decode(s, code = 'utf-8'):
    try:
        return s.decode(code)
    except UnicodeDecodeError:
        try:
            text = unicode(s, 'ASCII', 'strict')
            return s.decode('ASCII')
        except UnicodeDecodeError:
            pass

        try:
            text = unicode(s, 'ISO-8859-1', 'strict')
            return s.decode('ISO-8859-1')
        except UnicodeDecodeError:
            pass
            
        try:
            text = unicode(s, 'ISO-8859-15', 'strict')
            return s.decode('ISO-8859-15')
        except UnicodeDecodeError:
            pass

class NoDeberiaPasar(Exception):
    pass

class CauseException(Exception):
    pass

# lanzado por particion
class SintaxisInvalida(Exception):
    pass

def getBDD():
    #db = create_engine(config.URI_ENGINE)
    db = create_engine(config.URI_ENGINE+'?check_same_thread=False', poolclass=NullPool)
    return db

def crearBDD(metadatos):
    db = getBDD()
    metadatos.create_all(db)
    
def borrarBDD(metadatos):
    db = getBDD()
    metadatos.drop_all(db)    

def getSesionBDD(db):
    # con scoped se resuelven todos los problemas de concurrencia!
    ##Session = scoped_session(sessionmaker(bind=db, autoflush=True, transactional=True))
    Session = scoped_session(sessionmaker(bind=db, autoflush=True))
    session = Session()
    return session

def sql_text(string):
	return sqlalchemy.text(string)

def call_out_file(comando):
    if config.DEBUG:
        print comando
    try:
        salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open(config.HOME_WIITHON_LOGS_PROCESO , "w") )
        return salida == 0
    except KeyboardInterrupt:
        return False
    except TypeError:
        return False

def call_out_null(comando):
    if config.DEBUG:
        print comando
    try:
        salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT , stdout=open("/dev/null" , "w") )
        return salida == 0
    except KeyboardInterrupt:
        return False
    except TypeError:
        return False

def call_out_screen(comando):
    if config.DEBUG:
        print comando
    try:
        salida = subprocess.call( comando , shell=True , stderr=subprocess.STDOUT)
        return salida == 0
    except KeyboardInterrupt:
        return False
    except TypeError:
        return False
        
def descomprimirZIP(file_in, file_out):
    try:
        import zipfile
        zip = zipfile.ZipFile(file_in)
        zip.extract(file_out)
        zip.close()
    except:
        comando = 'unzip -o "%s" "%s"' % (file_in, file_out)
        call_out_null(comando)

def parsear_a_XML(texto):
    texto = texto.replace("&" , "&amp;")
    texto = texto.replace(">" , "&gt;")
    texto = texto.replace("<" , "&lt;")
    texto = texto.replace("\'" , "&apos;")    
    return texto
    
# as "urllib.quote()"
def encode_strange_characters_url(texto):
    texto = strip_multiples_spaces(texto)
    texto = texto.replace("&" , "%26")
    texto = texto.replace("/" , "%2F") 
    texto = texto.replace("á" , "%E1")
    texto = texto.replace("é" , "%E9")
    texto = texto.replace("í" , "%ED")
    texto = texto.replace("ó" , "%F3")
    texto = texto.replace("ú" , "%FA")
    texto = texto.replace("ñ" , "%F1")
    texto = texto.replace("€" , "%80")
    texto = texto.replace(" " , "%20")
    texto = texto.replace(":" , "%3A")
    return texto
    
def strip_multiples_spaces(texto):
    return " ".join(texto.split())

def setLanguage(locale = 'default'):
        
    if locale == 'default':
        gettext.install(config.APP,config.LOCALE, unicode=1)
    else:
        lang = gettext.translation(config.APP, languages=[locale])
        lang.install()
        os.environ['LANGUAGE'] = locale

def configurarLenguaje(inicial = 'default'):

    if inicial == 'es':
        lang = 'es_ES.UTF-8'
    elif inicial == 'it':
        lang = 'it_IT.UTF-8'
    elif inicial == 'en':
        lang = 'en_US.UTF-8'
    elif inicial == 'fr':
        lang = 'fr_FR.UTF-8'
    elif inicial == 'de':
        lang = 'de_DE.UTF-8'
    elif inicial == 'nl_NL':
        lang = 'nl_NL.UTF-8'
    elif inicial == 'pt_BR':
        lang = 'pt_BR.UTF-8'
    elif inicial == 'pt_PT':
        lang = 'pt_PT.UTF-8'
    elif inicial == 'ca_ES':
        lang = 'ca_ES.UTF-8'

    try:
        locale.setlocale(locale.LC_ALL, lang)
    except:
        locale.setlocale(locale.LC_ALL, '')

    for module in (gettext, gtk.glade):
        module.bindtextdomain(config.APP,config.LOCALE)
        module.textdomain(config.APP)
        
    setLanguage(inicial)

def get_lang_default(APP_LANGUAGE_LISTA):
    try:
        LANG = os.environ['LANG'].split('_')[0]
        encontrado = False
        i = 0
        while not encontrado and i<len(APP_LANGUAGE_LISTA):
            value = APP_LANGUAGE_LISTA[i][0]
            language = APP_LANGUAGE_LISTA[i][1]
            encontrado = value.lower() == LANG
            i += 1
        
        if not encontrado:
            return config.LANGUAGE_WIITHON_DEFAULT
        else:
            return LANG
    except:
        return config.LANGUAGE_WIITHON_DEFAULT

def remove_last_separator(text):
    text=text.rstrip(', ') 
    return text.rstrip(': ')

def get_index_by_code(lista, code):
    i = 0
    for c, language in lista:
        if c == code:
            return i
        else:
            i += 1
    return -1

def get_code_by_index(lista, index):
    i = 0
    for code, language in lista:
        if i == index:
            return code
        else:
            i += 1
    return None

# True ---> space OK
# False --> full disk
def space_for_dvd_iso_wii(path):
    # check for 4.4 GB of free space before to extract ISO
    fs = os.statvfs(path)
    return ((fs[statvfs.F_BSIZE]*fs[statvfs.F_BAVAIL]/1024) >= 4693504)

def esImagen(fichero):
    return  (getExtension(fichero)=="png") or (getExtension(fichero)=="jpg") or (getExtension(fichero)=="gif") or (getExtension(fichero)=="jpeg")

## check user group and permissions
def check_gids():
    
    try:
        group = 0
        file=open("/etc/group","r")
        for line in file:
            if line.startswith("disk:"):
                group = int(line.split(":")[2])
                break
        file.close()
        return group in os.getgroups()
    except:
        return False

def rand(min, max):
    return random.randint(min, max)

def num_files_in_folder(folder):
    return len(os.listdir(folder))

def getVersionRevision():
    revision = getSTDOUT("cat /usr/share/doc/wiithon/REVISION")
    version = getSTDOUT("python /usr/share/doc/wiithon/VERSION %s" % revision)
    cachos = version.split("-")
    if len(cachos) > 1:
        version = cachos[0]
        revision = cachos[1]
    else:
        version = cachos[0]
        revision = ''
    return version, revision

class SesionWiiTDB:

    def __init__(self):
        self.dominio = config.URL_WIITDB
        self.connected = False
        self.PHPSESSID = None
        self.timeout = 0

    def conectar_wiitdb(self, user, password):
        
        if config.DEBUG:
            print "conectar_wiitdb"
        
        if not self.connected:

            conn = httplib.HTTPConnection(self.dominio)

            data = {    'authid': user,
                        'authpw': password}

            params = urllib.urlencode(data)
                
            headers = {
                        "Host": self.dominio,
                        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.5) Gecko/20091109 Ubuntu/9.10 (karmic) Firefox/3.5.5",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "es-es,es;q=0.8,en-us;q=0.5,en;q=0.3",
                        "Accept-Encoding": "gzip,deflate",
                        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                        "Keep-Alive": "300",
                        "Connection": "keep-alive",
                        "Referer": "http://%s/Login/Signup?action=login" % (self.dominio),
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Content-Length": "%d" % (len(user)+len(password)+2*len("authid")+2+1)
                        }

            conn.request ("POST", '/Login/Signup?action=login', params, headers)
            r = conn.getresponse()
            
            ###  BUSCAR PHPSESSID ###
            headers = r.getheaders()
            i = 0
            encontrado = False
            while (not encontrado) and (i<len(headers)):
                encontrado = headers[i][0] == "set-cookie"
                if not encontrado:
                    i = i + 1
            ### /BUSCAR MIME PNG ###
            
            conn.close()
            
            self.connected = encontrado
            if self.connected:
                s = headers[i][1]
                self.PHPSESSID = s[s.find("=")+1:s.find(";")]
                self.timeout = time.time()

    def desconectar_wiitdb(self):
        
        if config.DEBUG:
            print "desconectar_wiitdb"
        
        if self.connected:

            conn = httplib.HTTPConnection(self.dominio)
            
            params = None
            headers = {
                            "Host": self.dominio,
                            "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.5) Gecko/20091109 Ubuntu/9.10 (karmic) Firefox/3.5.5",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "es-es,es;q=0.8,en-us;q=0.5,en;q=0.3",
                            "Accept-Encoding": "gzip,deflate",
                            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                            "Keep-Alive": "300",
                            "Connection": "keep-alive",
                            "Referer": "http://" % self.dominio,
                            "Cookie": "PHPSESSID=%s" % self.PHPSESSID
                        }
            conn.request ("GET", 'Login/Signup?action=logout', params, headers)
            r = conn.getresponse()
            conn.close()
            self.connected = False
            self.PHPSESSID = None
            self.timeout = 0
            
    def connect_if_need_it(self, user, password):
        tries = 3
        minutes_timeout = 15
        i = 0
        while i<tries and not self.connected and (time.time()-self.timeout) > (minutes_timeout*60):
            self.desconectar_wiitdb()
            self.conectar_wiitdb(user, password)
            i += 1
            if i > 1:
                time.sleep(2)

    def get_url_editar_juego(self, IDGAME):
        
        if config.DEBUG:
            print "editar_juego"

        if self.connected:
            return "http://%s/Game/%s?action=edit&PHPSESSID=%s" % (self.dominio, IDGAME, self.PHPSESSID)
        else:
            return None

def get_title_for_search(juego):

    # valor inicial
    title = juego.title
    encontrado = False
    
    juego_wiitdb = juego.getJuegoWIITDB()
    if juego_wiitdb is not None:
        i = 0
        while not encontrado and i<len(juego_wiitdb.descripciones):
            descripcion = juego_wiitdb.descripciones[i]
            encontrado = descripcion.lang == config.LANGUAGE_FOR_SEARCH
            i += 1

        if encontrado:
            title = descripcion.title

    title = encode_strange_characters_url(title)

    return title

# FIXME: temporal solution
def get_subinterval_type_disc_art(type_disc_art):
    
    if DISC_CUSTOM == type_disc_art:
        return 16
    else: # elif DISC_ORIGINAL == type_disc_art
        return 0

# FIXME: temporal solution
def get_subinterval_type_cover(type_cover):
    if COVER_3D == type_cover:
        return 16
    elif COVER_FULL == type_cover:
        return 34
    else: # elif COVER_NORMAL == type_cover
        return 0

def remove_multipart_rar(archivoRAR):
    if getExtension(archivoRAR) == 'rar':
        i = 0
        stop = False
        while not stop and i<100: # r00 to r99
            borrar = "%s.r%.2d" % (getNombreFichero(archivoRAR) , i)
            if os.path.exists(borrar):
                os.remove(borrar)
                if config.DEBUG:
                    print "borrar %s" % borrar
            else:
                stop = True
            i += 1
        if os.path.exists(archivoRAR):
            os.remove(archivoRAR)
            if config.DEBUG:
                print "borrar %s" % archivoRAR

def notifyDBUS(titulo, texto, segs):	
    try:
        '''
        bus = SessionBus()
        notifications = bus.get('.Notifications')
        return notifications.Notify('DBus Test', 0, 'dialog-information', titulo, texto, [], {}, segs*1000)
        '''
        # Disabling dbus notifications, problems with pydbus (incompatible gboject vs gobject2)
        pass
    except:
        pass

def getNombreTipoCaratula(tipo_caratula):
    if tipo_caratula == COVER_3D:
        return _("3D cover")
    if tipo_caratula == COVER_FULL:
        return _("Full cover")
    else: # if tipo_caratula == COVER_NORMAL:
        return _("Normal cover")

def getNombreTipoDisco(tipo_disc_art):
    if tipo_disc_art == DISC_CUSTOM:
        return _("Custom disc")
    else: # if tipo_disc_art == DISC_ORIGINAL:
        return _("Original disc")

