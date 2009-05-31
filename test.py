#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import time
from pool import Pool
import subprocess
import threading
from threading import Thread

class PoolCustomizada(Pool):
	def __init__(self , numHilos):
		Pool.__init__(self , numHilos)

	def ejecutar(self , idWorker , elemento , dato1 , dato2):
		print "Trabajo realizado sobre Elemento = %s por Hilo = %d" % (elemento,idWorker+1)
		print "dato1 = %s" % dato1
		print "dato2 = %s" % dato2
		time.sleep(1)

class HiloPool(threading.Thread):
	def run(self):
		self.pool = PoolCustomizada(15)
		for i in range(30):
			self.pool.nuevoElemento("elemento %d" % i)
		self.pool.empezar(args=("hola","adios"))

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
