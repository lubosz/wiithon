#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# miércoles, 21 de octubre de 2009

import math
from math import sqrt

##################### GENERAL #############################

def factorial(n):
    if n == 0:
        return 1.0
    else:
        return n * factorial(n-1)
        
def productorio(lista):
    total = 1.0
    for n in lista:
        total *= n
    return total
        
def sumatorio(lista):
    total = 0.0
    for n in lista:
        total += n
    return total

##################### COMBINATORIA #############################

'''
Sí entran todos los elementos.
Sí importa el orden.
No/Si se repiten los elementos.
'''
def permu(n, circular = False):
    if circular:
        return factorial(n-1)
    elif isinstance(n,list):
        return factorial(sumatorio(n)) / productorio(map (lambda x:factorial(x),n))
    else:
        return factorial(n)

'''
No entran todos los elementos.
Sí importa el orden.
No/Si se repiten los elementos.
'''
def varia(n, m, repeticion = False):
    if repeticion:
        return n**m
    else:
        return factorial(n) / factorial(n-m)

'''
No  entran todos los elementos.
No importa el orden.
No/Si se repiten los elementos. 
'''
def combi(n, m, repeticion = False):
    if repeticion:
        return combi(n+m-1,n)
    else:
        return factorial(n) / (factorial(m) * factorial(n-m))

##################### ESTADISTICA #############################

class MuestraEstadistica:
    
    def __init__(self, xi, fa):
        self.xi = xi
        self.fa = fa

    def total_muestras(self):
        return sumatorio(self.fa)

    def frec_rel(self):
        fi = []
        muestras = self.total_muestras()
        for i in range(len(self.fa)):
            fi.append(self.fa[i] / muestras)
        return fi
    
    def frec_acu(self):
        Fa = []
        acumulado = 0.0
        for i in range(len(self.fa)):
            acumulado += self.fa[i]
            Fa.append(acumulado)
        return Fa
    
    def frec_acu_rel(self):
        fi = self.frec_rel()
        Fi = []
        acumulado = 0.0
        for i in range(len(fi)):
            acumulado += fi[i]
            Fi.append(acumulado)
        return Fi

    def frec_rel_porc(self):
        fi = []
        muestras = self.total_muestras()
        for i in range(len(self.fa)):
            fi.append((self.fa[i] / muestras) * 100)
        return fi

    def moda(self):
        i_max = 0
        for i in range(len(self.fa)):
            if self.fa[i] > self.fa[i_max]:
                i_max = i
        return self.xi[i_max]

    def mediana(self):
        muestras = self.total_muestras()
        valor_mediana = muestras / 2.0
        Fa = self.frec_acu()
        for i in range(len(Fa)):
            if Fa[i] > valor_mediana:
                return self.xi[i]
            elif Fa[i] == valor_mediana:
                return (self.xi[i] + self.xi[i+1]) / 2.0
        return -1

    def cuartiles(self, k):
        # 1<=k<=3
        if k < 1:
            k = 1
        if k > 3:
            k = 3
        muestras = self.total_muestras()
        valor_mediana = (k * muestras) / 4.0
        Fa = self.frec_acu()
        for i in range(len(Fa)):
            if Fa[i] > valor_mediana:
                return self.xi[i]
            elif Fa[i] == valor_mediana:
                return (self.xi[i] + self.xi[i+1]) / 2.0
        return -1
    
    def percentiles(self, k):
        # 1<=k<=99
        if k < 1:
            k = 1
        if k > 99:
            k = 99
        muestras = self.total_muestras()
        valor_mediana = (k * muestras) / 100.0
        Fa = self.frec_acu()
        for i in range(len(Fa)):
            if Fa[i] > valor_mediana:
                return self.xi[i]
            elif Fa[i] == valor_mediana:
                return (self.xi[i] + self.xi[i+1]) / 2.0
        return -1
    
    # momento k respecto a ref
    def momento(self, k, ref = 0):
        suma = 0.0
        muestras = self.total_muestras()
        for i in range(len(self.xi)):
             suma += (((self.xi[i]-ref)**k) * self.fa[i])
        return suma / muestras

    def media(self):
        return self.momento(1, 0)

    def varianza(self):
        return self.momento(2, self.media())
    
    # Coeficiente de asimetría de Fisher
    def asimetria_fisher(self):
        return self.momento(3, self.media()) / self.desviacion_tipica()**3
        
    def asimetria_pearson(self):
        return (self.media() - self.moda()) / self.desviacion_tipica()
        
    def asimetria_bowley(self):
        return (self.cuartiles(3) + self.cuartiles(1) - (2*self.mediana())) / (self.cuartiles(3) - self.cuartiles(1))
        
    def curtosis(self):
        return self.momento(4, self.media()) / self.desviacion_tipica()**4
    
    def desviacion_tipica(self):
        return sqrt(self.varianza())

    def mostrarInfo(self, titulo, lista):
        print "----- %s --------" % titulo
        t = 0.0
        for d in lista:
            print "%.2f, " % d,
            t += d
        print "Total: %.2f" % t
        
    def analisis(self):

        Fa = self.frec_acu()
        fi = self.frec_rel()
        Fi = self.frec_acu_rel()
        fi_porc = self.frec_rel_porc()

        self.mostrarInfo('Muestra', self.xi)
        self.mostrarInfo('Frecuencia absoluta', self.fa)
        self.mostrarInfo('Frecuencia absoluta acumulada', Fa)
        self.mostrarInfo('Frecuencia relativa', fi)
        self.mostrarInfo('Frecuencia relativa acumulada', Fi)
        self.mostrarInfo('Frecuencia en porcentaje', fi_porc)

        # valores unicos
        print "-----------------"
        print "Media = %.2f" % self.media()
        print "Moda = %.2f" % self.moda()
        print "Mediana = %.2f" % self.mediana()
        print "Cuartil 1 = %.2f" % self.cuartiles(1)
        print "Cuartil 2 = %.2f" % self.cuartiles(2)
        print "Cuartil 3 = %.2f" % self.cuartiles(3)
        print "Percentil 30 = %.2f" % self.percentiles(30)
        print "Percentil 60 = %.2f" % self.percentiles(60)
        print "Percentil 78 = %.2f" % self.percentiles(78)
        print "Momento 8 respecto la media = %.2f" % self.momento(8, self.media())
        print "Varianza = %.2f" % self.varianza()
        print "Desviacion tipica = %.2f" % self.desviacion_tipica()
        print "asimetria Fisher = %.2f" % self.asimetria_fisher()
        print "asimetria Pearson = %.2f" % self.asimetria_pearson()
        print "asimetria Bowley = %.2f" % self.asimetria_bowley()
        print "Curtosis = %.2f" % self.curtosis()

##################### MAIN #############################

def main():
    xi = [1,2,3,4,5,6]
    fa = [20,40,60,80,100,120]
    s = MuestraEstadistica(xi, fa)
    s.analisis()

if __name__ == '__main__':
    main()
