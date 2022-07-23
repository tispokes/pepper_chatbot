#!/usr/bin/env python2

# TODO better parser
# TODO options
# TODO remove comments

from random import choice
import qi

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

MARKUP_OPENING_CHAR = '['

class GestureRunner():
    def __init__(self, session):
        self.text_to_speech = session.service("ALTextToSpeech")
        self.animation_player = session.service("ALAnimationPlayer")

    def pepper_gesture_runner(self, behaviour):
        print "requested behaviour: ", behaviour
        if behaviour not in ALL_BEHAVIOURS:
            behaviour = choice(ALL_BEHAVIOURS)
        print "running behaviour: ", behaviour
        doing = qi.async(self.animation_player.runTag, behaviour)
        doing.wait()
        print "used behaviour: ", behaviour

    def process_response(self, rasa_repsonse):
        sentence = ""
        gestures = []
        if rasa_repsonse and len(rasa_repsonse) > 2:
            words = rasa_repsonse.split()
            for word in words:
                if word[0] != MARKUP_OPENING_CHAR:
                    sentence = sentence + " " + word
                if word[0] == MARKUP_OPENING_CHAR:
                    gestures.append(word[1:-1])
                    # continue
            print(sentence)
        print("Pepper is speaking")
        say = qi.async(self.text_to_speech.say, sentence)
        for gesture in gestures:
            self.pepper_gesture_runner(gesture)
        say.wait()
        print("Pepper speaking DONE")
