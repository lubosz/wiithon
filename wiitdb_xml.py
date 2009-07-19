#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import libxml2

from juego import Juego
from wiitdb_companies import Companie
from wiitdb_juego import JuegoWIITDB, Accesorio, RatingContent, RatingType, JuegoDescripcion
import util

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''

db =        util.getBDD()
session =   util.getSesionBDD(db)

class WiiTDBXML:
    
    def __init__(self):
        self.version = '0'
        self.games = 0

    def leerAtributo(self, nodo, atributo):
        valor = ""
        attr = nodo.get_properties()
        while attr != None:
            if attr.name == atributo:
                valor = attr.content
            attr = attr.next    
        return valor
        
    def run(self):
        #transicion = session.create_transaction()

        fichXML = 'recursos/wiitdb/wiitdb.xml'
        xmldoc = libxml2.parseFile(fichXML)
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

                        creado = False
                        juego = None
                        name = self.leerAtributo(nodo, 'name')
                        
                        if nodo.children is not None:
                            nodo = nodo.children
                            while nodo.next is not None:
                                if nodo.type == "element":
                                    # Objeto *juego* aún no creado
                                    if not creado:
                                        if nodo.name == "id":
                                            idgame = nodo.content
                                            sql = util.decode("idgame=='%s'" % (idgame))
                                            juego = session.query(JuegoWIITDB).filter(sql).first()
                                            if juego == None:
                                                juego = JuegoWIITDB(nodo.content, name)

                                            creado = True                                                
                                    
                                    # ya se ha creado
                                    else:
                                                                                    
                                        if nodo.name == "region":
                                            juego.region = nodo.content
                                            
                                        elif nodo.name == "locale":
                                            lang = self.leerAtributo(nodo, 'lang')

                                            sql = util.decode("lang=='%s' and idgame='%s'" % (lang, juego.idgame))
                                            descripcion = session.query(JuegoDescripcion).filter(sql).first()
                                            if descripcion == None:
                                                descripcion = JuegoDescripcion(lang, juego.idgame)
                                                session.save( descripcion )

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

                                        elif nodo.name == "developer":
                                            juego.developer = nodo.content
                                            
                                        elif nodo.name == "publisher":
                                            juego.publisher = nodo.content
                                            
                                        elif nodo.name == "date":
                                            pass
                                            
                                        elif nodo.name == "genre":
                                            pass
                                            
                                        elif nodo.name == "rating":
                                            tipo = self.leerAtributo(nodo, 'type')
                                            sql = util.decode("tipo=='%s'" % (tipo))
                                            rating_type = session.query(RatingType).filter(sql).first()
                                            if rating_type == None:
                                                rating_type = RatingType(tipo)
                                                session.save( rating_type )
                                                
                                            valor = self.leerAtributo(nodo, 'value')
                                            # valor es una atributo de la relacion
                                            juego.rating.append(rating_type)
                                            
                                            #print juego.rating
                                                
                                            if nodo.children is not None:
                                                nodo = nodo.children
                                                while nodo.next is not None:
                                                    if nodo.type == "element":
                                                        if nodo.name == "descriptor":
                                                            valor = nodo.content
                                                            sql = util.decode("valor=='%s' and tipo =='%s'" % (valor, rating_type.tipo))
                                                            rating_content = session.query(RatingContent).filter(sql).first()
                                                            if rating_content == None:
                                                                rating_content = RatingContent(valor)
                                                                session.save(rating_content)
                                                                
                                                            rating_type.contenidos.append(rating_content)

                                                    nodo = nodo.next
                                                nodo = nodo.parent

                                        elif nodo.name == "wi-fi":
                                            juego.wifi_players = self.leerAtributo(nodo, 'players')
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
                                                                    session.save(accesorio)

                                                                if obligatorio == 'true':
                                                                    accesorio.obligatorio.append(juego)
                                                                else:
                                                                    accesorio.opcional.append(juego)

                                                    # siguiente control
                                                    nodo = nodo.next
                                                
                                                # volvemos a input
                                                nodo = nodo.parent
                                        
                                # siguiente hijo de game
                                nodo = nodo.next
                                
                            #volver a game
                            nodo = nodo.parent
                            if creado:
                                session.merge(juego)
                                #session.save(juego)
                            
                        else:
                            print "Error en %s" % name

                    cont += 1
                    if cont % 50 == 0:
                        print "< %d%% >" % (cont * 100 / self.games)
                    
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

