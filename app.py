# -*- coding: utf-8 -*-

import os
import subprocess
import struct
import wave

import pyaudio

from mlpy import dtw_subsequence as dtw
from numpy import array
from numpy.fft import fft


config = {'commands_folder': 'commands'}

def unpack_wav(data, nframes, nchannels):
    unpacked = struct.unpack_from("{0}h".format(nframes * nchannels), data)
    first_channel = [unpacked[i] for i in range(0, len(unpacked), nchannels)]
    out = array(list(first_channel))
    dft = fft(out, 1024)
    return dft

def normalize(arr):
    return arr / arr.max()

def load_wav(filepath):
    voice = wave.open(filepath, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = voice.getparams()
    frames = voice.readframes(nframes * nchannels)
    out = unpack_wav(frames, nframes, nchannels)
    voice.close()
    return normalize(out)

class Command:

    def __init__(self, name, path):
        self.name = name
        self.voice = load_wav(os.path.join(path, 'command.wav'))
        self.noise = load_wav(os.path.join(path, 'command_noise.wav'))
        self.shell_path = os.path.join(path, 'command.sh')

    def execute(self):
        with open(os.devnull) as mute:
            subprocess.call(self.shell_path, stderr=mute)

    def distances(self, query):
        voice_d = dtw(self.voice, query)[0]
        noise_d = dtw(self.noise, query)[0]
        return voice_d, noise_d

class VoiceCmd:

    def __init__(self, config):
        self.config = config
        self.commands = {}
        commands_folder = self.config['commands_folder']
        for command_name in os.listdir(commands_folder):
            cmd = Command(command_name, os.path.join(commands_folder, command_name))
            self.commands[command_name] = cmd


    def run(self):
        print "Speak now."
        signal = normalize(self.read_voice())
        print "Recording stopped"
        for command in self.commands.itervalues():
            dist = command.distances(signal)
            print command.name, dist, self.distance(command.voice, command.noise)

    def distance(self, template, query):
        return dtw(template, query)[0]

    def read_voice(self):
        rate, fpb, seconds, channels = 44100, 1024, 5, 1
        read = []
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=fpb)
        chunks_needed = rate / fpb * seconds
        for i in xrange(chunks_needed):
            data = stream.read(fpb)
            read.append(data)
        stream.close()
        p.terminate()
        data = ''.join(read)
        out = unpack_wav(data, chunks_needed * fpb, channels)
        return out


if __name__ == '__main__':
    try:
        VoiceCmd(config).run()
    except KeyboardInterrupt:
        print "\nBye!"
