import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
LED_PIN = 17
PIR_PIN = 4

def Lire_Badge(lecture_continue=False):
    """
    Reads RFID badge information continuously until interrupted.
    This function initializes an RFID reader and enters a loop where it waits for
    badges to be placed on the reader. When a badge is detected, its ID is displayed
    and the function pauses for 1 second to prevent duplicate readings of the same badge.
    Args:
        choix (bool): A flag that controls the reading loop. When True, the function
                      will continuously read badges. When False, the loop exits.
    Returns:
        id, text (int, string): Renvoi l'id du badge et ce qu'il contient 
    Raises:
        KeyboardInterrupt: Caught internally to allow graceful exit when user presses Ctrl+C.
    Note:
        - Requires SimpleMFRC522 RFID reader library
        - Cleans up GPIO resources properly on exit
        - Prints detected badge IDs to console
    """

    # Initialisation du lecteur
    reader = SimpleMFRC522()
    id = -1
    text = "Error"
    
    try:   
        if lecture_continue:
            # Mode Boucle
            while True:
                id, text = reader.read()
                print(f"Badge détecté en boucle ! ID: {id}")
                time.sleep(1)
        else:
            # Mode API (Lecture unique)
            print("En attente d'un badge...")
            id, text = reader.read()
            print(f"Badge détecté ! ID: {id}")
            
    except KeyboardInterrupt:
        pass

    finally:
        # Nettoyage propre du GPIO
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