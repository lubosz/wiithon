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
from gettext import gettext as _

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

import config

# Caracteres que hacen que una expresión no pueda ser expresión regular
BLACK_LIST = "/\"\'$&|[]"
BLACK_LIST2 = "\";`$\\\'"

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

def getNombreFichero(fichero):
    posPunto = fichero.rfind(".")
    if posPunto != -1:
        return fichero[0:posPunto]
    else:
        return fichero

def getMagicISO(imagenISO):
    f = open(imagenISO , "r")
    magic = f.read(6)
    f.close()
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

'''
def getUltimaLinea(fichero):
    f = open( fichero , "r")
    ultimaLinea = ""
    for linea in file.readlines():
        ultimaLinea = linea
    f.close()
    return ultimaLinea
'''

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

        __clipboard = gtk.Clipboard() # This is a singleton

        def __init__(self, clear=False, copy=False):
            sexy.IconEntry.__init__(self)
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
    
def descargar(url, destino):
    try:
        mysock = urllib.urlopen(url)
        oFile = open(destino ,'wb')
        oFile.write(mysock.read())
        oFile.close()
    except:
        raise ErrorDescargando

def descargarImagen(url, destino, type = "image/png", referer = "http://www.wiiboxart.com/pal.php"):
    try:
        dominio, ruta_imagen = getDominioYRuta(url)
        
        conn = httplib.HTTPConnection(dominio)

        params = None
        headers =   {
                        "Host": dominio,
                        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.11) Gecko/2009060310 Ubuntu/8.10 (intrepid) Firefox/3.0.11",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "es-es,es;q=0.8,en-us;q=0.5,en;q=0.3",
                        "Accept-Encoding": "gzip,deflate",
                        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                        #"Keep-Alive": "300",
                        #"Connection": "keep-alive",
                        "Referer": referer
                    }
        
        conn.request ("GET", '/%s' % (ruta_imagen), params, headers)
        
        r = conn.getresponse()
        
        i = 0
        encontrado = False
        headers = r.getheaders()
        while (not encontrado) and (i<len(headers)):
            if headers[i][0] == "content-type":
                encontrado = (headers[i][1] == type)
            if not encontrado:
                i = i + 1
        
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

def decode(s, code = 'utf-8'):
    try:
        return s.decode(code)
    except UnicodeDecodeError:
        return s

class NoDeberiaPasar(Exception):
    pass

# lanzado por particion
class SintaxisInvalida(Exception):
    pass

def getBDD():
    db = create_engine(config.URI_ENGINE)
    return db

def crearBDD(metadatos):
    db = getBDD()
    metadatos.create_all(db)
    
def borrarBDD(metadatos):
    db = getBDD()
    metadatos.drop_all(db)    

def getSesionBDD(db):
    # con scoped se resuelven todos los problemas de concurrencia!
    Session = scoped_session(sessionmaker(bind=db, autoflush=True, transactional=True))
    session = Session()
    return session

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
    texto = texto.replace("\"" , "&quot;")
    return texto

def setLanguage(locale = 'default'):
        
    if locale == 'default':
        gettext.install(config.APP,config.LOCALE, unicode=1)
    else:
        lang = gettext.translation(config.APP, languages=[locale])
        lang.install()

def configurarLenguaje():

    locale.setlocale(locale.LC_ALL, '')

    for module in (gettext, gtk.glade):
        module.bindtextdomain(config.APP,config.LOCALE)
        module.textdomain(config.APP)
        
    setLanguage('default')

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
    return (getExtension(fichero)=="png") or (getExtension(fichero)=="jpg") or (getExtension(fichero)=="gif")

## check user group and permissions
def check_permissions(partition):
	file=open("/etc/group","r")
	for line in file:
       		if "disk:x:" in line:
                	group=line.rsplit(":");
                	break;
	file.close;

	if (int(group[2]) in os.getgroups()):
        	print "User %s is in disk group" % os.getlogin()
	else:
        	print "User %s is NOT in disk group" % os.getlogin();

	if (os.access(partition,os.W_OK)):
        	print "user can write on partition %s" % partition;
