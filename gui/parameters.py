##Parámetros y Constantes
IMPLANT_SR = 16000 #se setea abajo
OUT_SR = 96000

#MAXIMA (para estrategia ACE)
MAXIMA = 8 #Dejar como 0 para usar todos los canales disponibles

#MISMATCH: Corrimiento extra en la cóclea (hacia la base medido en mm)
MISMATCH = 0

#DISPERTION = Parámetro que uso para simular el "broadness" de la región del excitación de los electrodos.
#0 = Filtro angosto
#1 = Filtro de electrodo a electrodo (media geométrica)
#2 = Filtros cada 2 electrodos aprox
#Toma float >= 0
DISPERTION = 1

#Extracción de envolvente: Método Rectify+LP (Cochlear)
ENVELOPE_FC = 200
ENVELOPE_FULLWAVE = True
#Extracción de envolvente: Método Hilbert (Medel)

#MODO DE SINTESIS
INTERLEAVED = 1 #Es ACE, pero con estimulación interleaved
ACE = 2       #Es ACE, pero estimulando todo en paralelo al mismo tiempo
CONTINOUS  = 3 #Es oomo modo ACE, pero usando todos los canales disponibles
MODE = INTERLEAVED

#ESTIMULACION
PW  = 0 #de cada electrodo, en segundos . Debe ser menor a 1/(n*pps). Dejar como 0 para que se asigne al máximo posible50*(10**-6).
PPS = 0 #al menos 4 veces la frec de corte del filtro de envolvete si se usa en un caso real.
WIN_LEN_ACE = 500 #Solo para debuggear. En ms. Lo correcto debería ser por ciclo?
WIN_LEN_AUTO = False #Desactive el debugeo al setear los parametros del array

#Usar esta funcion para setear el pps y pw, que indica los límites de "seguridad" y da info
def SETEAR_PPS(pps, pw = 0):
  global PPS, PW
  #Lo correcto es setear el pps primero y dejar pw como un parámetro con restricción. Para este caso, elijo un pw demasiado grande, irreal, pero que dé un efecto audible
  #En este caso elijo que pw abarque todo el tiempo de 1/n.pps
  PPS = pps
  PW = pw
  if(MODE == INTERLEAVED and 1/(MAXIMA*PPS) < PW):
    print('ERROR: Ancho de pulso muy grande para la frecuencia especificada.')
    print('El ancho de pulso máximo para la frecuencia de ' + str(PPS) + ' pps es de ' + str(round(1000000/MAXIMA/PPS,2)) +'us' )
  if(pw == 0): PW = 1/(MAXIMA*PPS)
  print('Samples por pulso: ' + str(round(PW*OUT_SR)))
  print('Pulse width: ' + str(round(PW*1000000)) + 'us')

SETEAR_PPS(800)


#CROSSTALK
CHANNEL_INTERACTION_INDEX = 1 #Qué tanta interacción incluyo. 0 = Nada. Es un "control de ganancia" del efecto
                              #A partir de la versión 4, en "1" toma valor "normalizado" según estudios (patente CSSS de Medel).
                              #Tambien a partir de v4 hay que recalcular los coeficientes de interacción al cambiar este parámetro (llamar a "array.setearParametros()")
ASYMMETRY_INDEX = 0 #qué tanto más se filtra hacia los electrodos basales que apicales.
                      # 0 = se filtra en ambas direcciones por igual.
                      # 1 = se filtra solo en direccion basal.
                      #Retomado en la v4


#PREPROCESAMIENTO ADICIONAL (TODO)
ADRO = False
ASC  = False
WNR = False
SNR_NR = False

#COMPRESION DEL RANGO DINÁMICO (valores globales)
T_SPL = 25 # (from 9 to 50 dB SPL) . 25 = Default
C_SPL = 65 # (from 65 to 84 dB SPL)  65 = Default
IIDR = C_SPL - T_SPL
VOLUME_LEVEL = 1
SENSITIVITY = 6 # ranges from a minimum of “1” to a maximum of “20,” may be adjusted by the recipient (if the audiologist provides the recipient with control over the sensitivity parameter), or it may be set to a fixed level by the audiologist. The default sensitivity setting is “12,” which results in the IIDR being positioned from 25 dB SPL (T-SPL) to 65 dB SPL (C-SPL).


#FABRICANTES
COCHLEAR = 'Cochlear'
MEDEL = 'Med-El'
AB = 'Advanced Bionics'

#############################################################################

#                                   Linkeo a GUI                            #

##############################################################################

DISPERTION = 0
MAXIMA = 8
MISMATCH = 0
ENVELOPE_FC = 200
INTERACTION_INDEX = 1
ASYMMETRY_INDEX = 1




MAXIMA_ID = 0
DISPERTION_ID = 1
MISMATCH_ID = 2
INTERACTION_INDEX_ID = 3
ASYMMETRY_INDEX_ID = 4
ENVELOPE_FC_ID = 5
N_PARAM = 6



PARAM_NAMES = [None] * N_PARAM
PARAM_NAMES[MAXIMA_ID] = 'Maxima: '
PARAM_NAMES[DISPERTION_ID] = 'Dispersión de canal: '
PARAM_NAMES[MISMATCH_ID] = 'Corrimiento (mm): '
PARAM_NAMES[INTERACTION_INDEX_ID] = 'Interacción: '
PARAM_NAMES[ASYMMETRY_INDEX_ID] = 'Asimetría de interacción: '
PARAM_NAMES[ENVELOPE_FC_ID] = 'FC LP: '


###########################     ELEC ARRAYS                ##################################################

from elec_arrays import *
ElecArrayNames = ['Medel - Sonnet 2', 'Cochlear - Nucleus 7']
ElecArrayDic = { ElecArrayNames[0]: GENERIC_MEDEL3, ElecArrayNames[1]: GENERIC_COCHLEAR1}