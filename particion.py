#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import util
import config
from util import SintaxisInvalida

class Particion:       
    def __init__(self, device__datos_y_fabricante):
        cachos = device__datos_y_fabricante.strip().split(config.SEPARADOR)
        if(len(cachos)==6+1):
            # nombre lógico unix (/dev/sda1)
            self.device = cachos[0]
            
            # tipo de particion "fat32|wbfs"
            self.tipo = util.decode(cachos[1])
            
            # Espacio en GB usados de la partición
            self.usado = float(cachos[2].replace(",",".").replace("G",""))
            
            # Espacio en GB libres de la partición
            self.libre = float(cachos[3].replace(",",".").replace("G",""))
            
            # Espacio en GB total de la partición
            self.total = float(cachos[4].replace(",",".").replace("G",""))
            
            # Nombre del fabricante, requiere udevinfo
            self.fabricante = util.decode(cachos[5])
        else:
            raise SintaxisInvalida

    def __repr__(self):
        return "%s (%s) %.0f GB" % (self.device, self.fabricante, self.total)
