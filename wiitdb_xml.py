#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import libxml2
import datetime
from threading import Thread
from datetime import date
import zipfile

import config
import util
import wiitdb_schema
from wiitdb_schema import *

'''
    * name : returns the node name
    * type : returns a string indicating the node type
    * content : returns the content of the node, it is based on xmlNodeGetContent() and hence is recursive.
    * parent , children, last, next, prev, doc, properties: pointing to the associated element in the tree, those may return None in case no such link exists.
'''

db =        util.getBDD()
session =   util.getSesionBDD(db)

class ErrorImportandoWiiTDB(Exception):
    pass
    
class ErrorCreandoTablas(Exception):
    pass

class WiiTDBXML(Thread):
    
    def __init__(self, url, destino, fichXML, 
                                callback_spinner,
                                callback_nuevo_juego,
                                callback_nuevo_descripcion,
                                callback_nuevo_genero,
                                callback_nuevo_online_feature,
                                callback_nuevo_accesorio,
                                callback_nuevo_companie,
                                callback_error_importando,
                                callback_empieza_descarga,
                                callback_empieza_descomprimir,
                                callback_empieza_importar,
                                callback_termina_importar
                                ):
        Thread.__init__(self)
        self.url = url
        self.todos = not url.find("?ID=")!=-1
        self.destino = destino
        self.fichXML = fichXML
        self.callback_spinner = callback_spinner
        self.callback_nuevo_juego = callback_nuevo_juego
        self.callback_nuevo_descripcion = callback_nuevo_descripcion
        self.callback_nuevo_genero = callback_nuevo_genero
        self.callback_nuevo_online_feature = callback_nuevo_online_feature
        self.callback_nuevo_accesorio = callback_nuevo_accesorio
        self.callback_nuevo_companie = callback_nuevo_companie
        self.callback_error_importando = callback_error_importando
        self.callback_empieza_descarga = callback_empieza_descarga
        self.callback_empieza_descomprimir = callback_empieza_descomprimir
        self.callback_empieza_importar = callback_empieza_importar
        self.callback_termina_importar = callback_termina_importar
        self.version = '0'
        self.games = 0
        self.salir = False
        
    def limpiarTemporales(self):
        if os.path.exists(self.destino):
            os.remove(self.destino)
            
        if os.path.exists(self.fichXML):
            os.remove(self.fichXML)
    
    def descargarZIP(self):
        if self.callback_empieza_descarga:
            self.callback_empieza_descarga(self.url)
        util.descargar(self.url, self.destino)
        
    def descomprimirZIP(self):
        if self.callback_empieza_descomprimir:
            self.callback_empieza_descomprimir(self.destino)
        # descargar XML
        zip = zipfile.ZipFile(self.destino)
        zip.extract(self.fichXML)
        zip.close()
        
    def run(self):
        self.limpiarTemporales()
        
        self.descargarZIP()
        self.descomprimirZIP()

        #transicion = session.create_transaction() 
        # empieza transacion
        #session.begin()
        if os.path.exists(self.fichXML):
            xmldoc = libxml2.parseFile(self.fichXML)
            ctxt = xmldoc.xpathNewContext()
            nodo = ctxt.xpathEval("//*[name() = 'datafile']")[0]
            
            '''
            try:
                metadatos = Base.metadata
                db = util.getBDD()
                metadatos.drop_all(db)
                metadatos.create_all(db)
            except:
                self.error_importando(_("Base de datos ocupada."))
            '''
            if self.callback_empieza_importar:
                self.callback_empieza_importar(self.fichXML)

            cont = 0
            while not self.salir and nodo != None:
                
                if nodo.type == "element":

                    if nodo.name == "datafile":
                        nodo = nodo.children

                    elif nodo.name == "WiiTDB":
                        self.version = int(self.leerAtributo(nodo, 'version'))                        
                        self.games = int(self.leerAtributo(nodo, 'games').split("/")[0])

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
                                                try:
                                                    juego = session.query(JuegoWIITDB).filter(sql).first()
                                                except:
                                                    self.error_importando(_("XML invalido"))

                                                if juego == None:
                                                    juego = JuegoWIITDB(nodo.content, name)

                                                iniciado = True
                                        
                                        # ya se ha iniciado
                                        else:

                                            if nodo.name == "region":
                                                juego.region = nodo.content

                                            elif nodo.name == "locale":
                                                lang = self.leerAtributo(nodo, 'lang')

                                                sql = util.decode("lang=='%s' and idJuegoWIITDB='%s'" % (lang, juego.idJuegoWIITDB))
                                                descripcion = session.query(JuegoDescripcion).filter(sql).first()
                                                if descripcion == None:
                                                    descripcion = JuegoDescripcion(lang)
                                                    if self.callback_nuevo_descripcion:
                                                        self.callback_nuevo_descripcion(descripcion)

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
                                                try:
                                                    year = int(self.leerAtributo(nodo, 'year'))
                                                    month = int(self.leerAtributo(nodo, 'month'))
                                                    day = int(self.leerAtributo(nodo, 'day'))
                                                    
                                                    fecha = date(year, month, day)
                                                    
                                                    juego.fecha_lanzamiento = fecha
                                                    
                                                except ValueError:
                                                    pass
                                                
                                            elif nodo.name == "genre":
                                                valores = nodo.content
                                                for valor in valores.split(","):
                                                    valor = valor.strip().replace("'","`")
                                                    sql = util.decode("nombre=='%s'" % (valor))
                                                    genero = session.query(Genero).filter(sql).first()
                                                    if genero == None:
                                                        genero = Genero(valor)
                                                        if self.callback_nuevo_genero:
                                                            self.callback_nuevo_genero(genero)

                                                    juego.genero.append(genero)

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
                                                                        if self.callback_nuevo_online_feature:
                                                                            self.callback_nuevo_online_feature(online_feature)
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

                                                                if nombres[0] == "wiimotenunchuk":
                                                                    nombres = ['wiimote', 'nunchuck']
                                                                for nombre in nombres:
                                                                    nombre = nombre.strip()
                                                                    '''
                                                                    wiimote = wimmote
                                                                    nunchuk = nunchuck
                                                                    gamecube = gamegube
                                                                    classiccontroller = calssiccontroller, classccontroller
                                                                    balanceboard = wii balance board
                                                                    motionplus = motion.plus
                                                                    '''
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
                                                                    elif nombre == "motion.plus":
                                                                        nombre = "motionplus"

                                                                    sql = util.decode("nombre=='%s'" % (nombre))
                                                                    accesorio = session.query(Accesorio).filter(sql).first()
                                                                    if accesorio == None:
                                                                        accesorio = Accesorio(nombre)
                                                                        if self.callback_nuevo_accesorio:
                                                                            self.callback_nuevo_accesorio(accesorio, obligatorio == 'true')

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
                                                juego.roms.append(rom)

                                    # siguiente hijo de game
                                    nodo = nodo.next
                                    
                                #volver a game
                                nodo = nodo.parent
                                if iniciado:
                                    session.save_or_update(juego)
                                    if self.callback_nuevo_juego:
                                        self.callback_nuevo_juego(juego)
                                else:
                                    self.error_importando(_("XML invalido"))

                            else:
                                self.error_importando(_("XML invalido"))

                        cont += 1
                        # callback cada 1%
                        try:
                            llamarCallback = (cont % (self.games / 100) == 0)
                        except ZeroDivisionError:
                            llamarCallback = True
                        
                        if llamarCallback and self.callback_spinner:
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
                                        sql = util.decode("code=='%s'" % (code))
                                        companie = session.query(Companie).filter(sql).first()
                                        if companie == None:
                                            companie = Companie(code, name)
                                            session.save(companie)
                                            if self.callback_nuevo_companie:
                                                self.callback_nuevo_companie(companie)

                                nodo = nodo.next
                            nodo = nodo.parent
                        else:
                            self.error_importando(_("XML invalido"))

                nodo = nodo.next

            # libera el xml
            xmldoc.freeDoc()
            ctxt.xpathFreeContext()

            # hacemos efectivas las transacciones
            session.commit()
            
            self.limpiarTemporales()
            
            if self.callback_termina_importar:
                self.callback_termina_importar(self.fichXML, self.todos)
        else:
            self.error_importando(_("No existe el XML"))

    def leerAtributo(self, nodo, atributo):
        valor = ""
        attr = nodo.get_properties()
        while attr != None:
            if attr.name == atributo:
                valor = attr.content
            attr = attr.next    
        return valor

    def error_importando(self, motivo):
        self.interrumpir()
        #session.rollback()
        self.limpiarTemporales()
        if self.callback_error_importando:
            self.callback_error_importando(self, self.fichXML, motivo)

    def interrumpir(self):
        self.salir = True
