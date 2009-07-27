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

###### PARA AUMENTAR LA RECURRENCIA ##########

from sqlalchemy import pool
from sqlalchemy.databases.firebird import dialect

# Force SA to use a single connection per thread
dialect.poolclass = pool.SingletonThreadPool
  
###############################################

Base = declarative_base()

#############################################################################

class Companie(Base):
    __tablename__ = 'wiitdb_companies'
    
    idCompanie = Column('idCompanie', Integer, primary_key=True)
    code = Column('code',VARCHAR(2))
    name = Column('name', VARCHAR(255))

    def __init__(self, code, name):    
        self.code = util.decode(code).strip()
        self.name = util.decode(name).strip()

    def __repr__(self):
        return "%s - %s" % (self.code, self.name)

Index('idUnico_wiitdb_companies', Companie.code, Companie.name, unique=True)

## EMPIEZA RATING

class RatingValue(Base):
    __tablename__ = 'rating_value'
    
    idRatingValue = Column("idRatingValue", Integer, primary_key=True)
    idRatingType = Column("idRatingType", Integer , ForeignKey('rating_type.idRatingType'))
    valor = Column('valor', VARCHAR(255))
    
    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)

Index('idUnico_rating_value', RatingValue.idRatingType, RatingValue.valor, unique=True)

class RatingContent(Base):
    __tablename__ = 'rating_content'

    idRatingContent = Column("idRatingContent", Integer, primary_key=True)
    idRatingType = Column("idRatingType",Integer , ForeignKey('rating_type.idRatingType'))
    valor = Column('valor', VARCHAR(255))

    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)
        
Index('idUnico_rating_content', RatingContent.idRatingType, RatingContent.valor, unique=True)

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
        
Index('idUnico_rating_type', RatingType.tipo, unique=True)

rel_rating_content_juego = Table("rel_rating_content_juego", Base.metadata, 
    Column("idRatingContent", Integer, ForeignKey('rating_content.idRatingContent')),
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame'))
    )

class OnlineFeatures(Base):
    __tablename__ = 'online_features'
    
    idFeature = Column('idFeature', Integer , primary_key=True)
    valor = Column('valor', VARCHAR(255))
    
    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)
    
Index('idUnico_online_features', OnlineFeatures.valor, unique=True)

rel_online_features_juego = Table("rel_online_features_juego", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame')),
    Column("idFeature", Integer, ForeignKey('online_features.idFeature'))
    )
    

class JuegoDescripcion(Base):
    __tablename__ = 'wiitdb_juego_descripcion'
    
    idDescripcion = Column('idDescripcion', Integer , primary_key=True)
    idgame = Column('idgame', VARCHAR(6) , ForeignKey('wiitdb_juegos.idgame'))
    lang = Column('lang', VARCHAR(2))
    title = Column('title', Unicode(255))
    synopsis = Column('synopsis', Unicode(255))
    
    def __init__(self, lang='', title='', synopsis=''):
        self.lang = lang
        self.title = util.decode(title)
        self.synopsis = util.decode(synopsis)
        
    def __repr__(self):
        return "%s - %s (%s): %s" % (self.idgame, self.title, self.lang, self.synopsis)
        
    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

Index('idUnico_wiitdb_juego_descripcion', JuegoDescripcion.idgame, JuegoDescripcion.lang, unique=True)

class Rom(Base):
    __tablename__ = 'roms'

    idRom = Column('idRom', Integer , primary_key=True)
    version = Column('version', VARCHAR(255))
    name = Column('name', VARCHAR(255))
    size = Column('size', Integer)
    crc = Column('crc', VARCHAR(8))
    md5 = Column('md5', VARCHAR(32))
    sha1 = Column('sha1', VARCHAR(40))

    def __init__(self, version, name, size, crc, md5, sha1):
        self.version = util.decode(version)
        self.name = util.decode(name)
        self.size = int(size)
        self.crc = util.decode(crc)
        self.md5 = util.decode(md5)
        self.sha1 = util.decode(sha1)

    def __repr__(self):
        return "Ver. %s - %s (%.2f GB)" % (self.version, self.name, self.size/1024.0/1024.0)
        
#Index('idUnico_roms', Rom.version, Rom.name, unique=True)

class Genero(Base):
    __tablename__ = 'genero'
    
    idGenero = Column('idGenero', Integer, primary_key=True)
    nombre = Column('nombre', Unicode(255))
    
    def __init__(self,  nombre):
        self.nombre = util.decode(nombre).strip()
        
    def __repr__(self):
        return "%s" % (self.nombre)

Index('idUnico_genero', Genero.nombre, unique=True)
        
rel_juego_genero = Table("rel_juego_genero", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame')),
    Column("idGenero", Integer, ForeignKey('genero.idGenero'))
    )

class Accesorio(Base):
    __tablename__ = 'accesorio'

    nombre = Column('nombre', Unicode(255), primary_key=True)
    descripcion = Column('descripcion', Unicode(6000))

    def __init__(self,  nombre, descripcion = ''):
        self.nombre = util.decode(nombre).strip()
        self.descripcion = util.decode(descripcion).strip()

    def __repr__(self):
        return "%s %s" % (self.nombre, self.descripcion)
        
Index('idUnico_accesorio', Accesorio.nombre, unique=True)

rel_accesorio_juego_obligatorio = Table("rel_accesorio_juego_obligatorio", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame')),
    Column("nombre", Unicode(255), ForeignKey('accesorio.nombre'))
    )
    
rel_accesorio_juego_opcional = Table("rel_accesorio_juego_opcional", Base.metadata, 
    Column("idgame", VARCHAR(6), ForeignKey('wiitdb_juegos.idgame')),
    Column("nombre", Unicode(255), ForeignKey('accesorio.nombre'))
    )

class JuegoWIITDB(Base):
    __tablename__ = 'wiitdb_juegos'

    # campos
    idgame = Column('idgame', VARCHAR(6), primary_key=True)
    name = Column('name'  , Unicode(255))
    region = Column('region', Unicode(255))
    developer = Column('developer', Unicode(255))
    publisher = Column('publisher', Unicode(255))
    fecha_lanzamiento = Column('fecha_lanzamiento', Date, nullable=True)
    wifi_players = Column('wifi_players', Integer)
    input_players = Column('input_players', Integer)
    idRatingType = Column('idRatingType',   Integer , ForeignKey('rating_type.idRatingType'), nullable=True)
    idRatingValue = Column("idRatingValue", Integer , ForeignKey('rating_value.idRatingValue'), nullable=True)
    idRom = Column("idRom", Integer , ForeignKey('roms.idRom'), nullable=True)
    
    # indices
    # ??

    # relaciones
    #   1:1
    rating_type = relation(RatingType)
    rating_value = relation(RatingValue)
    rom = relation(Rom)    
    
    #   1:N
    descripciones = relation(JuegoDescripcion)
    
    #   N:M
    rating_contents = relation(RatingContent, secondary=rel_rating_content_juego)
    features = relation(OnlineFeatures, secondary=rel_online_features_juego)
    obligatorio = relation(Accesorio, secondary=rel_accesorio_juego_obligatorio)
    opcional = relation(Accesorio, secondary=rel_accesorio_juego_opcional)
    genero = relation(Genero, secondary=rel_juego_genero)

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
        return "%s - %s" % (self.idgame, self.name)

Index('idUnico_wiitdb_juegos', JuegoWIITDB.idgame, unique=True)
        
#############################################################################

util.crearBDD(Base.metadata)
