#adaptado de https://python-sounddevice.readthedocs.io/en/0.4.6/examples.html#recording-with-arbitrary-duration

import sounddevice as sd
import soundfile as sf
import queue

q = queue.Queue()

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


try:
    # Make sure the file is opened before recording anything:
    with sf.SoundFile('temp4.wav', mode='x', samplerate=44100,
                      channels=1) as file:
        with sd.InputStream(samplerate=44100, device=0,
                            channels=1, callback=callback):
            print('#' * 80)
            print('press Ctrl+C to stop the recording')
            print('#' * 80)
            while True:
                file.write(q.get())
except KeyboardInterrupt:
    print('\nRecording finished: ' + repr(args.filename))
    parser.exit(0)