#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import config
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Text, VARCHAR, MetaData, ForeignKey

motor = create_engine('sqlite:///%s' % os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' ))
metadatos = MetaData()

tablaCaratula = Table('caratulas',metadatos,
	# claves primarias y foraneas
	Column('id',Integer,primary_key=True),
	Column('idJuego',Integer),#, ForeignKey('juegos.id')), # clave foranea de "juegos"
	# campos
	Column('tipo',VARCHAR(255)), # Tipos : normal160x225, disco160x160
	Column('fichero',VARCHAR(255)), # Nombre del fichero PNG, de momento no hace falta otra tabla "tipos de imagen"
)

# solo crea las tablas cuando no existen
metadatos.create_all(motor)

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

