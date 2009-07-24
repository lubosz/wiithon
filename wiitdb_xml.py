#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import libxml2
from threading import Thread

import config
import util
from juego import Juego
from wiitdb_schema import JuegoWIITDB, Accesorio, RatingContent, RatingType, RatingValue , JuegoDescripcion, Companie, Rom, OnlineFeatures

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiiTDBXML(Thread):
    
    def __init__(self, fichXML, callback_spinner):
        Thread.__init__(self)
        self.fichXML = fichXML
        self.callback_spinner = callback_spinner
        self.version = '0'
        self.games = 0
        
    def run(self):
        #transicion = session.create_transaction() 
        if os.path.exists(self.fichXML):
            xmldoc = libxml2.parseFile(self.fichXML)
            ctxt = xmldoc.xpathNewContext()
            nodo = ctxt.xpathEval("//*[name() = 'datafile']")[0]
            
            cont = 0
            
            while nodo != None:
                if nodo.type == "element":

                    if nodo.name == "datafile":
                        nodo = nodo.children

                    elif nodo.name == "WiiTDB":
                        self.version = int(self.leerAtributo(nodo, 'version'))

                        import time
                        from datetime import date
                        
                        #print time.time()
                        
                        self.games = int(self.leerAtributo(nodo, 'games'))
                        print "Importando %s juegos. version de XML: %s" % (self.games, self.version)

                    elif nodo.name == "game":
                        if nodo.type == "element":

                            iniciado = False
                            juego = None
                            name = self.leerAtributo(nodo, 'name')
                            
                            if nodo.children is not None:
                                nodo = nodo.children
                                while nodo.next is not None:
                                    if nodo.type == "element":
                                        # id, region, locale, developer, publisher, date, genre, rating, wi-fi, input, rom
                                        if not iniciado:
                                            if nodo.name == "id":
                                                idgame = nodo.content
                                                sql = util.decode("idgame=='%s'" % (idgame))
                                                juego = session.query(JuegoWIITDB).filter(sql).first()
                                                if juego == None:
                                                    juego = JuegoWIITDB(nodo.content, name)
                                                iniciado = True
                                        
                                        # ya se ha iniciado
                                        else:
                                                                                        
                                            if nodo.name == "region":
                                                juego.region = nodo.content
                                                
                                            elif nodo.name == "locale":
                                                lang = self.leerAtributo(nodo, 'lang')

                                                sql = util.decode("lang=='%s' and idgame='%s'" % (lang, juego.idgame))
                                                descripcion = session.query(JuegoDescripcion).filter(sql).first()
                                                if descripcion == None:
                                                    descripcion = JuegoDescripcion(lang)

                                                if nodo.children is not None:
                                                    nodo = nodo.children
                                                    while nodo.next is not None:
                                                        if nodo.type == "element":
                                                            if nodo.name == "title":
                                                                descripcion.title = nodo.content
                                                            elif nodo.name == "synopsis":
                                                                descripcion.synopsis = nodo.content
                                                        nodo = nodo.next
                                                    nodo = nodo.parent
                                                    
                                                # añadimos la descripcion al juego
                                                juego.descripciones.append(descripcion)

                                            elif nodo.name == "developer":
                                                juego.developer = nodo.content
                                                
                                            elif nodo.name == "publisher":
                                                juego.publisher = nodo.content
                                                
                                            elif nodo.name == "date":
                                                year = self.leerAtributo(nodo, 'year')
                                                month = self.leerAtributo(nodo, 'month')
                                                day = self.leerAtributo(nodo, 'day')
                                                
                                                if year == "" or month == "" or day == "":
                                                    fecha = "1900-01-01"
                                                else:
                                                    fecha = "%s-%s-%s" % (year, month, day)
                                                juego.fecha_lanzamiento = fecha
                                                
                                            elif nodo.name == "genre":
                                                pass
                                                
                                            elif nodo.name == "rating":
                                                # crear un tipo de rating si es nuevo
                                                tipo = self.leerAtributo(nodo, 'type')
                                                sql = util.decode("tipo=='%s'" % (tipo))
                                                rating_type = session.query(RatingType).filter(sql).first()
                                                if rating_type == None:
                                                    rating_type = RatingType(tipo)
                                                    
                                                juego.rating_type = rating_type
                                                    
                                                # crea una relacion si es un nuevo valor del tipo
                                                valor = self.leerAtributo(nodo, 'value')
                                                sql = util.decode("idRatingType=='%s' and valor=='%s'" % (rating_type.idRatingType , valor))
                                                rating_value = session.query(RatingValue).filter(sql).first()
                                                if rating_value == None:
                                                    rating_value = RatingValue(valor)                                        
                                                    rating_type.valores.append(rating_value)
                                                    
                                                juego.rating_value = rating_value
                                                    
                                                if nodo.children is not None:
                                                    nodo = nodo.children
                                                    while nodo.next is not None:
                                                        if nodo.type == "element":
                                                            if nodo.name == "descriptor":
                                                                valores = nodo.content
                                                                for valor in valores.split(","):
                                                                    valor = valor.strip()
                                                                    sql = util.decode("idRatingType=='%s' and valor=='%s'" %
                                                                                                (rating_type.idRatingType, valor))
                                                                    rating_content = session.query(RatingContent).filter(sql).first()
                                                                    if rating_content == None:
                                                                        rating_content = RatingContent(valor)
                                                                        rating_type.contenidos.append(rating_content)
                                                                        
                                                                    juego.rating_contents.append(rating_content)

                                                        nodo = nodo.next
                                                    nodo = nodo.parent

                                            elif nodo.name == "wi-fi":
                                                juego.wifi_players = self.leerAtributo(nodo, 'players')
                                                
                                                if nodo.children is not None:
                                                    nodo = nodo.children
                                                    while nodo.next is not None:
                                                        if nodo.type == "element":
                                                            if nodo.name == "feature":
                                                                valores = nodo.content
                                                                for valor in valores.split(","):
                                                                    valor = valor.strip()
                                                                    sql = util.decode("valor=='%s'" % (valor))
                                                                    online_feature = session.query(OnlineFeatures).filter(sql).first()
                                                                    if online_feature == None:
                                                                        online_feature = OnlineFeatures(valor)
                                                                    juego.features.append(online_feature)
                                                        nodo = nodo.next
                                                    nodo = nodo.parent
                                                
                                            elif nodo.name == "input":
                                                juego.input_players = self.leerAtributo(nodo, 'players')

                                                if nodo.children is not None:
                                                    nodo = nodo.children
                                                    while nodo.next is not None:
                                                        if nodo.type == "element":
                                                            if nodo.name == "control":
                                                                nombres = self.leerAtributo(nodo, 'type').split(",")
                                                                obligatorio = self.leerAtributo(nodo, 'required')
                                                                # EMPIEZA PARCHE NOMBRES
                                                                if nombres[0] == "wiimotenunchuk":
                                                                    nombres = ['wiimote', 'nunchuck']
                                                                for nombre in nombres:
                                                                    nombre = nombre.strip()
                                                                    if nombre == "wimmote":
                                                                        nombre = "wiimote"
                                                                    elif nombre == "nunchuck":
                                                                        nombre = "nunchuk"
                                                                    elif nombre == "gamegube":
                                                                        nombre = "gamecube"
                                                                    elif nombre == "calssiccontroller" or nombre == "classccontroller":
                                                                        nombre = "classiccontroller"
                                                                    elif nombre == "wii balance board":
                                                                        nombre = "balanceboard"
                                                                    # TERMINA PARCHE NOMBRES
                                                                    sql = util.decode("nombre=='%s'" % (nombre))
                                                                    accesorio = session.query(Accesorio).filter(sql).first()
                                                                    if accesorio == None:
                                                                        accesorio = Accesorio(nombre)

                                                                    if obligatorio == 'true':
                                                                        juego.obligatorio.append(accesorio)
                                                                    else:
                                                                        juego.opcional.append(accesorio)

                                                        # siguiente control
                                                        nodo = nodo.next
                                                    
                                                    # volvemos a input
                                                    nodo = nodo.parent
                                                    
                                            elif nodo.name == "rom":
                                                version = self.leerAtributo(nodo, 'version')
                                                name = self.leerAtributo(nodo, 'name')
                                                size = self.leerAtributo(nodo, 'size')
                                                crc = self.leerAtributo(nodo, 'crc')
                                                md5 = self.leerAtributo(nodo, 'md5')
                                                sha1 = self.leerAtributo(nodo, 'sha1')
                                                                                           
                                                rom = Rom(version, name, size, crc, md5, sha1)
                                                juego.rom = rom                                            

                                    # siguiente hijo de game
                                    nodo = nodo.next
                                    
                                #volver a game
                                nodo = nodo.parent
                                if iniciado:
                                    session.save_or_update(juego)

                            else:
                                print "Error en %s" % name

                        cont += 1
                        self.callback_spinner(cont, self.games)
                        
                        nodo = nodo.next

                    elif nodo.name == "companies":

                        if nodo.children is not None:
                            nodo = nodo.children

                            while nodo.next is not None:
                                if nodo.type == "element":
                                    if nodo.name == "company":
                                        code = self.leerAtributo(nodo, 'code')
                                        name = self.leerAtributo(nodo, 'name')
                                        comp = Companie(code, name)
                                        session.merge(comp)

                                nodo = nodo.next
                            nodo = nodo.parent
                        else:
                            print "No hay Companies (?)"

                nodo = nodo.next

            # libera el xml
            xmldoc.freeDoc()
            ctxt.xpathFreeContext()

            # hacemos efectivas las transacciones
            session.commit()
        else:
            print "El fichero xml %s, no existe" % self.fichXML

    def leerAtributo(self, nodo, atributo):
        valor = ""
        attr = nodo.get_properties()
        while attr != None:
            if attr.name == atributo:
                valor = attr.content
            attr = attr.next    
        return valor

