#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from almacen import tablaCaratula , motor
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker

class Caratula(object):
	def __init__(self , idJuego , tipo , fichero):
		self.idJuego = idJuego
		self.tipo = tipo
		self.fichero = fichero
		
	def __repr__(self):
		return "%s" % (self.fichero)

mapper(Caratula , tablaCaratula)
Session = sessionmaker(bind=motor , autoflush=True, transactional = True)
session = Session()

