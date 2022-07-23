###########################################################
# This method converts raw audio files in the project directory to wav files
#
# Author: Johannes Bramauer, Vienna University of Technology
# Created: May 30, 2018
# License: MIT
#
###########################################################
import wave
import os

def rawToWav(filename, RAW, WAV):

    rawfile = filename + RAW
    if not os.path.isfile(rawfile):
        return

    outfile = wave.open(filename + WAV, "wb")
    outfile.setframerate(48000)
    outfile.setnchannels(1)
    outfile.setsampwidth(2)

    f = open(rawfile, "rb")
    sample = f.read(4096)
    print 'writing file: ' + filename + WAV

    while sample != "":
        outfile.writeframes(sample)
        sample = f.read(4096)

    outfile.close()

    os.remove(rawfile)
