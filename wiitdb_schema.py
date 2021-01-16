#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

'''
Documentación: http://www.sqlalchemy.org/docs/05/ormtutorial.html
#define-and-create-a-table
http://www.sqlalchemy.org/trac/wiki/05Migration
'''

import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref, sessionmaker

import config
import util
from util import SintaxisInvalida

###### PARA EVITAR PROBLEMAS DE RECURRENCIA ##########

#from sqlalchemy import pool
#from sqlalchemy.databases.firebird import dialect
#
# Force SA to use a single connection per thread
#dialect.poolclass = pool.SingletonThreadPool

db =        util.getBDD()
session =   util.getSesionBDD(db)

###############################################

Base = declarative_base()

#############################################################################

class Preferencia(Base):
    
    __tablename__ = "preferencias"
    
    id = Column('id',Integer, primary_key=True)
    campo = Column('campo', VARCHAR(255))
    valor = Column('valor', Unicode(3072))
    tipo = Column('tipo', VARCHAR(255))

    def __init__(self, tipo = '', campo = '', valor = ''):
        self.tipo = str(tipo)
        self.campo = str(campo)
        self.valor = str(valor)

    def __repr__(self):
        return "%s(%s) => %s" % (self.campo, self.tipo, self.valor)

try:
    Index('idUnico_preferencia', Preferencia.campo, unique=True)
except:
    Index('idUnico_preferencia', Preferencia.c.campo, unique=True)

class Companie(Base):
    __tablename__ = 'companie'
    
    idCompanie = Column('idCompanie', Integer, primary_key=True)
    code = Column( 'code', VARCHAR(2) )
    name = Column( 'name', VARCHAR(255))

    def __init__(self, code, name):    
        self.code = util.decode(code).strip()
        self.name = util.decode(name).strip()

    def __repr__(self):
        return "%s - %s" % (self.code, self.name)

try:
    Index('idUnico_companie', Companie.code, unique=True)
except:
    Index('idUnico_companie', Companie.c.code, unique=True)

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

try:
    Index('idUnico_rating_value', RatingValue.idRatingType, RatingValue.valor, unique=True)
except:
    Index('idUnico_rating_value', RatingValue.c.idRatingType, RatingValue.c.valor, unique=True)

class RatingContent(Base):
    __tablename__ = 'rating_content'

    idRatingContent = Column("idRatingContent", Integer, primary_key=True)
    idRatingType = Column("idRatingType",Integer , ForeignKey('rating_type.idRatingType'))
    valor = Column('valor', VARCHAR(255))

    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)
        
try:
    Index('idUnico_rating_content', RatingContent.idRatingType, RatingContent.valor, unique=True)
except:
    Index('idUnico_rating_content', RatingContent.c.idRatingType, RatingContent.c.valor, unique=True)

class RatingType(Base):
    __tablename__ = 'rating_type'

    idRatingType = Column('idRatingType', Integer, primary_key=True)
    tipo = Column('tipo', VARCHAR(255))
    
    contenidos = relation(RatingContent)
    valores = relation(RatingValue)

    def __init__(self, tipo):
        self.tipo = util.decode(tipo).strip()

    def __repr__(self):
        return "%s" % (self.tipo)

try:
    Index('idUnico_rating_type', RatingType.tipo, unique=True)
except:
    Index('idUnico_rating_type', RatingType.c.tipo, unique=True)

rel_rating_content_juego = Table("rel_rating_content_juego", Base.metadata, 
    Column("idJuegoWIITDB", Integer, ForeignKey('juego_wiitdb.idJuegoWIITDB')),
    Column("idRatingContent", Integer, ForeignKey('rating_content.idRatingContent'))
    )

class OnlineFeatures(Base):
    __tablename__ = 'online_features'
    
    idFeature = Column('idFeature', Integer , primary_key=True)
    valor = Column('valor', VARCHAR(255))
    
    def __init__(self, valor):
        self.valor = util.decode(valor).strip()

    def __repr__(self):
        return "%s" % (self.valor)

try:    
    Index('idUnico_online_features', OnlineFeatures.valor, unique=True)
except:
    Index('idUnico_online_features', OnlineFeatures.c.valor, unique=True)

rel_online_features_juego = Table("rel_online_features_juego", Base.metadata, 
    Column("idJuegoWIITDB", Integer, ForeignKey('juego_wiitdb.idJuegoWIITDB')),
    Column("idFeature", Integer, ForeignKey('online_features.idFeature'))
    )
    

class JuegoDescripcion(Base):
    __tablename__ = 'juego_descripcion'
    
    idDescripcion = Column('idDescripcion', Integer , primary_key=True)
    idJuegoWIITDB = Column('idJuegoWIITDB', Integer , ForeignKey('juego_wiitdb.idJuegoWIITDB'))
    lang = Column('lang', VARCHAR(2))
    title = Column('title', Unicode(255))
    synopsis = Column('synopsis', Unicode(5000), nullable = False)
    
    def __init__(self, lang='', title='', synopsis=''):
        self.lang = lang
        self.title = util.decode(title)
        self.synopsis = util.decode(synopsis)
        
    def __repr__(self):
        return "%s (%s)" % (self.title, self.lang)
        
    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

try:
    Index('idUnico_juego_descripcion', JuegoDescripcion.idJuegoWIITDB, JuegoDescripcion.lang, unique=True)
except:
    Index('idUnico_juego_descripcion', JuegoDescripcion.c.idJuegoWIITDB, JuegoDescripcion.c.lang, unique=True)

class Rom(Base):
    __tablename__ = 'rom'

    idRom = Column('idRom', Integer , primary_key=True)
    idJuegoWIITDB = Column('idJuegoWIITDB', Integer , ForeignKey('juego_wiitdb.idJuegoWIITDB'))
    version = Column('version', VARCHAR(255))
    name = Column('name', VARCHAR(255))
    size = Column('size', Integer)
    crc = Column('crc', VARCHAR(8))
    md5 = Column('md5', VARCHAR(32))
    sha1 = Column('sha1', VARCHAR(40))

    def __init__(self, version, name, size, crc, md5, sha1):
        self.version = util.decode(version)
        self.name = util.decode(name)
        try:
            self.size = int(size)
        except ValueError:
            self.size = 0
        self.crc = util.decode(crc)
        self.md5 = util.decode(md5)
        self.sha1 = util.decode(sha1)

    def __repr__(self):
        return "Ver. %s - %s (%.2f GB)" % (self.version, self.name, self.size/1024.0/1024.0)

class Genero(Base):
    __tablename__ = 'genero'
    
    idGenero = Column('idGenero', Integer, primary_key=True)
    nombre = Column('nombre', Unicode(255))
    
    def __init__(self,  nombre):
        self.nombre = util.decode(nombre).strip()
        
    def __repr__(self):
        return "%s" % (self.nombre)

try:
    Index('idUnico_genero', Genero.nombre, unique=True)
except:
    Index('idUnico_genero', Genero.c.nombre, unique=True)
        
rel_juego_genero = Table("rel_juego_genero", Base.metadata, 
    Column("idJuegoWIITDB", Integer, ForeignKey('juego_wiitdb.idJuegoWIITDB')),
    Column("idGenero", Integer, ForeignKey('genero.idGenero'))
    )

class Accesorio(Base):
    __tablename__ = 'accesorio'
    
    idAccesorio = Column('idAccesorio', Integer, primary_key=True)
    nombre = Column('nombre', Unicode(255))
    descripcion = Column('descripcion', Unicode(512))

    def __init__(self,  nombre, descripcion = ''):
        self.nombre = util.decode(nombre).strip()
        self.descripcion = util.decode(descripcion).strip()

    def __repr__(self):
        return "%s %s" % (self.nombre, self.descripcion)

try:        
    Index('idUnico_accesorio', Accesorio.nombre, unique=True)
except:
    Index('idUnico_accesorio', Accesorio.c.nombre, unique=True)

rel_accesorio_juego_obligatorio = Table("rel_accesorio_juego_obligatorio", Base.metadata, 
    Column("idJuegoWIITDB", Integer, ForeignKey('juego_wiitdb.idJuegoWIITDB')),
    Column("idAccesorio", Integer, ForeignKey('accesorio.idAccesorio'))
    )
    
rel_accesorio_juego_opcional = Table("rel_accesorio_juego_opcional", Base.metadata, 
    Column("idJuegoWIITDB", Integer, ForeignKey('juego_wiitdb.idJuegoWIITDB')),
    Column("idAccesorio", Integer, ForeignKey('accesorio.idAccesorio'))
    )

class JuegoWIITDB(Base):
    __tablename__ = 'juego_wiitdb'

    # campos
    idJuegoWIITDB = Column('idJuegoWIITDB', Integer, primary_key=True)
    idgame = Column('idgame', VARCHAR(6))
    name = Column('name'  , Unicode(255))
    region = Column('region', Unicode(40))
    developer = Column('developer', Unicode(100))
    publisher = Column('publisher', Unicode(100))
    fecha_lanzamiento = Column('fecha_lanzamiento', Date, nullable=True)
    wifi_players = Column('wifi_players', Integer)
    input_players = Column('input_players', Integer)

    #   1:1
    rating_type = relation(RatingType)
    rating_value = relation(RatingValue)
    idRatingType = Column('idRatingType',   Integer , ForeignKey('rating_type.idRatingType'), nullable=True)
    idRatingValue = Column("idRatingValue", Integer , ForeignKey('rating_value.idRatingValue'), nullable=True)
    
    #   1:N
    descripciones = relation(JuegoDescripcion)
    roms = relation(Rom)
    
    #   N:M
    rating_contents = relation(RatingContent, secondary=rel_rating_content_juego)
    features = relation(OnlineFeatures, secondary=rel_online_features_juego)
    obligatorio = relation(Accesorio, secondary=rel_accesorio_juego_obligatorio)
    opcional = relation(Accesorio, secondary=rel_accesorio_juego_opcional)
    genero = relation(Genero, secondary=rel_juego_genero, backref='juego_wiitdb')

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
        
    def getTextPlayersWifi(self, corto = False):
        buffer = ""
        if self.wifi_players == 0:
            if corto:
                buffer = _("NO")
            else:
                buffer = _("No")
        else:
            if not corto:
                for feature_online in self.features:
                    buffer += "%s, " % feature_online.valor
		buffer = util.remove_last_separator(buffer)
            if self.wifi_players == 1:
                if corto:
                    buffer = _("SI, 1j.")
                else:
                    buffer = _("Si, 1 jugador (%s)") % buffer
            else:
                if corto:
                    buffer = _("SI, %djs.") % (self.wifi_players)
                else:
                    buffer = _("Si, %d jugadores (%s)") % (self.wifi_players, buffer)
        return buffer
        
    def getTextPlayersLocal(self, corto = False):
        buffer = ""
        if self.input_players == 1:
            if corto:
                buffer = _("1j.")
            else:
                buffer = _("1 jugador")
        else:
            if corto:
                buffer = _("%djs.") %  self.input_players
            else:
                buffer = _("%d jugadores") %  self.input_players
        return buffer

    def getTextFechaLanzamiento(self, core, corto = False):
        buffer = ""
        if  self.fecha_lanzamiento is not None:
            if corto:
                buffer = "%s" % ( self.fecha_lanzamiento.strftime(core.prefs.FORMATO_FECHA_CORTA_WIITDB) )
            else:
                buffer = "%s" % ( self.fecha_lanzamiento.strftime(core.prefs.FORMATO_FECHA_WIITDB) )
        else:
            buffer = core.prefs.FORMATO_FECHA_DESCONOCIDA
        return buffer

    def getTextRating(self, corto = False):
        buffer = ""
        if self.rating_type is None or self.rating_value is None:
            return ""
        else:
            if not corto:
                for rating_content in self.rating_contents:
                    buffer += "%s, " % rating_content.valor
                buffer = "%s (%s+): %s" % ( self.rating_type.tipo,  self.rating_value.valor , buffer)
            else:
                buffer = "%s (%s+)" % ( self.rating_type.tipo,  self.rating_value.valor)
            return util.remove_last_separator(buffer)

try:
    Index('idUnico_juego_wiitdb', JuegoWIITDB.idgame, unique=True)
except:
    Index('idUnico_juego_wiitdb', JuegoWIITDB.c.idgame, unique=True)

class Juego(Base):
    __tablename__ = 'juego'

    idJuego = Column('idJuego', Integer, primary_key=True)
    idgame = Column('idgame', VARCHAR(6))
    title = Column('title', Unicode(255))
    size = Column('size', Float)
    idParticion = Column("idParticion", Integer , ForeignKey('particion.idParticion'), nullable=False)

    def __init__(self , idgame , title , size):
        self.idgame = util.decode(idgame)
        self.title = util.decode(title)
        self.size = float(size)

    def __init__(self, cachos):
        if(len(cachos)==3):
            self.idgame = util.decode(cachos[0])
            self.title = util.decode(cachos[1])
            self.size = float(cachos[2])
        else:
            raise SintaxisInvalida
            
    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

    def __repr__(self):
        return "%s (ID: %s) %.2f GB (%s)" % (self.title, self.idgame, self.size, self.particion.device)
        
    def getJuegoWIITDB(self):
        sql = util.decode("juego_wiitdb.idgame=='%s'" % (self.idgame))
        return session.query(JuegoWIITDB).filter(util.sql_text(sql)).first()


class Particion(Base):
    __tablename__ = 'particion'

    idParticion = Column('idParticion', Integer, primary_key=True)
    device = Column('device', VARCHAR(10))
    tipo = Column('tipo', VARCHAR(5))
    usado = Column('usado', Float)
    libre = Column('libre', Float)
    total = Column('total', Float)
    fabricante = Column('fabricante', Unicode(255))
    
    juegos = relation(Juego, backref='particion')
    
    def __init__(self, cachos):
        if(len(cachos)==6+1):
            # nombre lógico unix (/dev/sda1)
            self.device = util.decode(cachos[0])
            
            # tipo de particion "fat32|wbfs|dvd"
            self.tipo = util.decode(cachos[1])
            
            # Espacio en GB usados de la partición
            self.usado = float(cachos[2].replace(",",".").replace("G",""))
            
            # Espacio en GB libres de la partición
            self.libre = float(cachos[3].replace(",",".").replace("G",""))
            
            # Espacio en GB total de la partición
            self.total = float(cachos[4].replace(",",".").replace("G",""))
            
            # Nombre del fabricante, requiere udevinfo
            self.fabricante = util.decode(cachos[5])
        else:
            raise SintaxisInvalida

    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = util.decode(value)
        object.__setattr__(self, name, value)

    def __repr__(self):
        return "%s %s (%.0f GB)" % (self.device, self.fabricante, self.total)
        
    def getColorForeground(self, core):
        
        numColores = 3

        if (((self.idParticion - 1) % numColores) == 0):
            return core.prefs.COLOR_FOREGROUND1
        elif (((self.idParticion - 1) % numColores) == 1):
            return core.prefs.COLOR_FOREGROUND2
        else:#if (((self.idParticion - 1) % numColores) == 2):
            return core.prefs.COLOR_FOREGROUND3

    def getColorBackground(self, core):

        numColores = 3

        if (((self.idParticion - 1) % numColores) == 0):
            return core.prefs.COLOR_BACKGROUND1
        elif (((self.idParticion - 1) % numColores) == 1):
            return core.prefs.COLOR_BACKGROUND2
        else:#if (((self.idParticion - 1) % numColores) == 2):
            return core.prefs.COLOR_BACKGROUND3
            
    def refrescarEspacioLibreUsado(self, core):
        cachos = core.getEspacioLibreUsado(self)
        self.usado = float(cachos[0])
        self.libre = float(cachos[1])
        self.total = float(cachos[2])
        session.commit()

try:
    Index('idUnico_particion', Particion.device, unique=True)
except:
    Index('idUnico_particion', Particion.c.device, unique=True)

#############################################################################

util.crearBDD(Base.metadata)
