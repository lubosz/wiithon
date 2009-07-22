#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

'''
Documentación: http://www.sqlalchemy.org/docs/05/ormtutorial.html
#define-and-create-a-table
Ojo, mi ubuntu va con SQLAlchemy 0.4 pero el último es 0.5x
Aquí un wiki con las diferencias:
http://www.sqlalchemy.org/trac/wiki/05Migration
'''

import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref, sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy

import config
import util

Base = declarative_base()

#############################################################################

class Companie(Base):
    __tablename__ = 'wiitdb_companies'
    
    code = Column('code',VARCHAR(2), primary_key=True)
    name = Column('name', VARCHAR(255))

    def __init__(self, code, name):
        self.code = util.decode(code).strip()
        self.name = util.decode(name).strip()

    def __repr__(self):
        return "%s - %s" % (self.code, self.name)

## EMPIEZA RATING

class RatingValue(Base):
    __tablename__ = 'rating_value'
    
    idRatingValue = Column("idRatingContent", Integer, primary_key=True)
    idRatingType = Column("idRatingType", Integer , ForeignKey('rating_type.idRatingType'))
    valor = Column('valor', VARCHAR(255))

class RatingContent(Base):
    __tablename__ = 'rating_content'

    idRatingContent = Column("idRatingContent", Integer, primary_key=True)
    idRatingType = Column("idRatingType",Integer , ForeignKey('rating_type.idRatingType'))
    valor = Column('valor', VARCHAR(255))

    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)

class RatingType(Base):
    __tablename__ = 'rating_type'

    idRatingType = Column('idRatingType',   Integer, primary_key=True)
    tipo = Column('tipo', VARCHAR(255))
    
    contenidos = relation(RatingContent)
    valores = relation(RatingValue)

    def __init__(self, tipo):
        self.tipo = util.decode(tipo).strip()

    def __repr__(self):
        return "%s" % (self.tipo)

## TERMINA RATING
##############################################################################

rel_rating_juego = Table("rel_rating_type_juego", Base.metadata, 
    Column("idRatingType", VARCHAR(255), ForeignKey('rating_type.idRatingType'),primary_key=True),
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame'), primary_key=True)
    )

##############################################################################

class JuegoDescripcion(Base):
    __tablename__ = 'wiitdb_juego_descripcion'
    
    idDescripcion = Column('idDescripcion', Integer , primary_key=True)
    idgame = Column('idgame', VARCHAR(6) , ForeignKey('wiitdb_juegos.idgame'))
    lang = Column('lang', VARCHAR(2))
    title = Column('title', Unicode(255))
    synopsis = Column('synopsis', Unicode(255))
    
    def __init__(self, lang, title, synopsis):
        self.lang = lang
        self.title = util.decode(title)
        self.synopsis = util.decode(synopsis)
        
    def __repr__(self):
        return "%s - %s (%s): %s" % (self.idgame, self.title, self.lang, self.synopsis)
        
    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

class JuegoWIITDB(Base):
    __tablename__ = 'wiitdb_juegos'

    idJuegoWIITDB = Column('idJuegoWIITDB', Integer , primary_key=True)
    idgame = Column('idgame', VARCHAR(6), unique=True)
    name = Column('name'  , Unicode(255))
    region = Column('region', Unicode(255))
    developer = Column('developer', Unicode(255))
    publisher = Column('publisher', Unicode(255))
    anio = Column('anio', Integer)
    mes = Column('mes', Integer)
    dia = Column('dia', Integer)
    wifi_players = Column('wifi_players', Integer)
    input_players = Column('input_players', Integer)
    
    descripciones = relation(JuegoDescripcion)
    rating = relation(RatingType, secondary=rel_rating_juego)

    def __init__(self , idgame , name , region='', developer='', publisher='', anio='', mes='', dia='', wifi_players='', input_players=''):
        self.idgame = util.decode(idgame)
        self.name = util.decode(name)
        self.region = util.decode(region)
        self.developer = util.decode(developer)
        self.publisher = util.decode(publisher)
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.wifi_players = wifi_players
        self.input_players = input_players

    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

    def __repr__(self):
        return "%s - %s (%s)" % (self.idgame, self.name, self.region)

#############################################################################

rel_accesorio_juego_obligatorio = Table("rel_accesorio_juego_obligatorio", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame'), primary_key=True),
    Column("nombre", Unicode(255), ForeignKey('accesorio.nombre'),primary_key=True)
    )
    
rel_accesorio_juego_opcional = Table("rel_accesorio_juego_opcional", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame'), primary_key=True),
    Column("nombre", Unicode(255), ForeignKey('accesorio.nombre'),primary_key=True)
    )

#############################################################################

class Accesorio(Base):
    __tablename__ = 'accesorio'

    nombre = Column('nombre', Unicode(255), primary_key=True)
    descripcion = Column('descripcion', Unicode(255))
    
    obligatorio = relation(JuegoWIITDB, secondary=rel_accesorio_juego_obligatorio)
    opcional = relation(JuegoWIITDB, secondary=rel_accesorio_juego_opcional)

    def __init__(self,  nombre, descripcion = ''):
        self.nombre = util.decode(nombre).strip()
        self.descripcion = util.decode(descripcion).strip()

    def __repr__(self):
        return "%s %s" % (self.nombre, self.descripcion)

#############################################################################

util.crearBDD(Base.metadata)

#############################################################################
