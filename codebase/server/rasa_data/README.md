# RASA

Dieses Verzeichnis enthält alle nötigen Dateien um eine Rasa-Instanz mit dem trainierten Model für Pepper zu starten.

## Wichtige Dateien

- `domain.yml` -> Alle Antworten inkl. Markup-Tags für Peppers Gestensteuerung.
- `data/nlu.yml` -> Alle Trainigssätze je `intent` (Absicht)
- `data/stories.yml` -> Zusammenspiel von `intent` und `utter` (Äußerung)

## Skripte

- `bin/start_rasa.sh`
- `bin/train_model.sh`

## Verzeichnisstruktur

Alle Dateien und Unterverzeichnisse sollten sich in `/var/bot/pepper-chatbot` befinden.
TODO VENV
TODO user RASA -> Link RASA Install und co.

## Gestensteuerung

Gesten werden in eckige Klammern gerahmt ('[]'). Wenn eine Antwort (response) in der Datei `domain.yaml` mit einer Geste beginnt, muss der Antworttext in Anführungszeichen gesetzt werden ("), da es sonst als Array/Liste erkannt wird.

Mehr zur YAML-Syntax: https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html

## Training des Modells

Bei Änderungen an einer der `Wichtige Dateien` muss das Modell neu trainiert werden.
Wird nur die `domain.yml` geändert, geht das Training sehr schnell.
Werden neue Stories oder NLU-Daten hinzugefügt, ist das Training zeitintensiver.

Das Skript `train_model.sh` stellt sicher, dass immer der gleiche Name für das trainierte Modell genutzt wird.

## Start von RASA

Der Start von RASA muss aus dem Verzeichnis in der die `domain.yml`-Datei gespeichert ist erfolgen. RASA muss mit dem Parameter `--enable-api` gestartet werden, damit die Endpoints `webhooks/<channel>/webhook` erreichbar sind.
Diese werden von der Python Chatbot-Schnittstelle verwendet.

Das Skript `start_rasa.sh` kann via `cronjob` oder andere Dienste dazu verwendet werden.

Mehr dazu: https://rasa.com/docs/rasa/http-api/
