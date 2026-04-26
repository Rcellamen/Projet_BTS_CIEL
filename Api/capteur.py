import time
import threading

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522


LED_PIN = 17
PIR_PIN = 4

_badge_lock = threading.Lock()  # ← à mettre en haut du fichier serveur, hors des routes

def Lire_Badge(lecture_continue):
        reader = SimpleMFRC522()
        id = -1
        text = ""
        with _badge_lock:  # ← une seule lecture à la fois
            try:
                if lecture_continue:
                    while True:
                        id, text = reader.read()
                        print(f"Badge détecté ! ID: {id}")
                        time.sleep(1)
                else:
                    print("En attente d'un badge...")
                    id, text = reader.read()
                    print(f"Badge détecté ! ID: {id}")

            except KeyboardInterrupt:
                pass

            finally:
                GPIO.cleanup()

        return id, text

def Lire_PIR():

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        PIR_PIN = 4
        GPIO.setup(PIR_PIN, GPIO.IN)
        GPIO.setup(LED_PIN, GPIO.OUT)

        etat = GPIO.input(PIR_PIN)

        if etat:
            GPIO.output(LED_PIN, GPIO.HIGH)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)

        return ({
            "statut": "ok",
            "mouvement": bool(etat),
            "message": "Mouvement détecté" if etat else "Aucun mouvement"
        }), 200

    except Exception as e:
        return ({
            "statut": "erreur",
            "message": str(e)
        }), 500 