#Tomado de acá: https://codereview.stackexchange.com/questions/231930/python-sound-visualizer

import sys
import time
import threading
import re
import struct
from tkinter import (Tk, TclError, Frame, Label, Button,
                     Radiobutton, Scale, Entry, ttk,
                     filedialog, IntVar)
import wave
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import pyaudio


DEFAULT_FREQUENCY = 223  # frequency in Hz
DEFAULT_DURATION = 5.0   # length of sound stream in seconds
INTERVAL = 100           # plot interval in millisecond
PACKAGE_LENGTH = 1024    # number of samples in sound package
VOLUME_RESOLUTION = 0.02 # resolution in volume scale (0 - 1)
FILE_SEARCH = r'^([a-zA-Z]:)?([/|\\].+[/|\\])*(.+$)'

PADY_OUTER = (2, 15)
PADY_INNER_1 = (2, 4)
PADY_INNER_2 = (0, 4)
PADY_INNER_3 = (0, 10)

class TkMplSetup:

    def __init__(self, root):
        self.root = root
        self.root.geometry('800x500')

        self.root.title("Sound Visualiser")
        self.root.columnconfigure(0, weight=1)

        self.volume = 0
        self.duration = DEFAULT_DURATION
        self.running = False
        self.stopped = True
        self.error_message = ''

        self.plot_area()
        self.main_buttons()
        self.control_buttons()

    def plot_area(self):
        plot_frame = Frame(self.root)
        plot_frame.grid(row=0, column=0, sticky='nw')

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        canvas.get_tk_widget().pack()

    def main_buttons(self):
        bottom_frame = Frame(self.root)
        bottom_frame.grid(row=1, column=0, rowspan=2, sticky='new')

        self.start_pause_button = Button(
            bottom_frame, text='Start', command=self.control_start_pause)
        self.start_pause_button.pack(side='left')

        self.stop_button = Button(
            bottom_frame, text='Stop', command=self.stop)
        self.stop_button.pack(side='left')

        self.quit_button = Button(
            bottom_frame, text='Quit', command=self.quit)
        self.quit_button.pack(side='left')

    def control_start_pause(self):
        if self.error_message:
            return

        if self.stopped:
            try:
                self.ax.lines.pop(0)

            except IndexError:
                pass

            if self.selected_type == 1:
                try:
                    self.frequency = int(self.frequency_entry.get())

                except ValueError:
                    self.frequency = DEFAULT_FREQUENCY
                    self.frequency_entry.insert(0, DEFAULT_FREQUENCY)

                except TclError:
                    self.frequency = DEFAULT_FREQUENCY

            if self.selected_type in [1, 2]:
                try:
                    self.duration = float(self.duration_entry.get())

                except ValueError:
                    self.duration = DEFAULT_DURATION
                    self.duration_entry.insert(0, DEFAULT_DURATION)

                except TclError:
                    self.duration = DEFAULT_DURATION

            # minus 1 is a correction to try to get the progress bar right,
            #under investigation
            self.time_progress['maximum'] = 1000 * (self.duration - 1.0)
            self.time_progress['value'] = 0
            self.running = True
            self.stopped = False
            self.start_pause_button.config(text='Pause')
            self.start_visualisation()
            return

        if self.running:
            self.visualisation.event_source.stop()
            self.pause_start_time = time.time()
            self.start_pause_button.config(text='Run')

        else:
            self.pause_time += time.time() - self.pause_start_time
            self.visualisation.event_source.start()
            self.start_pause_button.config(text='Pause')

        self.running = not self.running

    def stop(self):
        try:
            self.visualisation.event_source.stop()
        except AttributeError:
            pass

        self.stopped = True

    def quit(self):
        # add the delays for the processes to stop orderly
        # not sure if really required
        self.stop()
        # self.audio.terminate()  --> adding this line seems to crash the exit
        self.root.after(1, self.root.destroy)
        time.sleep(1)
        sys.exit()

    def control_buttons(self):
        self.control_frame = Frame(self.root)
        self.control_frame.grid(row=0, column=1, sticky='nw')

        self.control_wave_type()
        self.control_sampling_rate()
        self.control_volume_time()

        self.r_type.set(1)
        self.select_type()

    def control_wave_type(self):
        type_outer_frame = Frame(self.control_frame, bd=1, relief='groove')
        type_outer_frame.grid(row=0, column=0, sticky='ew', pady=PADY_OUTER)

        self.r_type = IntVar()

        Label(type_outer_frame, text='Sound type').grid(
            row=0, column=0, stick='w', pady=PADY_INNER_1)

        modes = {'note': 1, 'design': 2, 'file': 3}
        for i, (key, val) in enumerate(modes.items()):
            Radiobutton(type_outer_frame, text=key, width=6,
                        variable=self.r_type, value=val,
                        command=self.select_type).grid(
                            row=1, column=i, stick='w', pady=PADY_INNER_2)

        self.type_frame = Frame(type_outer_frame)
        self.type_frame.grid(
            row=2, column=0, columnspan=3, sticky='w', pady=PADY_INNER_3)

    def select_type(self):
        self.error_message = ''
        self.selected_type = self.r_type.get()

        if self.selected_type == 1:
            self.note_options()

        elif self.selected_type == 2:
            self.design_options()

        elif self.selected_type == 3:
            self.file_options()

        else:
            assert False, f'check selected_type invalid value {self.selected_type}'

        self.select_sampling_display()

    def note_options(self):
        for widget in self.type_frame.winfo_children():
            widget.destroy()

        Label(self.type_frame, text='Frequency').pack(side='left')
        self.frequency_entry = Entry(self.type_frame, width=5)
        self.frequency_entry.insert(0, DEFAULT_FREQUENCY)
        self.frequency_entry.pack(side='left')

        Label(self.type_frame, text='Duration').pack(side='left')
        self.duration_entry = Entry(self.type_frame, width=5)
        self.duration_entry.insert(0, DEFAULT_DURATION)
        self.duration_entry.pack(side='left')

    def design_options(self):
        for widget in self.type_frame.winfo_children():
            widget.destroy()

        Label(self.type_frame, text='Duration').pack(side='left')
        self.duration_entry = Entry(self.type_frame, width=5)
        self.duration_entry.insert(0, DEFAULT_DURATION)
        self.duration_entry.pack(side='left')

    def file_options(self):
        for widget in self.type_frame.winfo_children():
            widget.destroy()

        sound_file = filedialog.askopenfile(
            title='Select sound file',
            filetypes=(('wav files', '*.wav'), ('all files', '*')))

        try:
            file_name = 'Sound file: ' + re.search(
                FILE_SEARCH, sound_file.name).group(3) + '  '

        except AttributeError:
            file_name = '  '

        Label(self.type_frame, text=file_name).pack(anchor='w')

        if file_name:
            try:
                w = wave.open(sound_file.name)
            except (wave.Error, EOFError, AttributeError):
                self.error_message = 'Invalid wav file'
                Label(self.type_frame, text=self.error_message).pack(anchor='w')
                return

            frames = w.getnframes()
            channels = w.getnchannels()
            sample_width = w.getsampwidth()
            self.fs = w.getframerate()
            self.sound_byte_str = w.readframes(frames)
            self.duration = frames / self.fs * channels

            if sample_width == 1:
                self.fmt = f'{int(frames * channels)}B'

            else:
                self.fmt = f'{int(frames * channels)}h'

            print(f'frames: {frames}, channels: {channels}, '
                  f'sample width: {sample_width}, framerate: {self.fs}')

    def control_sampling_rate(self):
        sampling_outer_frame = Frame(self.control_frame, bd=1, relief='groove')
        sampling_outer_frame.grid(
            row=1, column=0, sticky='ew', pady=PADY_OUTER)

        Label(sampling_outer_frame, text='Sampling frequency').grid(
            row=0, column=0, stick='w', pady=PADY_INNER_1)

        self.sampling_frame = Frame(sampling_outer_frame)
        self.sampling_frame.grid(row=1, column=0, stick='w', pady=PADY_INNER_3)

    def select_sampling_display(self):
        if self.selected_type in [1, 2]:
            self.display_sampling_options()

        elif self.selected_type == 3:
            self.display_sampling_rate()

        else:
            assert False, f'control sampling rate for selected_type {self.selected_type}'

    def display_sampling_options(self):
        for widget in self.sampling_frame.winfo_children():
            widget.destroy()

        self.r_fs = IntVar()
        self.r_fs.set(12)
        self.select_fs()

        modes = {'2048': 11, '4096': 12, '8192': 13,
                 '16384': 14, '32768': 15}
        for i, (key, val) in enumerate(modes.items()):
            Radiobutton(self.sampling_frame, text=key, width=6,
                        variable=self.r_fs, value=val,
                        command=self.select_fs).grid(
                            row=int(i / 3), column=(i % 3), sticky='w')

    def select_fs(self):
        self.fs = 2**self.r_fs.get()
        self.ax.set_xlim(1000 * PACKAGE_LENGTH / self.fs, 0)
        self.fig.canvas.draw()

    def display_sampling_rate(self):
        for widget in self.sampling_frame.winfo_children():
            widget.destroy()

        Label(self.sampling_frame, text=f'Sampling rate: {self.fs} Hz').grid(
            row=0, column=0, stick='w')

        Label(self.sampling_frame, text=f'Duration: {self.duration:.1f} seconds').grid(
            row=1, column=0, stick='w')

    def control_volume_time(self):
        volume_outer_frame = Frame(self.control_frame, bd=1, relief='groove')
        volume_outer_frame.grid(
            row=2, column=0, sticky='ew', pady=PADY_OUTER)

        Label(volume_outer_frame, text='Volume').grid(
            row=0, column=0, stick='w', pady=PADY_INNER_1)

        volume_slider = Scale(volume_outer_frame,
                              from_=0, to_=1, resolution=VOLUME_RESOLUTION,
                              orient='horizontal',
                              command=self.set_volume,
                              showvalue=0,
                             )
        volume_slider.set(self.volume)
        volume_slider.grid(row=1, column=0, sticky='w', pady=PADY_INNER_3)

        Label(volume_outer_frame, text='Time').grid(
            row=0, column=1, stick='w', pady=PADY_INNER_1, padx=(20, 0))

        self.time_progress = ttk.Progressbar(volume_outer_frame,
                                             orient='horizontal',
                                             length=100,
                                             mode='determinate'
                                            )
        self.time_progress.grid(
            row=1, column=1, sticky='w', pady=PADY_INNER_3, padx=(20, 0))

    def set_volume(self, value):
        self.volume = float(value)


class SoundVisualiser(TkMplSetup):

    def __init__(self, root):
        super().__init__(root)
        self.audio = pyaudio.PyAudio()
        self.out = ''

    def generate_sound_stream(self):
        if self.selected_type == 1:
            self.sound_stream = (
                (np.sin(2 * np.pi * self.frequency / self.fs *
                        np.arange(self.fs * self.duration))).astype(np.float32)
            ).astype(np.float32)

        elif self.selected_type == 2:
            self.sound_stream = (
                (0.5 * np.sin(2 * np.pi * 325 / self.fs *
                              np.arange(self.fs * self.duration))) +
                (0.1 * np.sin(2 * np.pi * 330 / self.fs *
                              np.arange(self.fs * self.duration))) +
                (0.5 * np.sin(2 * np.pi * 340 / self.fs *
                              np.arange(self.fs * self.duration))) + 0
            ).astype(np.float32)

        elif self.selected_type == 3:
            a = struct.unpack(self.fmt, self.sound_byte_str)
            a = [float(val) for val in a]
            self.sound_stream = np.array(a).astype(np.float32)
            scale_factor = max(abs(np.min(self.sound_stream)),
                               abs(np.max(self.sound_stream)))
            self.sound_stream = self.sound_stream / scale_factor

        else:
            assert False, f'check selected_type invalid value {self.selected_type}'

        self.ax.set_xlim(1000 * PACKAGE_LENGTH / self.fs, 0)

    def callback(self, in_data, frame_count, time_info, status):
        self.out = self.sound_stream[:frame_count]
        self.sound_stream = self.sound_stream[frame_count:]
        return self.out*self.volume, pyaudio.paContinue

    def play_sound(self):
        self.stream = self.audio.open(format=pyaudio.paFloat32,
                                      channels=1,
                                      rate=self.fs,
                                      output=True,
                                      stream_callback=self.callback)

        self.stream.start_stream()

        # pause audio when self.running is False; close audio when stopped
        while self.stream.is_active():
            if self.stopped:
                break

            while not self.running:
                if self.stopped:
                    break

                if self.stream.is_active:
                    self.stream.stop_stream()
                else:
                    pass

            if self.running and not self.stream.is_active():
                self.stream.start_stream()

        self.stream.stop_stream()
        self.stream.close()

        self.running = False
        self.stopped = True
        self.start_pause_button.config(text='Start')

    def update_frame(self, frame):
        samples = len(self.out)
        if samples == PACKAGE_LENGTH:
            self.line.set_data(self.xdata, self.out)

        elif samples > 0:
            xdata = np.linspace(0, 1000 * samples / self.fs, samples)
            self.line.set_data(xdata, self.out)

        else:
            return

        elapsed_time = time.time() - self.start_time - self.pause_time
        self.time_progress['value'] = elapsed_time * 1000

        return self.line,

    def start_visualisation(self):
        self.generate_sound_stream()
        self.xdata = np.linspace(0, 1000 * PACKAGE_LENGTH / self.fs, PACKAGE_LENGTH)
        self.ax.set_ylim(1.1 * np.min(self.sound_stream),
                         1.1 * np.max(self.sound_stream))

        self.line, = self.ax.plot([], [], lw=2)

        duration_range = np.arange(0, self.duration, INTERVAL / 1000)
        self.start_time = time.time()
        self.pause_time = 0
        self.visualisation = FuncAnimation(self.fig,
                                           self.update_frame,
                                           frames=duration_range,
                                           interval=INTERVAL,
                                           repeat=False)

        # start audio deamon in a seperate thread as otherwise audio and
        # plot will not be at the same time
        x = threading.Thread(target=self.play_sound)
        x.daemon = True
        x.start()

        self.root.after(1, self.fig.canvas.draw())


def main():
    root = Tk()
    SoundVisualiser(root)
    root.mainloop()


if __name__ == '__main__':
    main()