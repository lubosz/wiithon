#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import libxml2
from wiitdb_companies import Companie, session
from wiitdb_juego import JuegoWIITDB
from juego import Juego

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''

class WiiTDBXML:

    def leerAtributo(self, nodo, atributo):
        valor = ""
        attr = nodo.get_properties()
        while attr != None:
            if attr.name == atributo:
                valor = attr.content
            attr = attr.next    
        return valor
        
    def __run__(self):
        fichXML = 'recursos/wiitdb/wiitdb.xml'
        xmldoc = libxml2.parseFile(fichXML)
        ctxt = xmldoc.xpathNewContext()
        nodo = ctxt.xpathEval("//*[name() = 'datafile']")[0]
        while nodo != None:

            if nodo.type == "element":

                if nodo.name == "datafile":
                    nodo = nodo.children

                elif nodo.name == "WiiTDB":
                    version = leerAtributo(nodo, 'version')
                    print "Importando xml version: %s" % version

                elif nodo.name == "game":
                    while (nodo.next != None):
                        if nodo.type == "element":
                            if nodo.name == "game":
                                idgame = ""
                                name = ""
                                region = ""
                                title_EN = ""
                                synopsis_EN = ""
                                title_ES = ""
                                synopsis_ES = ""
                                title_PT = ""
                                synopsis_PT = ""
                                developer = ""
                                publisher = ""
                                anio = 0
                                mes = 0
                                dia = 0
                                wifi_players = 0
                                input_players = 0

                                name = leerAtributo(nodo, 'name')
                                
                                #adentrarse en game
                                nodo = nodo.children
                                
                                while nodo.next is not None:
                                    if nodo.type == "element":
                                        if nodo.name == "id":
                                            idgame = nodo.content
                                        elif nodo.name == "developer":
                                            developer = nodo.content
                                        elif nodo.name == "publisher":
                                            publisher = nodo.content
                                        elif nodo.name == "region":
                                            region = nodo.content
                                        elif nodo.name == "wi-fi":
                                            wifi_players = leerAtributo(nodo, 'players')
                                        elif nodo.name == "input":
                                            input_players = leerAtributo(nodo, 'players')
                                        elif nodo.name == "locale":
                                            # leer atributos de locale
                                            lang = leerAtributo(nodo, 'lang')
                                            
                                            #adentrarse en locale
                                            nodo = nodo.children
                                            # FIXME: EN, JA, FR, DE, ES, IT, NL, PT, SV, NN, DA, FI, ZH, KO
                                            i = 0
                                            while nodo.next is not None:
                                                if nodo.type == "element":
                                                    if nodo.name == "title":
                                                        if lang == "EN":
                                                            title_EN = nodo.content
                                                        elif lang == "ES":
                                                            title_ES = nodo.content
                                                        elif lang == "PT":
                                                            title_PT = nodo.content
                                                    elif nodo.name == "synopsis":
                                                        if lang == "EN":
                                                            synopsis_EN = nodo.content
                                                        elif lang == "ES":
                                                            synopsis_ES = nodo.content
                                                        elif lang == "PT":
                                                            synopsis_PT = nodo.content
                                                nodo = nodo.next
                                                i += 1
                                            #volver a locale
                                            nodo = nodo.parent
                                            
                                    # siguiente hijo de game
                                    nodo = nodo.next
                                    
                                #volver a game
                                nodo = nodo.parent

                                juego = JuegoWIITDB(idgame , name , region,     title_EN, synopsis_EN,
                                                                                title_ES, synopsis_ES,
                                                                                title_PT, synopsis_PT,
                                                    developer, publisher, anio, mes, dia, wifi_players, input_players)
                                session.merge(juego)

                        nodo = nodo.next

                elif nodo.name == "companies":

                    nodo = nodo.children

                    while nodo.next is not None:
                        if nodo.type == "element":
                            if nodo.name == "company":
                                code = ""
                                name = ""

                                attr = nodo.get_properties()
                                while attr != None:
                                    if attr.name == "code":
                                        code = attr.content
                                    elif attr.name == "name":
                                        name = attr.content
                                    attr = attr.next    
                                comp = Companie(code, name)
                                session.merge(comp)

                        nodo = nodo.next

                    nodo = nodo.parent

            nodo = nodo.next

        # libera el xml
        xmldoc.freeDoc()
        ctxt.xpathFreeContext()

        # hacemos efectivas las transacciones
        session.commit()
