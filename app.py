# -*- coding: utf-8 -*-

import os
import subprocess
import struct
import wave

import pyaudio

from mlpy import Dtw
from numpy import array

config = {'commands_folder': 'commands'}

def unpack_wav(data, nframes, nchannels):
    unpacked = struct.unpack_from("{0}h".format(nframes * nchannels), data)
    first_channel = [unpacked[i] for i in range(0, len(unpacked), nchannels)]
    out = array(list(first_channel))
    return out

class Command:

    def __init__(self, name, path):
        self.name = name
        self.voice_path = os.path.join(path, 'command.wav')
        self.shell_path = os.path.join(path, 'command.sh')

    def execute(self):
        with open(os.devnull) as mute:
            subprocess.call(self.shell_path, stderr=mute)

    def get_voice_array(self):
        voice = wave.open(self.voice_path, 'rb')
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = voice.getparams()
        frames = voice.readframes(nframes * nchannels)
        out = unpack_wav(frames, nframes, nchannels)
        return out

class VoiceCmd:

    def __init__(self, config):
        self.config = config
        self.commands = {}
        self.dtw = Dtw()
        commands_folder = self.config['commands_folder']
        for command_name in os.listdir(commands_folder):
            cmd = Command(command_name, os.path.join(commands_folder, command_name))
            self.commands[command_name] = cmd


    def run(self):
        x = array([0,0,0,0,0,1,1])
        for command in self.commands.itervalues():
            dist = self.dtw.compute(x, command.get_voice_array())
            print dist
        print self.read_voice()

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
