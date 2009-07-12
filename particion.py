#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import config
from util import SintaxisInvalida

class Particion:
    def __init__(self, device, fabricante):
        self.device = device                # nombre lógico unix (/dev/sda1)
        self.usado = 0.0
        self.libre = 0.0
        self.total = 0.0                    # Espacio en GB total de la partición
        self.fabricante = fabricante        # Nombre del fabricante, requiere udevinfo
        
    def __init__(self, device_y_fabricante):
        cachos = device_y_fabricante.strip().split(config.SEPARADOR)
        if(len(cachos)==5):
            self.device = cachos[0]         # nombre lógico unix (/dev/sda1)
            self.usado = float(cachos[1])
            self.libre = float(cachos[2])
            self.total = float(cachos[3])          # Espacio en GB total de la partición
            self.fabricante = cachos[4]     # Nombre del fabricante, requiere udevinfo
        else:
            raise SintaxisInvalida

    def __repr__(self):
        return "%s (%s) %.2f" % (self.device, self.fabricante, self.total)
