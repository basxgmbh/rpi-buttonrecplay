from gpiozero import Button
from signal   import pause
import pygame.mixer as mixer
import os.path
import pyaudio
import wave
import threading

class ButtonPlayRec(object):
    def __init__(self):
        # General settings
        self.sample               = '/usr/local/share/buttonrecplay/audio/sample.wav'
        self.recfile              = '/usr/local/share/buttonrecplay/audio/rec.wav'
        self.beepfile             = '/usr/local/share/buttonrecplay/audio/beep.wav'
        self.max_rec_time         = 300                 # seconds
        self.rec_dev_index        = 1
        self.blue                 = Button(5 , bounce_time = 0.1)
        self.yellow               = Button(13, bounce_time = 0.1)
        self.red                  = Button(21, bounce_time = 0.1)
        # Initialization
        self.format               = pyaudio.paInt16
        self.samp_rate            = 44100
        self.chunk                = 4096
        self.channels             = 1
        self.max_frames           = int(self.samp_rate/self.chunk)*self.max_rec_time
        self.recorder             = pyaudio.PyAudio()
        mixer.init()
        self.beep                 = mixer.Sound(self.beepfile)
        self.blue.when_released   = self.start_play
        self.yellow.when_released = self.start_play
        self.red.when_released    = self.start_recording
        self.is_recording         = False

    def start_play(self, button):
        self.button = button
        if button == self.blue:
            filename = self.sample
            self.yellow.when_released = self.start_play
        elif button == self.yellow:
            filename = self.recfile
            self.blue.when_released = self.start_play
        if self.is_recording:
            self.remaining_frames = 0
            self.record_thread.join()
        if os.path.isfile(filename):
            mixer.music.load(filename)
            self.play()

    def play(self):
        mixer.music.play()
        self.button.when_released = self.pause

    def pause(self):
        if mixer.music.get_pos() != -1:
            mixer.music.pause()
            self.button.when_released = self.resume
        else:
            self.play()

    def resume(self):
        mixer.music.unpause()
        self.button.when_released = self.pause

    def start_recording(self):
        if mixer.music.get_pos() > 1:
            mixer.music.stop()
        mixer.Sound.play(self.beep)
        self.frames = []
        self.stream = self.recorder.open(
            format             = self.format
           ,rate               = self.samp_rate
           ,channels           = self.channels
           ,input_device_index = self.rec_dev_index
           ,input              = True
           ,frames_per_buffer  = self.chunk
        )
        self.red.when_released = self.stop_recording
        self.record_thread     = threading.Thread(target=self.record)
        self.record_thread.start()

    def record(self):
        self.is_recording = True
        # loop through stream and append audio chunks to frame array
        self.remaining_frames = self.max_frames
        while self.remaining_frames > 0:
            self.remaining_frames -= 1
            data = self.stream.read(self.chunk)
            self.frames.append(data)

        self.stream.stop_stream()
        self.stream.close()
        mixer.Sound.play(self.beep)
        self.red.when_released = self.start_recording

        # save the audio frames as .wav file
        wavefile = wave.open(self.recfile,'wb')
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self.recorder.get_sample_size(self.format))
        wavefile.setframerate(self.samp_rate)
        wavefile.writeframes(b''.join(self.frames))
        wavefile.close()
        self.is_recording = False

    def stop_recording(self):
        self.remaining_frames = 0
        self.record_thread.join()

rec = ButtonPlayRec()

pause()
