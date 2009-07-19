#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker

import config
import util

Base = declarative_base()

class Companie(Base):
    __tablename__ = 'wiitdb_companies'
    
    code = Column('code',VARCHAR(2),primary_key=True)
    name = Column('name', VARCHAR(255))

    def __init__(self, code, name):
        self.code = util.decode(code).strip()
        self.name = util.decode(name).strip()

    def __repr__(self):
        return "%s - %s" % (self.code, self.name)

util.crearBDD(Base.metadata)
