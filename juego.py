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
import util

from sqlalchemy.orm import mapper, relation, sessionmaker, backref
from sqlalchemy import create_engine, Table, Column, Integer, Float, \
                    Text, VARCHAR, MetaData, ForeignKey, Unicode
import config
from util import SintaxisInvalida   
from wiitdb_juego import tabla_wiitdb_juegos, JuegoWIITDB

BDD_PERSISTENTE = create_engine('sqlite:///%s'
                                % os.path.join(
        config.HOME_WIITHON_BDD, 'juegos.db' ))

metadatos = MetaData()

tabla_juegos = Table('juegos', metadatos,
    Column('idgame', VARCHAR(6), primary_key=True),
    Column('title', Unicode(255)),
    Column('size', Float),
    Column('device', VARCHAR(10)),
)

# solo crea las tablas cuando no existen
metadatos.create_all(BDD_PERSISTENTE)

class Juego(object):
    'class representing a game on the data base'
    def __init__(self , idgame , title , size, device):
        self.idgame = util.decode(idgame)
        self.title = util.decode(title)
        self.size = float(size)
        self.device = util.decode(device)
        
    def __init__(self, linea, device):
        cachos = linea.strip().split(config.SEPARADOR)
        if(len(cachos)==3):
            self.idgame = util.decode(cachos[0])
            self.title = util.decode(cachos[1])
            self.size = float(cachos[2])
            self.device = util.decode(device)
        else:
            raise SintaxisInvalida

    def __repr__(self):
        return "%s (%s) %s" % (self.title, self.idgame, self.device)

# http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg09381.html
'''
from wiitdb_juego import JuegoWIITDB

mapper(Juego , tabla_juegos, properties={
    'wiitdb_juegos':relation(JuegoWIITDB, 
        primaryjoin=tabla_juegos.c.idgame==tabla_wiitdb_juegos.c.idgame,
        _local_remote_pairs=[(tabla_juegos.c.idgame, tabla_wiitdb_juegos.c.idgame)],
        foreign_keys=[tabla_wiitdb_juegos.c.idgame],
    )
})
'''
mapper(Juego , tabla_juegos)
Session = sessionmaker(bind=BDD_PERSISTENTE, autoflush=True, transactional = True)
session = Session()
