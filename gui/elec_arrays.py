from imports import *
from parameters import *

"""##Modelos de arrays"""

class Elec_Array:
  def __init__(self, N = 12, dx = 0, xi = 0, angularInsertion=0):
    self.Nchann = N
    self.dx =dx
    self.xi = xi
    self.angularInsertion = angularInsertion
    self.freqsAnalisis = []
    self.freqsElectrodos = []
    self.channel1_lowcut = None
    self.preprocessing = None
    self.T_SPL = None
    self.C_SPL = None
    self.pw = 0 #Pulse width de cada canal en segundos
    self.name = ''
    self.manufacturer = ''
    self.calcularFreqs()
    self.gs = self.channel_interaction_matrix()
    self.SR = None
    #self.mismatch = mismatch



    #Por sanidad del código, mantener las frecuencias siempre ordenadas de menor a mayor (orden AB, al revés de Cochlear)

  def calcularFreqs(self):
    if(self.dx > 0): #Si tengo el dato de la separación de electrodos en un ARRAY PERIMODIOLAR, uso esto.
      for i in range(0,self.Nchann): self.freqsElectrodos.append(Greenwood(self.xi -self.dx*i - MISMATCH))

    if(self.angularInsertion >0): #Si no, uso el dato de la inserción angular
      for i in range(0,self.Nchann): self.freqsElectrodos.append(Greenwood_ang(self.angularInsertion*(self.Nchann-i)/self.Nchann))

  def setearParametros(self):
    if(self.manufacturer == COCHLEAR): self.SR = 16000
    if(self.manufacturer == MEDEL): self.SR = 17000
    if(self.manufacturer == AB): self.SR = 17400
    IMPLANT_SR = self.SR
    self.calcularFreqs() #setea Mismatch
    self.gs = self.channel_interaction_matrix()
    if(not WIN_LEN_AUTO): WIN_LEN_ACE = round(PW*IMPLANT_SR) #analiza en c ciclo

  def channel_interaction_matrix(self):
    N= self.Nchann
    gs = np.zeros([N, N]) #Matriz de interacción de electrodos. Asumo que vienen de grave a agudo.
                          #gs[from][to] guarda el factor de escalamiento para lo que recibe el electrodo "to" al estimular el electrodo "from"
                          #Es una matriz cuadrada. Si la tomo como simétrica (la dispersión de corriente a "izq y der" es la misma, entonces su inversa es una matriz Tridiagonal)

    l = 3.6 #mm, assumed space constant (patente CSSS Medel)

    for e in range(N):
      for ei in range(N):
        if(ei == e): g = 1

        d = abs(e-ei)*self.dx
        if(self.freqsElectrodos[ei] > self.freqsElectrodos[e]): #es más basal
          #g = interaction_basal_gain(np.abs(ei-e)) * CHANNEL_INTERACTION_INDEX
          g = np.e**(-d/l)

        if(self.freqsElectrodos[ei] < self.freqsElectrodos[e]): #es más apical
         # g = interaction_apical_gain(np.abs(ei-e)) * CHANNEL_INTERACTION_INDEX
           g = np.e**(-d/l) * (1-ASYMMETRY_INDEX)
        gs[e][ei] = g
    return gs
    #Podría ajustar el ancho de banda de los filtros que se aplican sobre el ruido blanco como alternativa para simular esto, pero no tendría la asimetría


#Devuelve la frecuencia característica de la posición "x" a lo largo de la membrana basilar, medida en mm desde la base
#asume longitud promedio de 35mm y rangos de audición promedios (G(0) y G(35)). Estudios recientes apuntan a largo promedio de 34.5mm (Danielan et al 2019) pero como es variable dejo este valor estándar
def Greenwood(x):
  return 165.4* ( 10 ** (0.06*(35-x)) - 0.88)

#Devuelve la frecuencia característica del ángulo "a" a lo largo de la membrana basilar, medido en grados desde la base
#Uso largo angular promedio 880°. Promediado de (Danielan et al 2019 y Anandhan 2018)
#--> Ángulo entre 0° y 880°
#No usar, no me está dando bien con los datos de (Anandhan ).
#No da buenos resultados porque esto asume una curva circular, donde el ángulo barrido es proporcional a la distancia recorrida, y en la cóclea no lo es
def Greenwood_ang(a):
  x = a/880*35
  return Greenwood(x)



#############################################################################

#                                   Modelos                                  #

##############################################################################

#MEDEL---------------------------------------------------------------------------
GENERIC_MEDEL1 = Elec_Array(N=12, xi = 31.2, dx=2.4)
GENERIC_MEDEL1.freqsAnalisis = [149,262,409,602,851, 1183,1632,2228,3064,4085,5656,7352]
GENERIC_MEDEL1.name = 'Generic Medel 1'
GENERIC_MEDEL1.manufacturer = MEDEL

GENERIC_MEDEL2 = Elec_Array(N=12, xi = 30.87, dx = 2.18)
GENERIC_MEDEL2.freqsAnalisis = [149,262,409,602,851, 1183,1632,2228,3064,4085,5656,7352]
GENERIC_MEDEL2.name = 'Generic Medel 2'
GENERIC_MEDEL2.manufacturer = MEDEL
GENERIC_MEDEL2.channel1_lowcut = 100

GENERIC_MEDEL3 = Elec_Array(N=12, xi = 28, dx = 23.1/11) #El de Francisco
GENERIC_MEDEL3.freqsAnalisis = [120,235,384,579,836, 1175,1624,2222,3019,4084,5507,7410]
GENERIC_MEDEL3.name = 'Medel Francisco'
GENERIC_MEDEL3.manufacturer = MEDEL
GENERIC_MEDEL3.channel1_lowcut = 70 #FSP = 70Hz, HDCIS = 250Hz

'''
#AB---------------------------------------------------------------------------
GENERIC_AB1 = Elec_Array(N=16)
GENERIC_AB1.freqsAnalisis = [333, 455, 540, 642, 762, 906, 1076, 1278, 1518, 1803, 2142, 2544, 3022, 3590, 4264, 6645]  #fuente: Wolfe , capitulo Programming AB
GENERIC_AB1.channel1_lowcut = 250

GENERIC_AB2 = Elec_Array(N=16) #Igual excepto la primer banda
GENERIC_AB2.freqsAnalisis = [383, 455, 540, 642, 762, 906, 1076, 1278, 1518, 1803, 2142, 2544, 3022, 3590, 4264, 6645]  #fuente: Wolfe , capitulo Programming AB
GENERIC_AB1.channel1_lowcut = 350
'''

#Cochlear ---------------------------------------------------------------------------
NUCLEUS_22 = Elec_Array(N=22, dx = 0.75)
freqTable22 = [[188,313], [313,438], [438, 563], [563, 688], [688, 813], [813,938], [938, 1063], [1063, 1188], [1188, 1313], [1313, 1563], [1563, 1813], [1813, 2063], [2063, 2313], [2313, 2688], [2688, 3063], [3063, 3563], [3563, 4063], [4063, 4688], [4688, 5313], [5313, 6063], [6063, 6938], [6938, 7938]  ] #fuente: Wolfe , capitulo Programming  Nucleus
#freqTable22 = freqTable22[::-1]

#Prototipo como el Implante Freedom (CI24RE) + Contour Advance + N6
GENERIC_COCHLEAR1 = Elec_Array(N=22, xi= 19, dx = 15/21)
GENERIC_COCHLEAR1.freqsAnalisis = freqTable22
GENERIC_COCHLEAR1.name = 'Generic Cochlear 1'
GENERIC_COCHLEAR1.manufacturer = COCHLEAR
# Se corresponde a la Frequency Table #22, la tabla por defecto para Cochlear

GENERIC_COCHLEAR1b = Elec_Array(N=19, xi = 19, dx =15/21)
GENERIC_COCHLEAR1b.freqsAnalisis = [[188,313], [313,438], [438, 563], [563, 688], [688, 813], [813,938], [938, 1063], [1063, 1313], [1313, 1563], [1563, 1813], [1813, 2188], [2188, 2563], [2563, 3063], [3063, 3563], [3563, 4188], [4188, 4938], [4938, 5813], [5813, 6813], [6813, 7938]  ] #fuente: Wolfe , capitulo Programming  Nucleus
#GENERIC_COCHLEAR1.freqs = [250, 375, 500, 625, 750, 875, 1000, 1188, 1438, ... ] frecuencias centrales
# Se corresponde a la Frequency Table #22 con menos electrodos activos

#Prototipo con el array Slim Straight (no usar aun)
GENERIC_COCHLEAR2 = Elec_Array(N=19, angularInsertion = 435)
GENERIC_COCHLEAR2.freqsAnalisis = freqTable22