#!/bin/sh -x

# trains a new model and stores it as "active_model" in directory models

# https://rasa.com/docs/rasa/command-line-interface/#rasa-train

cd /var/bot/pepper-chatbot
/opt/venv/rasa/bin/python3 -m rasa train --fixed-model-name current_model
