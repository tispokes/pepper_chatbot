#!/bin/sh -x

cd /var/bot/pepper-chatbot
/opt/venv/rasa/bin/python3 -m rasa run -m models --enable-api --debug
