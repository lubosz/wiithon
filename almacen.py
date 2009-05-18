#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import config
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Text, VARCHAR, MetaData, ForeignKey

'''
sudo apt-get install python-sqlalchemy

Documentación: http://www.sqlalchemy.org/docs/05/ormtutorial.html#define-and-create-a-table
Ojo, mi ubuntu va con SQLAlchemy 0.4 pero el último es 0.5x
Aquí un wiki con las diferencias:
http://www.sqlalchemy.org/trac/wiki/05Migration
'''

motor = create_engine('sqlite:///%s' % os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' ))
metadatos = MetaData()

tablaJuego = Table('juegos',metadatos,
	# claves primarias y foraneas
	Column('id',Integer,primary_key=True),
	# campos
	Column('idgame',VARCHAR(6)),
	Column('titulo', VARCHAR(50)),
	Column('year',Integer),
	Column('quarter',Integer), # 1=principios de año, 2, 3, 4 = finales de año
	Column('puntuacion',Integer), # del 0 al 5
)

tablaCaratula = Table('caratulas',metadatos,
	# claves primarias y foraneas
	Column('id',Integer,primary_key=True),
	Column('idJuego',Integer),#, ForeignKey('juegos.id')), # clave foranea de "juegos"
	# campos
	Column('tipo',VARCHAR(255)), # Tipos : normal160x225, disco160x160
	Column('fichero',VARCHAR(255)), # Nombre del fichero PNG, de momento no hace falta otra tabla "tipos de imagen"
)

# solo crea las tablas cuando no existen
metadatos.create_all(motor)

