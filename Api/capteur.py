import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

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