#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import config
from sqlalchemy.orm import mapper , relation , sessionmaker
from caratula import Caratula
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Text, VARCHAR, MetaData, ForeignKey

motor = create_engine('sqlite:///%s' % os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' ))
metadatos = MetaData()

tablaJuego = Table('juegos',metadatos,
	# claves primarias y foraneas
	Column('id',Integer,primary_key=True),
	# campos
	Column('idgame',VARCHAR(6)),
	Column('titulo', VARCHAR(50)),
	Column('year',Integer),
	Column('quarter',Integer), # 1=principios de año, 2, 3, 4 = finales de año
	Column('puntuacion',Integer), # del 0 al 5
)

# solo crea las tablas cuando no existen
metadatos.create_all(motor)

class Juego(object):

	caratula = None

	def __init__(self , idgame , titulo , year , quarter , puntuacion):
		self.idgame = idgame
		self.titulo = titulo
		self.year = year
		self.quarter = quarter
		self.puntuacion = puntuacion
		
	def __repr__(self):
		return "%d -> %s - %s del %d" % (self.id , self.idgame, self.titulo , self.year)
		
	def tieneCaratula(self):
		return self.caratula != None
		
	def crearCaratula(self):
		self.caratula = Caratula(self.id , "normal160x225" , self.idgame+".png")
		session.save(self.caratula)

	def borrarCaratula(self):
		# SQL LITE no soporta -> ondelete = CASCADE
		pass
		#if self.tieneCaratula:
			#session.delete( session.query(Caratula).filter( "idJuego==:idJuego" ).params(idJuego=self.id).first() )

	def harakiri(self):
		session.delete( session.query(Juego).filter( "idgame==:idgame" ).params(idgame=self.idgame).first() )

#mapper(Juego , tablaJuego , properties={'caratulas': relation(Caratula)} , order_by=tablaJuego.c.titulo)
mapper(Juego , tablaJuego)
Session = sessionmaker(bind=motor , autoflush=True, transactional = True)
session = Session()

'''
sudo apt-get install python-sqlalchemy

Documentación: http://www.sqlalchemy.org/docs/05/ormtutorial.html#define-and-create-a-table
Ojo, mi ubuntu va con SQLAlchemy 0.4 pero el último es 0.5x
Aquí un wiki con las diferencias:
http://www.sqlalchemy.org/trac/wiki/05Migration
'''

