#!/usr/bin/env python2

# This file is for testing the TTS and gestures/behaviours of pepper.

import GestureRunner
import qi
import argparse
import sys

def main(session):
    runner = GestureRunner.GestureRunner(session)
    tabletService = session.service("ALTabletService")
    tabletService.loadApplication("j-tablet-test")
    tabletService.showWebview()
    raw_input()
    tabletService.hideWebview()
    raw_input()
    runner.process_response("[yoo-hoo] Hallo zusammen. [happy]")
    raw_input()
    runner.process_response("\\tn=spell\\pepper")
    raw_input()
    runner.process_response("[sky] Danke. Gibt es noch Fragen?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
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