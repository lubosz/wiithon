#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import almacen
from almacen import tablaJuego , motor
from sqlalchemy.orm import mapper , relation , sessionmaker
from caratula import Caratula

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

