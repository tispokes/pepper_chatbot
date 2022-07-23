#!/usr/bin/env python2

# TODO description

import qi, argparse, sys
from random import choice

PEPPER_IP = "127.0.0.1"
# uncomment when running remotely
# PEPPER_IP = "141.75.152.37"
PEPPER_PORT = 9559

# possible languages
DE = "German"
EN = "English"

# http://doc.aldebaran.com/2-5/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-pepper
ALL_BEHAVIOURS = [
    "above",
    "affirmative",
    "afford",
    "agitated",
    "all",
    "allright",
    "alright",
    "any",
    "appease",
    "ashamed",
    "assuage",
    "attemper",
    "back",
    "bashful",
    "becalm",
    "beg",
    "beseech",
    "blank",
    "body language",
    "bored",
    "bow",
    "but",
    "call",
    "calm",
    "choice",
    "choose",
    "clear",
    "cloud",
    "cogitate",
    "cool",
    "crazy",
    "despairing",
    "desperate",
    "disappointed",
    "down",
    "earth",
    "embarrassed",
    "empty",
    "enthusiastic",
    "entire",
    "entreat",
    "estimate",
    "every",
    "everyone",
    "everything",
    "exalted",
    "except",
    "excited",
    "explain",
    "far",
    "field",
    "floor",
    "forlorn",
    "friendly",
    "front",
    "frustrated",
    "gentle",
    "gift",
    "give",
    "ground",
    "happy",
    "hello",
    "her",
    "here",
    "hey",
    "hi",
    "high",
    "him",
    "hopeless",
    "hysterical",
    "I",
    "implore",
    "indicate",
    "joyful",
    "me",
    "meditate",
    "modest",
    "mollify",
    "my",
    "myself",
    "negative",
    "nervous",
    "no",
    "not know",
    "nothing",
    "offer",
    "ok",
    "once upon a time",
    "oppose",
    "or",
    "pacify",
    "peaceful",
    "pick",
    "placate",
    "please",
    "present",
    "proffer",
    "quiet",
    "rapturous",
    "raring",
    "reason",
    "refute",
    "reject",
    "rousing",
    "sad",
    "select",
    "shamefaced",
    "show",
    "show sky",
    "shy",
    "sky",
    "soothe",
    "sun",
    "supplicate",
    "tablet",
    "tall",
    "them",
    "there",
    "think",
    "timid",
    "top",
    "unacquainted",
    "uncomfortable",
    "undetermined",
    "undiscovered",
    "unfamiliar",
    "unknown",
    "unless",
    "up",
    "upstairs",
    "void",
    "warm",
    "winner",
    "yeah",
    "yes",
    "yoo-hoo",
    "you",
    "your",
    "zero",
    "zestful"
]
ALL_BEHAVIOURS_LEN = len(ALL_BEHAVIOURS)

HOST = 'pepper-chatbot.informatik.fh-nuernberg.de'
PORT = 4444
FILE = 'Lars-wo_finde_ich_Raum_HW013.wav'
MARKUP_OPENING_CHAR = '['
BUFFER_SIZE = 1024 # same as in server

def pepper_gesture_runner(aps, behaviour):
    print "requested behaviour: ", behaviour
    if behaviour not in ALL_BEHAVIOURS:
        behaviour = choice(ALL_BEHAVIOURS)
    aps.runTag(behaviour, _async=True)
    print "used behaviour: ", behaviour

def send_file(socket):
    with open(FILE, "rb") as file:
        while True:
            # read the bytes from the file
            bytes_read = file.read(BUFFER_SIZE)
            if not bytes_read:
                file.close()
                socket.send(b"DONE")
                print("DONE SENDING")
                # file transmitting is done
                data = socket.recv(1024)
                socket.close()
                break
            socket.sendall(bytes_read)
    print(data)
    return data


def create_AL_services(session):
    # register needed services
    text_to_speech = session.service("ALTextToSpeech")
    animation_player = session.service("ALAnimationPlayer")
    return (animation_player, text_to_speech)

def process_response(data, animation_player, text_to_speech):
    if len(data) > 2:
        words = data.split()
        sentence = ""
        for word in words:
            if word[0] != MARKUP_OPENING_CHAR:
                sentence = sentence + " " + word
            if word[0] == MARKUP_OPENING_CHAR:
                pepper_gesture_runner(animation_player, word[1:-1])
                continue
        print(sentence)
    text_to_speech.say(sentence, DE)
    # text_to_speech.say("Hallo ich bin Pepper.")
    # text_to_speech.say("I can also speak english.", EN)
    
def end_of_session(aps, tts):
    aps.reset()
    tts.setLanguage("German")

def main(session):
    (animation_player, text_to_speech) = create_AL_services(session)
    
    # endless loop coming...
    backend_socket = create_socket()
    backend_response = send_file(backend_socket)
    process_response(backend_response, animation_player, text_to_speech)
    
    # finally
    end_of_session(animation_player, text_to_speech)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default=PEPPER_IP,
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=PEPPER_PORT,
                        help="Naoqi port number")

    args = parser.parse_args()
    session = qi.Session()
    try:
        session.connect("tcp://" + args.ip + ":" + str(args.port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    main(session)
