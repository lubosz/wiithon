#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os

from sqlalchemy.orm import mapper, relation, sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer, Text, \
    VARCHAR, MetaData, ForeignKey

import config

motor = create_engine('sqlite:///%s' % os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' ))
metadatos = MetaData()

tabla = Table('preferencias',metadatos,
    # claves primarias y foraneas
    Column('id',Integer,primary_key=True),
    # campos
    Column('ruta_anadir', VARCHAR(255)),
    Column('ruta_anadir_directorio', VARCHAR(255)),
    Column('ruta_extraer_iso', VARCHAR(255)),
    Column('ruta_copiar_caratulas', VARCHAR(255)),
    Column('ruta_copiar_discos', VARCHAR(255)),
    Column('device_seleccionado', VARCHAR(12)),
    Column('idgame_seleccionado', VARCHAR(6)),
)

# solo crea las tablas cuando no existen
metadatos.create_all(motor)

class Preferencia(object):

    def __init__(self):
        self.ruta_anadir = config.HOME
        self.ruta_anadir_directorio = config.HOME
        self.ruta_extraer_iso = config.HOME
        self.ruta_copiar_caratulas = config.HOME
        self.ruta_copiar_discos = config.HOME
        self.device_seleccionado = None
        self.idgame_seleccionado = None

    def __repr__(self):
        retorno = "ruta_anadir = %s\nruta_anadir_directorio = %s\nruta_extraer = %s\nruta_copiar_caratulas = %s\nruta_copiar_discos = %s\ndevice seleccionado = %s\nidgame seleccionado = %s\n" % (
                    self.ruta_anadir ,
                    self.ruta_anadir_directorio ,
                    self.ruta_extraer_iso ,
                    self.ruta_copiar_caratulas ,
                    self.ruta_copiar_discos ,
                    self.device_seleccionado ,
                    self.idgame_seleccionado )
        return retorno

mapper(Preferencia , tabla)
Session = sessionmaker(bind=motor , autoflush=True, transactional = True)
session = Session()

