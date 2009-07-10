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

tabla = Table('wiitdb_companies',metadatos,
    Column('code',VARCHAR(2),primary_key=True),
    Column('name', VARCHAR(255)),
)

# solo crea las tablas cuando no existen
metadatos.create_all(motor)

class Companie(object):

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __repr__(self):
        return "%s - %s" % (self.code, self.name)

mapper(Companie , tabla)
Session = sessionmaker(bind=motor , autoflush=True, transactional = True)
session = Session()
