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
import config

from sqlalchemy.orm import mapper, relation, sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer, Float, \
    Text, VARCHAR, MetaData, ForeignKey

BDD_PERSISTENTE = create_engine('sqlite:///%s'
                                % os.path.join(
        config.HOME_WIITHON_BDD, 'juegos.db' ))

metadatos = MetaData()

tabla = Table('juegos_wiitdb', metadatos,
    Column('idgame', VARCHAR(6)   ,primary_key=True),
    Column('name'  , VARCHAR(255)),
    Column('region', VARCHAR(255)),
    Column('title_EN', VARCHAR(255)),
    Column('synopsis_EN', VARCHAR(255)),
    Column('title_ES', VARCHAR(255)),
    Column('synopsis_ES', VARCHAR(255)),
    Column('title_PT', VARCHAR(255)),
    Column('synopsis_PT', VARCHAR(255)),
    Column('developer', VARCHAR(255)),
    Column('publisher', VARCHAR(255)),
    Column('anio', Integer),
    Column('mes', Integer),
    Column('dia', Integer),
    Column('wifi_players', Integer),
    Column('input_players', Integer),
)

# solo crea las tablas cuando no existen
metadatos.create_all(BDD_PERSISTENTE)

class Juego(object):
    'class representing a game on the data base'
    def __init__(self , idgame , title , size, device):
        self.idgame = idgame
        self.title = title
        self.size = float(size)
        self.device = device

    def __repr__(self):
        return "%s (%s)  %s" % (self.title, self.idgame, self.device)

mapper(Juego , tabla)
Session = sessionmaker(bind=BDD_PERSISTENTE,
                       autoflush=True, transactional = True)
session = Session()

