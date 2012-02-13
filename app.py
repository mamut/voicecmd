# -*- coding: utf-8 -*-

import os
import subprocess
import struct
import wave

from mlpy import Dtw
from numpy import array

config = {'commands_folder': 'commands'}

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
        unpacked = struct.unpack_from("{0}h".format(nframes * nchannels), frames)
        first_channel = [unpacked[i] for i in range(0, len(unpacked), nchannels)]
        out = array(list(first_channel))
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


if __name__ == '__main__':
    try:
        VoiceCmd(config).run()
    except KeyboardInterrupt:
        print "\nBye!"
