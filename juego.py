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
from sqlalchemy.orm import relation, backref, sessionmaker

import config
import util
from util import SintaxisInvalida

Base = declarative_base()

class Juego(Base):    
    __tablename__ = 'juegos'

    idgame = Column('idgame', VARCHAR(6), primary_key=True)
    title = Column('title', Unicode(255))
    size = Column('size', Float)
    device = Column('device', VARCHAR(10))

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

util.crearBDD(Base.metadata)

'''
# http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg09381.html

from wiitdb_juego import JuegoWIITDB

mapper(Juego , tabla_juegos, properties={
    'wiitdb_juegos':relation(JuegoWIITDB, 
        primaryjoin=tabla_juegos.c.idgame==tabla_wiitdb_juegos.c.idgame,
        _local_remote_pairs=[(tabla_juegos.c.idgame, tabla_wiitdb_juegos.c.idgame)],
        foreign_keys=[tabla_wiitdb_juegos.c.idgame],
    )
})
'''
