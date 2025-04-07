##IMPORT MODULES - GUI
import sys
import time
import threading #Llamar a la funcion cuando un audio se apaga (no hace falta, se puede hacer desde "progressbar"
import re
import struct
from tkinter import (Tk, TclError, Frame, Label, Button,
                     Radiobutton, Scale, Entry, ttk,
                     filedialog, IntVar, StringVar)
import tkinter as tk
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt #progressbar
from matplotlib.animation import FuncAnimation #progressbar
import sounddevice  #playback

#Importo otros archivos del mismo directorio
#todo: Cambiar al final por FIle




## Processing:
import numpy as np
from numpy import pi, sin, cos, abs
from scipy.fft import fft, ifft
from scipy.io import wavfile
from scipy.signal import convolve,correlate,fftconvolve,lfilter
from scipy import signal
import librosa
