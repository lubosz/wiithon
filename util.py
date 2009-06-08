#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import fnmatch
import fnmatch
import subprocess
import gtk

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

'''
class Observable:
    def __init__(self, topic_list):
        self.__observers = {}

        for topic in topic_list:
            self.__observers[topic] = []


    def subscribe(self, topic, callback):
        if isinstance(topic, list):
            for t in topic:
                if self.__observers.has_key(t):
                    self.__observers[t].append(callback)

                else:
                    raise SubscriptionError(t)

        else:
            if self.__observers.has_key(topic):
                self.__observers[topic].append(callback)

            else:
                raise SubscriptionError(topic)

    def notify(self, topic, what):
        if self.__observers.has_key(topic):
            for observer_cb in self.__observers[topic]:
                observer_cb(topic, what)

        else:
            print 'El topic no existe, reporta el bug'


class SubscriptionError(Exception):
    def __init__(self, topic=None):
        Exception.__init__(self)
        if topic:
            self.msg = 'The topic "%s" doesn\'t exist' %(topic)

        else:
            self.msg = 'Topic not exist'

    def __str__(self):
        return self.msg
'''

def getExtension(fichero):
	#fichero = eliminarComillas(fichero)
	posPunto = fichero.rfind(".")
	return fichero[posPunto+1:len(fichero)].lower()

def getNombreFichero(fichero):
	#fichero = eliminarComillas(fichero)
	posPunto = fichero.rfind(".")
	return fichero[0:posPunto]

def getMagicISO(imagenISO):
	f = open(imagenISO , "r")
	magic = f.read(6)
	f.close()
	if len(magic) == 6:
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

def getSTDOUT(comando , mostrarError = True):
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

def getUltimaLinea(fichero):
	f = open( fichero , "r")
	ultimaLinea = ""
	for linea in file.readlines():
		ultimaLinea = linea
	return ultimaLinea

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
#try:
#    import sexy
#    class Entry(sexy.IconEntry):
#
#        __clipboard = gtk.Clipboard() # This is a singleton
#
#        def __init__(self, clear=False, copy=False):
#            sexy.IconEntry.__init__(self)
#            if clear:
#                self.add_clear_button()
#
#            if copy:
#                icon = gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
#                self.connect("icon_released", self.on_copy_clicked)
#
#                self.set_icon(sexy.ICON_ENTRY_SECONDARY, icon)
#                self.set_icon_highlight(sexy.ICON_ENTRY_SECONDARY, True)
#
#        def on_copy_clicked(self, widget, icon_pos, button):
#            if icon_pos != sexy.ICON_ENTRY_SECONDARY or button != 1:
#		return True
#
#            self.__clipboard.set_text(str(self.get_text()))
#
#
#except ImportError:
#    logging.warning("There is no python-sexy available. fallback to standard gtk.")
#    class Entry(gtk.Entry):
#        def __init__(self, clear=False, copy=False):
#            gtk.Entry.__init__(self)
#
#
