#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import subprocess
import gtk

# Caracteres que hacen que una expresión no pueda ser expresión regular
BLACK_LIST = "/\"\'$&|[]"

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
	return magic

def tieneCaracteresRaros(cadena):
	# Nos dice si *cadena* tiene caracteres raros dados por una lista negra global
	for i in range(len(cadena)):
		for j in range(len(BLACK_LIST)):
			if (cadena[i]==BLACK_LIST[j]):
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

def getSTDOUT(comando):
	out = getSTDOUT_iterador(comando)
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
