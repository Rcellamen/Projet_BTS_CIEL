"""
Module de pilotage des capteurs hardware connectés au Raspberry Pi.

Capteurs gérés :
    - Lecteur RFID MFRC522 (badge)
    - Capteur de mouvement PIR (HC-SR501)
    - Détecteur d'ouverture de porte (contact sec / interrupteur magnétique)
    - LED visuelle de signalisation

Toutes les fonctions sont conçues pour être appelées depuis les routes Flask
définies dans `run.py`.
"""

import time
import threading

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522


# ── Constantes des broches GPIO (numérotation BCM) ─────────────────────────
LED_PIN   = 17      # LED de signalisation (sortie)
PIR_PIN   = 4       # Capteur infrarouge passif (entrée)
PORTE_PIN = 27      # Contact d'ouverture de porte (entrée, pull-up interne)


# ── Verrou protégeant l'accès concurrent au lecteur RFID ───────────────────
_badge_lock = threading.Lock()


def _init_gpio():
    """
    Initialise le mode GPIO et configure toutes les broches utilisées par
    les capteurs (PIR, détecteur de porte, LED). Idempotente : peut être
    appelée plusieurs fois sans effet de bord.
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIR_PIN,   GPIO.IN)
    GPIO.setup(PORTE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED_PIN,   GPIO.OUT)


def Lire_Badge(lecture_continue, timeout=30):
    """
    Lit un badge RFID via le module MFRC522, avec polling et timeout.

    Utilise `read_no_block()` plutôt que `read()` pour ne pas bloquer
    indéfiniment l'API : si aucune carte n'est détectée dans le délai imparti,
    la fonction retourne (-1, "") proprement et la route Flask répond à l'IHM.

    Note : on s'abstient volontairement de `GPIO.cleanup()` après la lecture.
    Cela évite de remettre les broches PIR/Porte/LED dans un état inattendu et
    laisse le reader RFID stable pour les appels suivants.

    :param lecture_continue: si True, mode debug en boucle infinie.
    :param timeout: durée maximale d'attente en secondes (défaut : 30).
    :return: tuple (id_badge, texte). id_badge = -1 si rien lu dans le délai.
    """
    id_badge = -1
    text = ""
    with _badge_lock:
        reader = SimpleMFRC522()
        try:
            print(f"[RFID] En attente d'un badge (timeout {timeout}s)…")

            if lecture_continue:
                # Mode debug : lit en boucle (utilisé manuellement, pas via API)
                while True:
                    rid, rtext = reader.read()
                    print(f"[RFID] Badge détecté ! ID: {rid}")
                    time.sleep(1)
            else:
                # Mode API : polling jusqu'au premier badge détecté ou timeout
                start = time.time()
                while time.time() - start < timeout:
                    rid, rtext = reader.read_no_block()
                    if rid:
                        id_badge = rid
                        text = rtext or ""
                        print(f"[RFID] Badge détecté ! ID: {id_badge}")
                        break
                    time.sleep(0.1)
                else:
                    print(f"[RFID] Timeout : aucun badge détecté en {timeout}s.")

        except KeyboardInterrupt:
            pass
        except Exception as e:
            # On loggue mais on ne plante pas l'API : l'IHM saura quoi afficher
            print(f"[RFID] Erreur lors de la lecture : {e}")

    return id_badge, (text or "")


def Lire_PIR():
    """
    Lit l'état instantané du capteur PIR (détection de mouvement).

    Allume également la LED si un mouvement est détecté, l'éteint sinon.

    :return: tuple (json, code_http) :
        - {"statut": "ok", "mouvement": bool, "message": str} en cas de succès
        - {"statut": "erreur", "message": str} en cas d'exception
    """
    try:
        _init_gpio()

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


def Lire_Porte():
    """
    Lit l'état instantané du détecteur d'ouverture de porte.

    Le contact est câblé entre PORTE_PIN et la masse, avec pull-up interne :
        - Porte fermée  → contact fermé → niveau LOW (0)
        - Porte ouverte → contact ouvert → niveau HIGH (1)

    :return: tuple (json, code_http) :
        - {"statut": "ok", "ouverte": bool, "message": str} en cas de succès
        - {"statut": "erreur", "message": str} en cas d'exception
    """
    try:
        _init_gpio()

        etat = GPIO.input(PORTE_PIN)
        ouverte = bool(etat)  # HIGH = porte ouverte (contact relâché)

        return ({
            "statut": "ok",
            "ouverte": ouverte,
            "message": "Porte Ouverte" if ouverte else "Porte Fermée"
        }), 200

    except Exception as e:
        return ({
            "statut": "erreur",
            "message": str(e)
        }), 500
