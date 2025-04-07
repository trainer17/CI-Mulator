import os
#os.chdir(r'C:\Users\Graciela\Desktop\Cochlear Implants\CodeGUI')
from imports import *
from parameters import *
from elec_arrays import *
from Processing import *


##Interfaz Gráfica
class TkMplSetup():

    def __init__(self, root):

        ##Constructor propiamente dicho
        self.root = root
        self.root.geometry('800x500')
        self.root.protocol('WM_DELETE_WINDOW', self.CLOSE)  #Le digo que código usar cuado se cierra la ventana


        self.root.title("Simulador de Implantes Cocleares")
        self.root.columnconfigure(0, weight=1)

        #Habilitamos y creamos pestañas
        self.tabsystem = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.tabsystem)
        self.tab2 = ttk.Frame(self.tabsystem)

        self.tabsystem.add(self.tab1, text = 'Principal')
        self.tabsystem.add(self.tab2, text = 'Opciones')
        self.tabsystem.pack(expand=1, fill="both")


        ##Variables de control
        self.sr = 0 #A determinar del audio que se levante
        self.originalSignal = None #Mono
        self.processedSignal = None  #Mono
        self.originalSignalPath = StringVar()
        self.dur = 0 #segundos
        self.time_progress = 0 #Tiempo transcurrido de playback

        ##Sección de control

        #ElecArrays
        self.selectedElecArrayName = StringVar()
        self.selectedElecArray = None
        #self.selectedElecArrayName.set(string 1) # set the default option


        #Señales por defecto
        self.defaultSignalNames= {'Diálogo 1 (Español)', 'Diálogo 2 (Inglés)', 'Melodía', 'Música','Percusión'}
        self.selectedDemoSignalName = StringVar()


        self.signalName = StringVar() #Nombre


        self.outStream = sounddevice.OutputStream()
        self.playImg = None
        self.stopImg = None
        self.recImg = None
        self.playing = False

        ##VARIABLES Solapa 2
        self.paramVals = [None] * N_PARAM
        self.paramTxts = [None]*N_PARAM
        self.paramControls = [None] * N_PARAM


        ##SECCIÓN DE GRAFICOS
        self.upperFrame =Frame(self.tab1)
        self.upperFrame.grid(row=0, column = 0)

        self.middleFrame =Frame(self.tab1)
        self.middleFrame.grid(row=1, column = 0)

        self.lowerFrame = Frame(self.tab1)
        self.lowerFrame.grid(row = 2, column = 0)




        ##CREAR BOTONES Y ELEMENTOS
        #Todo: Inicializar en none los usados
        self.crearElementos1() #Primer pestaña
        self.crearElementos2() #Segunda pestaña



    ##Dropdowns
    def crearElementos1(self):

        texto1 = tk.Label(self.upperFrame,text="Simulador de implantes cocleares")

        texto1.grid(column=1, row=0, padx=40, pady=40)

        ##Dropdown - Modelo de implante
        Label(self.upperFrame, text="Seleccionar modelo de implante:").grid(row = 1, column = 1)
        elecDropdown = tk.OptionMenu(self.upperFrame, self.selectedElecArrayName, *ElecArrayNames, command = self.setearElecArray)
        elecDropdown.grid(row = 1, column = 2)


        ##Dropdown - Audios de ejemplo precargados
        dropdown2 = tk.OptionMenu(self.middleFrame, self.selectedDemoSignalName, *self.defaultSignalNames,
                                    command =  self.openAudioEjemplo).grid(row = 1, column = 2)
        Label(self.middleFrame, text="Audios de ejemplo:").grid(row = 1, column = 1)

        ##File Select - Audio a cargar
        tk.Button(self.middleFrame, text='Seleccionar archivo de audio', command=self.openFile).grid(row = 2, column= 2, pady = 20)


        ##String - Audio seleccionado:
        Label(self.middleFrame, text="Audio Seleccionado:").grid(row = 3, column = 1)
        Label(self.middleFrame, textvariable=self.signalName).grid(row = 3, column = 2, columnspan=10)


        ##Imagenes de Botones
        from PIL import Image, ImageTk #Con esto puedo resizear la imagen

        #Play
        image = Image.open(r"playButton.png")
        image = image.resize((20,20))
        self.playImg = ImageTk.PhotoImage(image)

        #Stop
        image = Image.open(r"stopButton.png")
        image = image.resize((20,20))
        self.stopImg = ImageTk.PhotoImage(image)

        #Rec
        image = Image.open(r"recButton.png")
        image = image.resize((20,20))
        self.recImg = ImageTk.PhotoImage(image)

        ##Button - REC Button
        Label(self.middleFrame, text = 'Micrófono:', font = ('Verdana', 12)).grid(row = 4, column= 0, pady = 20, padx=20)
        self.recButton = tk.Button(self.middleFrame, text='Reproducir original', command=self.recMic, image = self.recImg)
        self.recButton.grid(row = 4, column= 1, pady = 20, padx=20)




        ##Button - Play Original Signal
        Label(self.lowerFrame, text = 'Audio original:', font = ('Verdana', 12)).grid(row = 0, column= 0, pady = 20, padx=20)
        self.playOriginalButton = tk.Button(self.lowerFrame, text='Reproducir original', command=self.playOriginal, image = self.playImg)
        self.playOriginalButton.grid(row = 0, column= 1, pady = 20, padx=20)

        ##Button - Play Processed Signal
        Label(self.lowerFrame, text = 'Simulación:', font = ('Verdana', 12)).grid(row = 0, column= 2, pady = 20, padx=20)
        self.playProcessedButton = tk.Button(self.lowerFrame, text='Reproducir original', command=self.playProcessed, image = self.playImg)
        self.playProcessedButton.grid(row = 0, column= 3, pady = 20, padx=20)

        self.processedTexto = tk.Label(self.lowerFrame,text="Seleccione una señal...")
        self.processedTexto .grid(column=3, row=1, padx=40, pady=40)

        ##Progressbar

        self.fig, self.ax = plt.subplots(figsize=(5, 4))   #Progressbar
        self.start_time = 0

        volume_outer_frame = Frame(self.middleFrame, bd=1, relief='groove')
        volume_outer_frame.grid(
            row=2, column=0, sticky='ew', pady=(2, 15))


        Label(volume_outer_frame, text='Time').grid(
            row=0, column=1, stick='w', pady=(2, 4), padx=(20, 0))

        self.time_progress = ttk.Progressbar(volume_outer_frame,
                                             orient='horizontal',
                                             length=100,
                                             mode='determinate' #relative progress - sé cuanto dura el audio
                                            )
        self.time_progress.grid(
            row=1, column=1, sticky='w', pady=(0, 10), padx=(20, 0))



    def crearElementos2(self):

        texto2 = tk.Label(self.tab2, text="Opciones avanzadas")
        texto2.grid(column=1, row=0, padx=40, pady=10)


        ##Tipo de datos de parametros
        self.paramVals[DISPERTION_ID] = tk.DoubleVar()
        self.paramVals[MAXIMA_ID] = tk.IntVar()
        self.paramVals[MISMATCH_ID] = tk.DoubleVar()
        self.paramVals[INTERACTION_INDEX_ID] = tk.DoubleVar()
        self.paramVals[ASYMMETRY_INDEX_ID] = tk.DoubleVar()
        self.paramVals[ENVELOPE_FC_ID] = tk.IntVar()



        ##Controles/Sliders de parámetros
        for param_id in range(N_PARAM): #Generales
            self.paramControls[param_id] = ttk.Scale(self.tab2, from_=0, to=2, orient= 'horizontal', command = self.slider_changed, variable = self.paramVals[param_id])
            self.paramControls[param_id].grid(column = 2, row = param_id+1, sticky = 'w')

            ##Displays de parámetros
            txt = ttk.Label(self.tab2, text = PARAM_NAMES[param_id])
            txt.grid(column = 0, row=param_id+1, sticky = 'w')
            self.paramTxts[param_id] = ttk.Label(self.tab2, text ='')
            self.paramTxts[param_id].grid(column = 1, row=param_id+1, sticky = 'w')


        #Variables especificas:
        self.paramControls[DISPERTION_ID].configure(from_=0, to=2)
        self.paramControls[MAXIMA_ID].configure(from_=6, to=12)
        self.paramControls[ENVELOPE_FC_ID].configure(from_=250, to=400)
        self.paramControls[MISMATCH_ID].configure(from_=-3, to=3)
        self.paramControls[ASYMMETRY_INDEX_ID].configure(from_=0, to=1)



    #Funcion que se llama al tocar los sliders
    def slider_changed(self, event):
        #Cambio el texto de los displays
        for param_id in range(N_PARAM):
            #Si es tipo double, redondeo los decimales
            val =  self.paramVals[param_id].get()
            text = ''
            if(type(val) == type(2.0)):  text ='{: .2f}'.format(val)
            else: text = str(val)
            self.paramTxts[param_id].configure(text = text)

        self.olvidarProcessedSignal()




    def openFile(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(title='Seleccionar archivo de audio')
        self.signalName.set(filename)
        self.selectedDemoSignalName.set('-')

        self.originalSignal, self.sr = librosa.load(filename) #Todo: Hacer mono
        self.olvidarProcessedSignal()



    def openAudioEjemplo(self, temp):
        selectedDemo = self.selectedDemoSignalName.get()
        self.signalName.set(selectedDemo)
        folder = r"demoSignals\\"
        self.originalSignal, self.sr = librosa.load(folder + selectedDemo+'.wav')
        sounddevice.stop() #Si estaba reproduciendo, paro
        self.dur = len(self.originalSignal)/self.sr
        self.olvidarProcessedSignal()


    def playOriginal(self):
        self.playStopSignal(self.originalSignal, self.sr)

    def playProcessed(self):
        if(self.processedSignal is None): self.processSignal()
        if(not (self.processedSignal is None)): self.playStopSignal(self.processedSignal, OUT_SR)



    def processSignal(self):
        if(self.selectedElecArray is None): return tk.messagebox.showinfo("Error",  "Debe seleccionar un modelo de implante antes de hacer la simulación")
        if(self.originalSignal is None):    return tk.messagebox.showinfo("Error",  "Debe seleccionar un archivo de audio antes de comenzar la simulación")

        self.processedTexto.configure(text = "Procesando...")
        root.update()

        self.processedSignal = CIS(self.originalSignal, self.selectedElecArray) #Acá el trabajo pesado

        self.processedTexto.configure(text="¡Procesado!")
        return

    def olvidarProcessedSignal(self):
        self.processedSignal = None #Borro el procesado anterior
        self.processedTexto.configure(text = '')
        self.stopSignal()



    def setearElecArray(self, *args):
        self.selectedElecArray = ElecArrayDic[self.selectedElecArrayName.get()]
        self.olvidarProcessedSignal()


    def recMic(self):
        self.stopSignal()
        self.signalName.set('Grabando...')

        #Llama a stop() de otros audios por defecto, no me ocupo de eso
        self.dur = 3 #Todo: Variable usuario (segundos)
        default_sr = 44100
        self.sr = default_sr
        nsamps = round(self.dur * default_sr)

        #Muestro tiempo en progressbar
        self.start_time = time.time()
        self.start_visualisation()

        self.originalSignal = sounddevice.rec(nsamps, samplerate=default_sr, channels=1, blocking = True)
        #"blocking" hace que se pause todo mientras está grabando

        self.signalName.set('Grabación')
        self.olvidarProcessedSignal()



    def playStopSignal(self, s, sr):

        if(s is None): return tk.messagebox.showinfo("Error",  "Debe seleccionar un archivo de audio")


        try:
            audiostream = sounddevice.get_stream()
            self.playing = audiostream.active
        except:
            self.playing = False #Aún no hay stream de audio


        #Si no está reproduciendo: Empiezo a reproducir
        if not self.playing:

            if(s is self.originalSignal):   self.playOriginalButton.config(text='Stop', image = self.stopImg)
            if(s is self.processedSignal):  self.playProcessedButton.config(text='Stop', image = self.stopImg)


            #Seteo un timer para que cuando termine de reproducirse cambie el texto
            self.dur = len(s)/sr #duracion en segundos
            t = threading.Timer(self.dur, self.stopSignal)   # task will trigger after 60 seconds
            t.start()

            sounddevice.play(s,sr)
            self.playing = True

            #Progressbar:
            self.start_time = time.time()
            self.start_visualisation()

        #Si está reproduciendo: Paro
        else: self.stopSignal()

        return

    def stopSignal(self):#Funcion interna, a llamar cuando haya pasado el tiempo del audio
        sounddevice.stop()
        self.playOriginalButton.config(text='Audio de entrada', image = self.playImg)
        self.playProcessedButton.config(text='Audio de entrada', image = self.playImg)
        #self.time_progress.stop() #Stop progressbar (no hace nada)
        self.playing = False


    ##Cerrar todo
    def CLOSE(self):
        sounddevice.stop()
        #self.outStream.stop()
        # self.audio.terminate()  --> adding this line seems to crash the exit
        #self.root.after(1, self.root.destroy)
        root.quit()
        root.destroy()
       #todo: Descomentar en la versión final
       # sys.exit()


    ##Progressbar - Setup
    def start_visualisation(self):

        INTERVAL = 100  # plot interval in millisecond
        duration_range = np.arange(0, self.dur, INTERVAL / 1000)
        self.start_time = time.time()
        self.pause_time = 0
        #self.time_progress['maximum'] = Lo que quieras. Por default, de 0 a 100
        self.time_progress['value'] = 0 # Valor inicial (redundante por la funcion que llamo, dejo para claridad)

        self.visualisation = FuncAnimation(self.fig,
                                           self.update_frame, #La función a llamar cada frame
                                           frames=duration_range, #array de datos de cada frame de animación
                                           interval=INTERVAL, #delay entre frames (ms)
                                           repeat=False)
        self.root.after(1, self.fig.canvas.draw())


    ##Progressbar - callback
    def update_frame(self, frame):

        if(not self.playing):
            self.time_progress['value'] = 0
            return

        #Progressbar
        elapsed_time = time.time() - self.start_time #en segundos
        self.time_progress['value'] = elapsed_time/self.dur * 100 #la barra toma valores entre 0 y 100

        return





##Procesamiento
class COCHLEAR_SIMULATION(TkMplSetup):

    def __init__(self, root):
        super().__init__(root)
        self.out = ''





##EXECUTE
root = None
def main():
    global root
    root = Tk()

    COCHLEAR_SIMULATION(root)
    root.mainloop()


if __name__ == '__main__':
    main()