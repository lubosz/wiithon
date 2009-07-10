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
import util

from sqlalchemy.orm import mapper, relation, sessionmaker, backref
from sqlalchemy import create_engine, Table, Column, Integer, Float, \
    Text, VARCHAR, MetaData, ForeignKey, Unicode

BDD_PERSISTENTE = create_engine('sqlite:///%s'
                                % os.path.join(
        config.HOME_WIITHON_BDD, 'juegos.db' ))

metadatos = MetaData()

tabla_wiitdb_juegos = Table('wiitdb_juegos', metadatos,
    Column('idgame', VARCHAR(6) , primary_key=True),
    Column('name'  , Unicode(255)),
    Column('region', Unicode(255)),
    Column('title_EN', Unicode(255)),
    Column('synopsis_EN', Unicode(255)),
    Column('title_ES', Unicode(255)),
    Column('synopsis_ES', Unicode(255)),
    Column('title_PT', Unicode(255)),
    Column('synopsis_PT', Unicode(255)),
    Column('developer', Unicode(255)),
    Column('publisher', Unicode(255)),
    Column('anio', Integer),
    Column('mes', Integer),
    Column('dia', Integer),
    Column('wifi_players', Integer),
    Column('input_players', Integer),
)

# solo crea las tablas cuando no existen
metadatos.create_all(BDD_PERSISTENTE)

class JuegoWIITDB(object):
    'class representing a game on the data base from WiiTDB'
    def __init__(self , idgame , name , region, 
                                                   title_EN, synopsis_EN,
                                                   title_ES, synopsis_ES,
                                                   title_PT, synopsis_PT,
                        developer, publisher, anio, mes, dia, wifi_players, input_players
                                                   ):
        self.idgame = util.decode(idgame)
        self.name = util.decode(name)
        self.region = util.decode(region)
        self.title_EN = util.decode(title_EN)
        self.synopsis_EN = util.decode(synopsis_EN)
        self.title_ES = util.decode(title_ES)
        self.synopsis_ES = util.decode(synopsis_ES)
        self.title_PT = util.decode(title_PT)
        self.synopsis_PT = util.decode(synopsis_PT)
        self.developer = util.decode(developer)
        self.publisher = util.decode(publisher)
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.wifi_players = wifi_players
        self.input_players = input_players

    def __repr__(self):
        return "%s (%s)" % (self.name, self.idgame)

from juego import Juego

mapper(JuegoWIITDB , tabla_wiitdb_juegos)
Session = sessionmaker(bind=BDD_PERSISTENTE, autoflush=True, transactional = True)
session = Session()

