from parameters import *


def envelope_extraction(s, fc, fullwave): #Modo Filtro
  envelope = np.zeros(len(s))
  if(fullwave):
    for i in range(len(s)): envelope[i] = abs(s[i])

  else: #half_wave
    for i in range(len(s)): envelope[i] = max(0., s[i])

  #Low - Pass: Butter de 2do orden
  sos = signal.butter(1, 1200, 'lowpass', fs=IMPLANT_SR, output='sos')
  envelope = signal.sosfilt(sos, envelope)

  return envelope

def envelope_Hilbert(x): #Modo Hilbert
  n = len(x)
  Z = np.zeros(n, dtype='complex')
  X = fft(x)
  for i in range(1,n//2): Z[i] = 2.*X[i]
  Z[n//2] = X[n//2]
  z = ifft(Z)
  env = np.abs(z)
  return env

#Genera una señal de ruido blanco de n samples
def wnoise_sig(n):
   return 2*(np.random.rand(n) - .5) #ruido del mismo largo de la señal

#Genera un tono puro de frecuencia f, duracion en segundos
def puretone(f, dur, sr):
  return [np.sin(2*pi*f*i/sr) for i in range(round(sr*dur))]



'''
Toma una señal y un array de electrodos, y le aplica filtros pasabanda en paralelo
Si "analisis==True" el centro de los filtros es de los de análisis del procesador
Si no, entra en modo resíntesis y el centro de los filtros es el de las frecuencias características estimadas de cada electrodo
Devuelve un array con las señales filtradas
'''
def filter_bank_CIS(s, elec_array, orden = 6, analisis = True, fs = IMPLANT_SR):
  N = elec_array.Nchann

  #frecuencias centrales de los filtros:
  if(analisis):
    freqs = elec_array.freqsAnalisis #Etapa de analizar la señal entrante

  else:
    freqs = elec_array.freqsElectrodos #Etapa de simular la estimulación de los electrodos ("resintesis")

  #Out (array con todas las señales filtradas)
  filtered_bank = []

  if elec_array.channel1_lowcut != None: fizq = elec_array.channel1_lowcut
  else: fizq = 150 # freq izq de la primer banda, la asumo

  #Todo: Que el primer low cut sea mucho más pronunciado

  #e1 --> N-1
  for i in range(N-1):

    #Si el array ya me da las frecuencias exactas del implante, voy con esas
    if(type(freqs[i]) in [type([0,1]), type(np.array([0,1]))] ):
      f1 = freqs[i][0]
      f2 = freqs[i][1]

    #sino, las calculo:
    else:
      fc = freqs[i]
      fder = freqs[i+1]

      '''
      MODO INTERVÁLICO:
       Así, el ancho de banda de los filtlros se calcula en base a los intervalos y no a la distancia entre frecuecienias
       Ej: Si las frecuencias centrales son 100 200 300,   el filtro del medio va a tener banda de paso [141, 245],  ya que el intervalo 141/100 = 200/141
       A mi entender sería mejor así, pero no es lo que se usa
      '''
      if(not analisis): #resíntesis
        c = DISPERTION/2
        eps = 0.5 #Por si DISPERTION == 0
        f1 = fc**(1-c) * fizq**c - eps
        f2 = fc**(1-c) * fder**c + eps
        #f1 = np.sqrt(fc*(fizq))
        #f2 = np.sqrt(fc*(fder))
        #Todo: Afectar tambien al orden?

      '''
      MODO LINEAL:
       Si las frecuencias centrales son 100, 200, 300, filtro del medio va a tener banda de paso [100,300]
       O sea, hay un overlaping mucho mayor entre bandas haciendolo de esta manera que de la otra
      '''
      if(analisis):
        # Posible Q = 3 =  fc/BW  (fuente: Patente de CSSS). Pero da anchos muy angostos
        # TODO: Hacer pruebas con esto.
        f1 = (fizq + fc)/2
        f2 = (fc + fder)/2
        fizq = fc
    #TODO: A los de Medel aumentarles el overlap


    sos = signal.butter(orden/2, [f1,f2], 'bandpass', fs=fs, output='sos') #divido por 2 porque la implementación pide la cantidad de secciones de orden 2 para filtros BP
    filtered_bank.append(signal.sosfilt(sos, s))

  #eN --> Nyquist

  if(type(freqs[N-1]) in [type([0,1]), type(np.array([0,1]))] ): #Si es otro pasabanda:
    f1 = freqs[N-1][0]
    f2 = freqs[N-1][1]
    sos = signal.butter(orden/2, [f1,f2], 'bandpass', fs=fs, output='sos') #divido por 2 porque la implementación pide la cantidad de secciones de orden 2 para filtros BP
    filtered_bank.append(signal.sosfilt(sos, s))

  else:  #sino: Pasaaltos
    sos = signal.butter(orden, freqs[-1], 'highpass', fs=fs, output='sos')
    filtered_bank.append(signal.sosfilt(sos, s))

  return filtered_bank

#Resamplea x de la frecuencia de sampleo fs1 a fs2
def resample(x, fs1, fs2):
  n = round(len(x)*fs2/fs1)
  return signal.resample(x, n)

def compress_log(s):
  return Y

def compress_power(s):

  return Y

def compress_envelope(s):
  return s


'''CHANNEL INTERACTION '''


def channel_interaction_CONTINOUS(filtered_noises, elec_array):
  interacted_channels = filtered_noises.copy()
  N= elec_array.Nchann

  for e in range(N):
    for ei in range(N):
      interacted_channels[ei] += filtered_noises[e]*elec_array.gs[e][ei]*CHANNEL_INTERACTION_INDEX
  return interacted_channels

#gain del crosstalk a "de" electrodos hacia la base. Viejo
def interaction_basal_gain(de):
  return 10.**(-de)

#gain del  crosstalk a "de" electrodos hacia el apex. Viejo
def interaction_apical_gain(de):
  return 1/(10*(de**3)) #sería más correcto una exponencial como tenía antes, con una base algo menor a 10?

##############################################################################################
#                             CIS,  ACE,  FSP                                               ##
###############################################################################################

def simulate_CIS(envs, elec_array):

  # 1- Asigno bandas de análisis a posiciones en la cóclea
  Nchann = elec_array.Nchann
  n = round(len(envs[0])*OUT_SR/IMPLANT_SR)
  out = np.zeros(n)

  #Resampleo las envolventes a la frecuencia de las señales filtradas
  #Resampleo s a algo que permita representar todo el rango audible. Elijo 48khz por ser multiplo entero de 16khzre
  for e in range(Nchann): envs[e] = resample(envs[e], IMPLANT_SR, OUT_SR)

  #Paso ruido blanco por los mismos filtros pasabanda y que las envolventes modulen su amplitud
  wnoise = wnoise_sig(n)
  filtered_noises = filter_bank_CIS(wnoise, elec_array, 6, analisis = False, fs = OUT_SR)

  # 2- Simulo la interacción de canales (ya sobre el "medio físico")
  # Podría ajustar el ancho de banda de los filtros que se aplican sobre el ruido blanco como alternativa para simular esto, pero no tendría la asimetría
  #Esto es valid para modo Continous, pero no para interleaved


  # 3 - Mezclo los canales paralelos a uno solo
  if(MODE == CONTINOUS):  #Ruido blanco modulado
    out = np.zeros(n)
    interacted_channels = channel_interaction_CONTINOUS(filtered_noises, elec_array)
    for c in range(Nchann): out += interacted_channels[c] * np.array(envs[c])
    return out

  #Maxima (simulacion de ACE)
  #Igual a CONTINOUS cuando MAXIMA está seteado a 0
  #Ojo que tecnicamente, m = #electrodos = N_chann en el nombre n-m, y yo los nombro al revés
  # m = cantidad de canales a estimular
  if(MAXIMA == 0): m = Nchann
  if(MAXIMA >  0): m = MAXIMA


  #Modo ACE continuo: Simplemente CIS continuo con menos canales
  if(MODE == ACE):
    return simulate_CIS_ACE(envs, filtered_noises, elec_array, n, m)

  #Modo Interleaved: Simulo la estimulación secuencial (Y aplica  n of m = ACE)
  #TODO: Probar la alternativa de implementar CONTINOUS, y hacer 0 los otros canales de a momentos.
  if(MODE == INTERLEAVED):
     return simulate_CIS_Interleaved(envs, filtered_noises, elec_array, n,m)

  return

'''
Nota: Así como están ahora estos modos a partir de v3, son más fieles que en la versión 2
Un buen experimento a hacer sería comparar el cambio entre las dos versiones (basicamente, cambia el modo de aplicar channel interaction)
entre esta manera más fiel y la otra más naive, a ver si justifica la fidelidad contra tiempo de ejecucion.
'''
def simulate_CIS_ACE(envs, filtered_noises, elec_array, n, m):
    out = np.zeros(n)
    gs = elec_array.gs

    WIN_SIZE = round(WIN_LEN_ACE * OUT_SR/1000) #Parámetro SÚPER arbitrario de largo de ventana de análisis, que elijo en 15ms
    i = 0

    while(i<n):
      #Extraigo las envolventes de mayor amplitud
      amplitudes_promedio = [sum(np.array(envs[c][i: i+WIN_SIZE]**2)) for c in range(elec_array.Nchann)] #Tomo la amplitud promedio en el ciclo de estimulación de cada envolvente
      indices_max = np.argpartition(amplitudes_promedio, -m)[-m:] #Indices de las envolventes de mayor amplitud

      #Estimulo bandas maximas
      for max_channel in indices_max:
        out[i: i+WIN_SIZE] += filtered_noises[max_channel][i: i+WIN_SIZE] * envs[max_channel][i: i+WIN_SIZE]

        #Simulo channel interaction:
        if(CHANNEL_INTERACTION_INDEX > 0):
          for other_channel in range(elec_array.Nchann):
            if(other_channel == max_channel): continue
            out[i:i+WIN_SIZE] += filtered_noises[other_channel][i:i+WIN_SIZE] * envs[max_channel][i:i+WIN_SIZE]*gs[max_channel][other_channel]

      i+=WIN_SIZE

    return out

def simulate_CIS_Interleaved(envs, filtered_noises, elec_array, n,m):
  i = 0
  pwn = round(PW*OUT_SR) #samples en cada pulso
  #pwn = round(1/m/PPS) #samples activos en cada pulso
  gs = elec_array.gs
  out = np.zeros(n)

  while(i+pwn<n):

    #Para acelerar: Si no hace falta buscar los máximos (n == m en n of m), no los busco
    if(m<elec_array.Nchann):
      #Extraigo las envolventes de mayor amplitud
      #amplitudes_promedio = [sum(envs[c][i:i+pwn]) for c in range(N_chann)] #Tomo la amplitud promedio en el ciclo de estimulación de cada envolvente
      amplitudes_promedio = [sum(np.array(envs[c][i:i+pwn]**2)) for c in range(elec_array.Nchann)]
      indices_max = np.argpartition(amplitudes_promedio, -m)[-m:] #Indices de las envolventes de mayor amplitud
    else: indices_max = range(elec_array.Nchann)

    for max_channel in indices_max:
      #if(len(interacted_channels_maximos[c][fr: to])<pwn): continue  #LLegué al final de la señal   (todo: filtered_noises?)

      fr = i+max_channel*pwn
      to = i+(max_channel+1)*pwn

      out[fr: to] = filtered_noises[max_channel][fr: to] * envs[max_channel][fr: to]

      #Simulo channel interaction:
      if(CHANNEL_INTERACTION_INDEX>0):
        for other_channel in range(elec_array.Nchann):
          if(other_channel == max_channel): continue
          out[fr:to] += filtered_noises[other_channel][fr:to] * envs[max_channel][fr:to]*gs[max_channel][other_channel]


    i+=m*pwn

  return out

"""Funciones gráficas/experimentación"""

#Analisis es True para señales de entrada o False para señales de salida
def plot_stft(x, elec_array, analisis=False, show_black_and_white=False, mini = False):

  x = np.array(x)

  #Espectro
  x_stft = np.abs(librosa.stft(x, n_fft=2048)) #hop = n_fft//4
  x_stft_db = librosa.amplitude_to_db(x_stft, ref=np.max)
  n_frames = len(x_stft_db[0])

  #Grafico
  fig, ax = plt.subplots()
  ax.set_title('Power spectrogram')
  if(mini): fig.set_size_inches(8, 4)
  else: fig.set_size_inches(15, 7)
  #ax.set_ylim([0, 1])

  #INPUT SIGNAL:
  if(analisis): #Mostramos las frecuencias de analisis
    if(show_black_and_white):
     librosa.display.specshow(data=x_stft_db, y_axis='log', x_axis = 'time',ax=ax,
                             sr=IMPLANT_SR, cmap='gray_r')
    else:
      img = librosa.display.specshow(data=x_stft_db, y_axis='log', x_axis = 'time',ax=ax, sr=IMPLANT_SR)
      plt.colorbar(img, ax= ax, format='%+2.0f dB')


    for f in elec_array.freqsAnalisis:  #Agregamos lineas horizontales en las frecuencias centrales de los electrodos del array
      lineaX = [512*i/OUT_SR for i in range(n_frames)] #fftsize//4
      lineaY = [f for _ in range(n_frames)]
      plt.plot(lineaX, lineaY, '-b')

 #OUTPUT SIGNAL:
  if(not analisis): #Mostramos las frecuencias de los electrodos
    if(show_black_and_white):
      librosa.display.specshow(data=x_stft_db, y_axis='log', x_axis = 'time',ax=ax,
                              sr=OUT_SR, cmap='gray_r')
    else:
      img = librosa.display.specshow(data=x_stft_db, y_axis='log', x_axis = 'time',ax=ax, sr=OUT_SR)
      plt.colorbar(img, ax= ax, format='%+2.0f dB')

    for f in elec_array.freqsElectrodos: #Agregamos lineas horizontales en las frecuencias centrales de los electrodos del array
      lineaX = [512*i/OUT_SR for i in range(n_frames)] #fftsize//4
      lineaY = [f for _ in range(n_frames)]
      plt.plot(lineaX, lineaY, '-r')

  plt.show()
  return fig, ax


def logear_experimento(nombre, s, elec_array):
  return
  #Exportar txt con nombre del experimento y parámetros, audio de salida, etc


"""Definimos CIS

(Cuando "MAXIMA < #canales", se convierte en ACE)
"""

def CIS(s, elec_array):
  N = elec_array.Nchann

  # 0 - Resampleo a 16khz - Hecho al cargar el audio
  #s = resample(s, sr_in, IMPLANT_SR)

  # 0b - Seteo parámetros del implante
  elec_array.setearParametros()

  # 1 - Pre-énfasis
  b, a = signal.butter(1, 1200,btype = 'highpass', fs = IMPLANT_SR , output='ba')
  zi = signal.lfilter_zi(b, a)
  s, _ = signal.lfilter(b, a, s, zi=zi*s[0])

  #2 - Banco de filtros pasabanda de análisis
  filtered_bank = filter_bank_CIS(s, elec_array, 6)

  #3 - Extracción de envolventes
  if(elec_array.manufacturer == COCHLEAR): envelopes = [envelope_extraction(filtered_bank[i], ENVELOPE_FC, ENVELOPE_FULLWAVE) for i in range(N)] # CIS convencional
  if(elec_array.manufacturer == MEDEL): envelopes = [envelope_Hilbert(filtered_bank[i]) for i in range(N)] # "CIS+"

  #4 - Compresión del rango dinámico
  compressed_envelopes = [compress_envelope(envelopes[i]) for i in range(N)]

  #5 - Aplicamos CIS

  #Aquí ocurre:
  #5.1 Asignación de bandas a electrodos + Mismatch
  #5.2 - Channel Interaction (crosstalk)
  out = simulate_CIS(envelopes, elec_array)


  return out

"""FSP"""

#Recibe una señal y genera tramos de senoidales que se ajusten a los zero-crossing
#A diferencia de lo que hace el implante, yo elegí tomar pares de zero crossings en vez de solo los que sean
#rising de neg a pos.
#¿Hace mucha diferencia? No lo sé. Lo elegí por un tema de pragmatismo a la hora de implementar

#Observacion: Algo más sofisticado, sería aprovechar que sen(x) \approx x cuando x \approx 0,
# Y entonces estimar los valores de x,
#Para tener yo un valor estimado del período mucho más fino a la hora de hacer la resíntesis
#Simplemente porque el implante no lo hace, entonces yo tampoco
def track_from_zero_crossings(s, continous_phase = True):
  s0 = [1 if s[i] > 0 else -1 for i in range(len(s))] #señal de signos
  out = np.zeros(len(s0))
  i=0
  phi = 0 #fase
  if(s[0] <0): phi = pi
  while i <len(s0):
    i0 = i
    i+=1 #Importante: Este +1 tiene que estar al inicio, no al final del loop. Sino genera una distorsión (que puede ser interesante en otro contexto) al dejar samples seteados en 0 en cada ciclo

    #Busco primer zero-crossing
    while(i <len(s0) and
          s0[i]*s0[i-1]>0): i+=1
    if( i>= len(s0)): break
    i+=1

    #Busco segundo zero-crossing
    while(i <len(s0) and
          s0[i]*s0[i-1]>0): i+=1
    di = i-i0 #Período en samples (sin interpolar)

    if continous_phase:
      for j in range(i0, i): #Lleno un período
        out[j] = sin(phi)
        phi += 2*pi/di  #Seria lo mismo que el "else" con range(0,di) en vez de ese range

    else:
      for j in range(i0, i): out[j] = sin(2*pi*j/di) #Lleno un período

  return out
#Guardo el parámetro "Continous_phase" porque me pregunto si, el ruido que resulta al dejarlo en false,
#no es similar al ruido que escucha un implantado con este método. Queda a definir

def FSP(s, elec_array):
  out = s
  return out
#Entre 70 y 350Hz
#Elijo este método: En los canales con CSSS (Elijo los primeros 3, según datos de calibración de Francisco) sumo en paralelo la señal "sinusoidal" que daría el método,
#al ruido original
#O sea, replico el método CSSS a mano en el paso de resíntesis
#Esto se logra disparando un pulso en cada zero crossing.
#De esta forma, simulo la parte espacial (electrodo y ruido) y temporal fina (csss y zero-crossings)


#La razón por la que elijo implementar el método de zero-crossings igual, a pesar de que para tonos simples podría resolverlo
#sumando la señal filtrada en paralelo, es que cuando hay más de un tono que cae en la misma banda,
#los zero crossing no dan un patrón de repetición acorde a una frecuencia fundamental "buena"