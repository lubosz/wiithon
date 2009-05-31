#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import config

'''
FIXME: hacerlo con enumerados (o el equivalente python)
'''
class Mensaje:
	def __init__(self , tipo , mensaje):
	        if not (tipo in config.TOPICS):
	        	raise AssertionError, "Tipo de Mensaje desconocido"
		self.tipo = tipo
		self.mensaje = mensaje
	
	def getTipo(self):
		return self.tipo
		
	def getMensaje(self):
		return self.mensaje

