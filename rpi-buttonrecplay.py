import os.path
import threading
from signal import pause
from time import sleep
from gpiozero import Button
import pygame.mixer as mixer
import pyaudio
import wave

# General settings
sample               = '/usr/lib/rpi-buttonrecplay/audio/sample.wav'
recfile              = '/usr/lib/rpi-buttonrecplay/audio/rec.wav'
beepfile             = '/usr/lib/rpi-buttonrecplay/audio/beep.wav'
max_rec_time         = 300 # seconds
rec_dev_index        = 1   # the first recording device
blue                 = Button(5 , bounce_time = 0.1)
yellow               = Button(13, bounce_time = 0.1)
red                  = Button(21, bounce_time = 0.1)
none                 = Button(17) # Assign unused button

# Initialization
format               = pyaudio.paInt16
samp_rate            = 44100
chunk                = 4096
channels             = 1
max_frames           = int(samp_rate/chunk)*max_rec_time
mixer.init()
beep                 = mixer.Sound(beepfile)
is_paused            = False
record_thread        = threading.Thread()
recorder = pyaudio.PyAudio()
running              = none

def record():
    global remaining_frames
    mixer.Sound.play(beep)
    sleep(0.2)
    stream = recorder.open(
        format             = format
       ,rate               = samp_rate
       ,channels           = channels
       ,input_device_index = rec_dev_index
       ,input              = True
       ,frames_per_buffer  = chunk
    )
    # loop through stream and append audio chunks to frame array
    remaining_frames = max_frames
    frames = []
    while remaining_frames > 0:
        remaining_frames -= 1
        data = stream.read(chunk)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    # save the audio frames as .wav file
    wavefile = wave.open(recfile,'wb')
    wavefile.setnchannels(channels)
    wavefile.setsampwidth(recorder.get_sample_size(format))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()
    mixer.Sound.play(beep)

def button_handler(button):
    global running
    global is_paused
    global remaining_frames
    global record_thread 
    if button in (blue, yellow):
        if running == button:
            if is_paused:
                mixer.music.unpause()
                is_paused = False
            elif mixer.music.get_pos() > 0:
                mixer.music.pause()
                is_paused = True
            else:
                mixer.music.play()
                is_paused = False
        else:
            if running == red:
                remaining_frames = 1
                record_thread.join()
            soundfile = sample if button == blue else recfile
            if os.path.isfile(soundfile):
                mixer.music.load(soundfile)
                mixer.music.play()
                running = button
                is_paused = False
    elif button == red:
        if running == button:
            remaining_frames = 1
            running = none
            record_thread.join()
        else:
            running = button
            if mixer.music.get_pos() > 0:
                mixer.music.stop()
            record_thread = threading.Thread(target=record)
            record_thread.start()

blue.when_released   = button_handler
yellow.when_released = button_handler
red.when_released    = button_handler

pause()
