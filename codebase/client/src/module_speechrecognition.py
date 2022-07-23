#!/usr/bin/env python2

# I used this module as base for my developments.
# See https://github.com/JBramauer/pepperspeechrecognition for all features
# like register to the module or something for own further development.
# JBraumer also uses https://github.com/Uberi/speech_recognition as base.
# 
# Usual it only works with a audio threshold to start recording, but that is
# too unprecise in normal live. I did some addons:
# - Now someone must look into Pepper's face while someone is speaking.
# - And Pepper has to be in a higher awareness mode then "None". That means,
#   pepper is kind a locked with a person.
# - Using an other TTS parser (mod9 in my case).
# - Added a GestureRunner to parse the answer from chatbot RASA into
#   "sentences" to say and "movement" (gesture) to execute.

# TODO:             # is these 2 line necessary? what do they do?

# own imports
from client_socket import ClientSocket
import GestureRunner

# used frameworks
import qi, naoqi, time, sys, threading, traceback
import numpy as np
from numpy import sqrt, mean, square
from naoqi import ALProxy
from optparse import OptionParser
from raw_to_wav import rawToWav

HOST = "127.0.0.1" # default, for running on Pepper
PORT = 9559

RECORDING_DURATION = 10     # seconds, maximum recording time, also default value for startRecording(), Google Speech API only accepts up to about 10-15 seconds
LOOKAHEAD_DURATION = 1.0    # seconds, for auto-detect mode: amount of seconds before the threshold trigger that will be included in the request
IDLE_RELEASE_TIME = 2.0     # seconds, for auto-detect mode: idle time (RMS below threshold) after which we stop recording and recognize
HOLD_TIME = 3.0             # seconds, minimum recording time after we started recording (autodetection)
SAMPLE_RATE = 48000         # Hz, be careful changing this, both google and Naoqi have requirements!

CALIBRATION_DURATION = 4    # seconds, timespan during which calibration is performed (summing up RMS values and calculating mean)
CALIBRATION_THRESHOLD_FACTOR = 5  # factor the calculated mean RMS gets multiplied by to determine the auto detection threshold (after calibration)

DEFAULT_LANGUAGE = "de-de"  # RFC5646 language tag, e.g. "en-us", "de-de", "fr-fr",... <http://stackoverflow.com/a/14302134>

WRITE_WAV_FILE = True      # write the recorded audio to "out.wav" before sending it to google. intended for debugging purposes
PRINT_RMS = False           # prints the calculated RMS value to the console, useful for setting the threshold
PRINT_RMS_ONLY_OVER = 10
PRINT_AVG = False
PRINT_FFT = False
PRINT_PEAK = False

PREBUFFER_WHEN_STOP = False # Fills pre-buffer with last samples when stopping recording. WARNING: has performance issues!

AUDIO_RAW = ".raw"
AUDIO_WAV = ".wav"

class SpeechRecognitionModule(naoqi.ALModule):
    """
    Use this object to get call back from the ALMemory of the naoqi world.
    Your callback needs to be a method with two parameter (variable name, value).
    """

    def __init__(self, strModuleName, strPepperHost, PepperPort):
        try:
            naoqi.ALModule.__init__(self, strModuleName)
            self.socket = ClientSocket()
            self.session = qi.Session()
            print self.session.connect("tcp://" + strPepperHost + ":" + str(PepperPort))
            
            self.gestureRunner = GestureRunner.GestureRunner(self.session)

            # is these 2 line necessary? what do they do?
            # just copied them from the examples...
            self.BIND_PYTHON(self.getName(), "callback")

            # declare event to ALMemory so other modules can subscribe
            self.memory = naoqi.ALProxy("ALMemory")
            self.memory.declareEvent("SpeechRecognition")

            # flag to indicate if subscribed to audio events
            self.isStarted = False
            self.isFaceDetected = False

            # flag to indicate if we are currently recording audio
            self.isRecording = False
            self.startRecordingTimestamp = 0
            self.recordingDuration = RECORDING_DURATION

            # flag to indicate if auto speech detection is enabled
            self.isAutoDetectionEnabled = False
            self.autoDetectionThreshold = 10 # TODO: find a default value that works fine so we don't need to calibrate every time

            # flag to indicate if we are calibrating
            self.isCalibrating = False
            self.startCalibrationTimestamp = 0

            # flag to indicate if new audio can be recorded
            # to prevent self recording
            self.isSpeaking = False

            # RMS calculation variables
            self.framesCount = 0
            self.rmsSum = 0 # used to sum up rms results and calculate average
            self.lastTimeRMSPeak = 0

            # audio buffer
            self.buffer = []
            self.preBuffer = []
            self.preBufferLength = 0    # length in samples (len(self.preBuffer) just counts entries)

            # init parameters
            self.language = DEFAULT_LANGUAGE
            self.idleReleaseTime = IDLE_RELEASE_TIME
            self.holdTime = HOLD_TIME
            self.lookaheadBufferSize = LOOKAHEAD_DURATION * SAMPLE_RATE

            # counter for wav file output
            self.fileCounter = 0

        except BaseException, err:
            print("ERR: SpeechRecognitionModule: loading error: %s" % str(err))

    # __init__ - end
    def __del__(self):
        print("INF: SpeechRecognitionModule.__del__: cleaning everything")
        self.stop()

    def start(self):

        if (self.isStarted):
            print("INF: SpeechRecognitionModule.start: already running")
            return

        print("INF: SpeechRecognitionModule: starting!")

        self.isStarted = True

        audio = naoqi.ALProxy("ALAudioDevice")
        self.awareness = naoqi.ALProxy("ALBasicAwareness")
        self.memory.subscribeToEvent("FaceDetected", self.getName(), "on_face_detected")
        nNbrChannelFlag = 0 # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2 AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0
        audio.setClientPreferences(self.getName(), SAMPLE_RATE, nNbrChannelFlag, nDeinterleave) # setting same as default generate a bug !?!
        audio.subscribe(self.getName())

    def on_face_detected(self, strVarName, faceDataArray):
        old = self.isFaceDetected
        self.isFaceDetected = not not faceDataArray # faceDataArray != []
        if (old != self.isFaceDetected):
            print "INF: Face", "" if self.isFaceDetected else "NOT", "detected &", self.awareness.getEngagementMode()

    def pause(self):
        print("INF: SpeechRecognitionModule.pause: stopping")
        if (self.isStarted == False):
            print("INF: SpeechRecognitionModule.stop: not running")
            return

        self.isStarted = False

        audio = naoqi.ALProxy("ALAudioDevice", HOST, PORT)
        audio.unsubscribe(self.getName())

        print("INF: SpeechRecognitionModule: stopped!")

    def stop(self):
        self.pause()

    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        # print("INF: SpeechRecognitionModule: Processing '%s' channels" % nbOfChannels)

        # calculate a decimal seconds timestamp
        timestamp = float (str(aTimeStamp[0]) + "."  + str(aTimeStamp[1]))

        # put whole function in a try/except to be able to see the stracktrace
        try:

            aSoundDataInterlaced = np.fromstring(str(buffer), dtype = np.int16)
            aSoundData = np.reshape(aSoundDataInterlaced, (nbOfChannels, nbrOfSamplesByChannel), 'F')

            # compute RMS, handle autodetection and calibration
            if (self.isCalibrating or self.isAutoDetectionEnabled or self.isRecording):

                # compute the rms level on front mic
                rmsMicFront = self.calcRMSLevel(self.convertStr2SignedInt(aSoundData[0]))

                if (rmsMicFront >= self.autoDetectionThreshold):
                    # save timestamp when we last had and RMS > threshold
                    self.lastTimeRMSPeak = timestamp

                    # start recording if we are not doing so already
                    if (self.isAutoDetectionEnabled 
                        and not self.isRecording 
                        and not self.isCalibrating
                        and not self.isSpeaking
                        and self.awareness.getEngagementMode() != "Unengaged"
                        and self.isFaceDetected):
                        self.startRecording()

                # perform calibration
                if (self.isCalibrating):
                    print "is Calibrating ..."
                    if (self.startCalibrationTimestamp <= 0):
                        # we are starting to calibrate, save timestamp
                        # to track how long we are doing this
                        self.startCalibrationTimestamp = timestamp

                    elif (timestamp - self.startCalibrationTimestamp >= CALIBRATION_DURATION):
                        # time's up, we're done!
                        self.stopCalibration()

                    # sum rms values of the frames
                    # keep track of how many frames we sum up
                    # to calculate mean afterwards
                    self.rmsSum += rmsMicFront
                    self.framesCount = self.framesCount + 1


                if (PRINT_RMS):
                    # for debug purposes
                    # also use it to find a good threshold value for auto detection
                    if (rmsMicFront>PRINT_RMS_ONLY_OVER):
                        print 'Mic RMS: ' + str(rmsMicFront)

            if (PRINT_AVG):
                # compute average
                aAvgValue = np.mean(aSoundData, axis = 1)
                print("avg: %s" % aAvgValue)
            if (PRINT_FFT):
                # compute fft
                nBlockSize = nbrOfSamplesByChannel
                signal = aSoundData[0] * np.hanning(nBlockSize)
                aFft = (np.fft.rfft(signal) / nBlockSize)
                print aFft
            if (PRINT_PEAK):
                # compute peak
                aPeakValue = np.max(aSoundData)
                if (aPeakValue > 16000):
                    print("Peak: %s" % aPeakValue)

            if (not self.isCalibrating):
                if (self.isRecording):
                    # write to buffer
                    self.buffer.append(aSoundData)

                    if (self.startRecordingTimestamp <= 0):
                        # initialize timestamp when we start recording
                        self.startRecordingTimestamp = timestamp
                    elif ((timestamp - self.startRecordingTimestamp) > self.recordingDuration):
                        print('stop after max recording duration')
                        # check how long we are recording
                        self.stopRecordingAndRecognize()

                    # stop recording after idle time (and recording at least hold time)
                    # lastTimeRMSPeak is 0 if no peak occured
                    if (timestamp - self.lastTimeRMSPeak >= self.idleReleaseTime) and (
                            timestamp - self.startRecordingTimestamp >= self.holdTime):
                        print ('stopping after idle/hold time')
                        self.stopRecordingAndRecognize()
                else:
                    # constantly record into prebuffer for lookahead
                    self.preBuffer.append(aSoundData)
                    self.preBufferLength += len(aSoundData[0])

                    # remove first (oldest) item if the buffer gets bigger than required
                    # removes one block of samples as we store a list of lists...
                    overshoot = (self.preBufferLength - self.lookaheadBufferSize)

                    if ((overshoot > 0) and (len(self.preBuffer) > 0)):
                        self.preBufferLength -= len(self.preBuffer.pop(0)[0])

        except:
            # i did this so i could see the stracktrace as the thread otherwise just silently failed
            traceback.print_exc()

    # processRemote - end

    def calcRMSLevel(self, data):
        rms = (sqrt(mean(square(data))))
        # TODO: maybe a log would be better for threshold?
        #rms = 20 * np.log10(np.sqrt(np.sum(np.power(data, 2) / len(data))))
        return rms

    def version(self):
        return "1.2"


    # use this method to manually start recording (works with both autodetection enabled or disabled)
    # the recording will stop after the signal is below the threshold for IDLE_RELEASE_TIME seconds,
    # but will at least record for HOLD_TIME seconds
    def startRecording(self):
        if (self.isRecording):
            print("INF: SpeechRecognitionModule.startRecording: already recording")
            return

        print("INF: Starting to record audio")
        # start recording
        self.startRecordingTimestamp = 0
        self.lastTimeRMSPeak = 0
        self.buffer = self.preBuffer
        self.isRecording = True

        return

    def stopRecordingAndRecognize(self):
        if (self.isRecording == False):
            print("INF: SpeechRecognitionModule.stopRecordingAndRecognize: not recording")
            return

        print("INF: stopping recording and recognizing")

        # TODO: choose which mic channel to use
        # can we use the sound direction module for this?

        # buffer is a list of nparrays we now concat into one array
        # and the slice out the first mic channel
        slice = np.concatenate(self.buffer, axis=1)[0]

        # initialize preBuffer with last samples to fix cut off words
        # loop through buffer and count samples until prebuffer is full
        # TODO: performance issues!
        if (PREBUFFER_WHEN_STOP):
            sampleCounter = 0
            itemCounter = 0

            for i in reversed(self.preBuffer):
                sampleCounter += len(i[0])

                if (sampleCounter > self.lookaheadBufferSize):
                    break

                itemCounter += 1

            start = len(self.buffer) - itemCounter
            self.preBuffer = self.buffer[start:]
        else:
            # don't copy to prebuffer
            self.preBuffer = []

        # start new worker thread to do the http call and some processing
        # copy slice to be thread safe!
        # TODO: make a job queue so we don't start a new thread for each recognition
        threading.Thread(target=self.recognize, args=(slice.copy(), )).start()

        # reset flag
        self.isRecording = False
        self.isFaceDetected = False

        return

    def calibrate(self):
        self.isCalibrating = True
        self.framesCount = 0
        self.startCalibrationTimestamp = 0

        print("INF: starting calibration")

        if (self.isStarted == False):
            self.start()

        return

    def stopCalibration(self):
        if (self.isCalibrating == False):
            print("INF: SpeechRecognitionModule.stopCalibration: not calibrating")
            return

        self.isCalibrating = False

        # calculate avg rms over self.framesCount
        self.threshold = CALIBRATION_THRESHOLD_FACTOR * (self.rmsSum / self.framesCount)
        print 'calibration done, RMS threshold is: ' + str(self.threshold)
        return

    def enableAutoDetection(self):
        self.isSpeaking = False
        self.isAutoDetectionEnabled = True
        print("INF: autoDetection enabled")
        return

    def disableAutoDetection(self):
        self.isSpeaking = True
        self.isAutoDetectionEnabled = False
        print("INF: autoDetection disabled")
        return

    def setLanguage(self, language = DEFAULT_LANGUAGE):
        self.language = language
        return

    # used for RMS calculation
    def convertStr2SignedInt(self, data):
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """

        # from the naoqi sample, but rewritten to use numpy methods instead of for loops
        lsb = data[0::2]
        msb = data[1::2]

        # don't remove the .0, otherwise overflow!
        rms_data = np.add(lsb, np.multiply(msb, 256.0))

        # gives and array that contains -65536 on every position where signedData is > 32768
        sign_correction = np.select([rms_data>=32768], [-65536])

        # add the two to get the correct signed values
        rms_data = np.add(rms_data, sign_correction)

        # normalize values to -1.0 ... +1.0
        rms_data = np.divide(rms_data, 32768.0)

        return rms_data

    def recognize(self, data):
        print 'sending %d bytes' % len(data)

        if (WRITE_WAV_FILE):
            # write to file
            filename = "out" + str(self.fileCounter)
            self.fileCounter += 1
            outfile = open(filename + AUDIO_RAW, "wb")
            data.tofile(outfile)
            outfile.close()
            rawToWav(filename, AUDIO_RAW, AUDIO_WAV)
            backend_response = self.socket.send_file(filename + AUDIO_WAV)
            self.disableAutoDetection()
            self.gestureRunner.process_response(backend_response)
            self.enableAutoDetection()
        print("------------")
        sys.exit()

    def setAutoDetectionThreshold(self, threshold):
        self.autoDetectionThreshold = threshold

    def setIdleReleaseTime(self, releaseTime):
        self.idleReleaseTime = releaseTime

    def setHoldTime(self, holdTime):
        self.holdTime = holdTime

    def setMaxRecordingDuration(self, duration):
        self.recordingDuration = duration

    def setLookaheadDuration(self, duration):
        self.lookaheadBufferSize = duration * SAMPLE_RATE
        self.preBuffer = []
        self.preBufferLength = 0

# SpeechRecognition - end


    def getAudioDuration(self):
        return len(self.audio_data)/48000.0

def main():
    """ Main entry point

    """
    parser = OptionParser()
    parser.add_option(
        "--pip",
        help="Parent broker port. The IP address or your robot",
        dest="pip")
    parser.add_option(
        "--pport",
        help="Parent broker port. The port NAOqi is listening to",
        dest="pport",
        type="int")
    parser.set_defaults(
        pip=HOST,
        pport=PORT)

    (opts, args_) = parser.parse_args()
    pip   = opts.pip
    pport = opts.pport

    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = naoqi.ALBroker(
        "myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       pip,         # parent broker IP
       pport)        # parent broker port

    try:
        p = ALProxy("SpeechRecognition")
        p.exit()  # kill previous instance, useful for developing ;)
    except:
        pass

    # Reinstantiate module

    # Warning: SpeechRecognition must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", pip, pport)

    # uncomment for debug purposes
    # usually a subscribing client will call start() from ALProxy
    SpeechRecognition.start()
    # SpeechRecognition.startRecording()
    SpeechRecognition.calibrate()
    SpeechRecognition.enableAutoDetection()
    # SpeechRecognition.startRecording()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print
        print "Interrupted by user, shutting down"
        myBroker.shutdown()
        sys.exit(0)



if __name__ == "__main__":
    main()
