#!/usr/bin/env python
#-*-coding: utf-8-*-

import time
from pool import HiloPool

hilo = HiloPool()
hilo.start()

i=0
while hilo.isAlive():
	print "Aún no ha terminado %d" % i
	time.sleep(2)
	i = i + 1

print "YA ha terminado!"

'''
p = subprocess.Popen("sudo /usr/local/share/wiithon/wbfs -p /dev/sdb1 add /home/makiolo/descargas/Resident\ Evil\ 4\ Wii\ Edition.iso" , shell=True , stdout=subprocess.PIPE)
out = p.stdout.readlines()
for linea in out:
	print "---------------"
	print linea.strip()
'''

#main()

'''
import os , config , almacen
from juego import session , Juego

print "cargando "+os.path.join( config.HOME_WIITHON_BDD , 'juegos.db' )

print "Juegos antes de insertar"
for j in session.query(Juego):
	print j

print "Se insertan juegos"
for i in range(10):
	j = Juego("GHX67"+str(i) , "Resident Evil 4" , 2008 , 1 , 5)
	existe = session.query(Juego).filter( "idgame==:idgame" ).params(idgame=j.idgame).count() > 0
	if existe:
		j.borrarCaratula()
		j.harakiri()
		print "Juego borrado"
	j.crearCaratula()
	session.save(j)
	print "Juego insertado"
session.commit()
print "Commit definitivo"

print "Juegos DESPUES de insertar"
for j in session.query(Juego):
	print j
'''
'''
import gtk
import gui

def cb(widget, *args):
    global wt_gui
    print 'exit'
    #wt_gui.alert_off()

wt_gui = gui.WiithonGUI()
res = wt_gui.alert('question', 'hola')

if res == 1:
    print 'Botón de la derecha'

elif res == 0:
    print 'Botón de la izquierda'

else:
    print 'another'
    print res


gtk.main()
'''
