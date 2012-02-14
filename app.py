# -*- coding: utf-8 -*-

import os
import subprocess
import struct
import wave

import pyaudio

from mlpy import dtw_subsequence as dtw
from mlpy import LibSvm
from numpy import array, absolute
from numpy.fft import rfft as fft

from mfcc import find_mfcc


config = {'commands_folder': 'commands'}

def unpack_wav(data, nframes, nchannels):
    unpacked = struct.unpack_from("{0}h".format(nframes * nchannels), data)
    first_channel = [unpacked[i] for i in range(0, len(unpacked), nchannels)]
    out = array(list(first_channel))
    #rescaled = power_spectrum(out)
    rescaled = find_mfcc(out)
    return rescaled

def power_spectrum(signal):
    dft = fft(normalize(signal), 2048)
    power = absolute(dft) ** 2
    return power

def normalize(arr):
    return arr / arr.max()

def load_wav(filepath):
    voice = wave.open(filepath, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = voice.getparams()
    frames = voice.readframes(nframes * nchannels)
    out = unpack_wav(frames, nframes, nchannels)
    voice.close()
    return out

class Command:

    def __init__(self, name, index, path):
        self.objects = []
        self.name = name
        self.index = index
        self.shell_path = os.path.join(path, 'command.sh')
        for filepath in os.listdir(path):
            if filepath.endswith('.wav'):
                fullpath = os.path.join(path, filepath)
                features = load_wav(fullpath)
                self.objects.append(features)

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
        self.command_names = {}
        commands_folder = self.config['commands_folder']
        for index, command_name in enumerate(os.listdir(commands_folder)):
            cmd = Command(command_name, index, os.path.join(commands_folder, command_name))
            self.commands[command_name] = cmd
            self.command_names[index] = command_name

        self.svm = LibSvm(svm_type='c_svc', kernel_type='linear')
        x, y = [], []
        for command in self.commands.itervalues():
            for feature in command.objects:
                x.append(feature)
                y.append(command.index)
        self.svm.learn(x, y)

    def run(self):
        print "Speak now."
        signal = self.read_voice()
        #signal = load_wav('commands/calculator/command1.wav')
        print "Recording stopped"
        decision = self.predict(signal)
        print decision
        self.commands[decision].execute()


    def predict(self, signal):
        return self.command_names[int(self.svm.pred(signal))]

    def distance(self, template, query):
        return dtw(template, query)[0]

    def read_voice(self):
        rate, fpb, seconds, channels = 44100, 1024, 3, 1
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

        debug = wave.open('debug.wav', 'wb')
        debug.setnchannels(channels)
        debug.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        debug.setframerate(rate)
        debug.writeframes(data)
        debug.close()

        out = unpack_wav(data, chunks_needed * fpb, channels)
        return out


if __name__ == '__main__':
    try:
        VoiceCmd(config).run()
    except KeyboardInterrupt:
        print "\nBye!"
