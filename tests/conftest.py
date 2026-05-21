"""
Configuration pytest commune à tous les tests unitaires du projet.

Rôle de ce fichier :
    1. Injecter des « mocks » pour les modules hardware (RPi.GPIO, mfrc522)
       afin que les tests puissent tourner sur Windows / sans Raspberry Pi.
    2. Ajouter les dossiers Api/ et App/ au PYTHONPATH pour pouvoir importer
       les modules du projet.
    3. Forcer la base de données SQLite en mémoire (BDD éphémère, repartant
       vierge à chaque test) pour ne jamais polluer la vraie BDD Surete.db.
    4. Exposer un client Flask de test et quelques fixtures utiles.

Ce fichier est exécuté automatiquement par pytest avant tous les autres
fichiers `test_*.py`. Il ne faut pas l'importer manuellement.
"""

import os
import sys
from unittest.mock import MagicMock

# ── 1) Mock des modules hardware AVANT tout autre import ─────────────────
sys.modules['RPi']        = MagicMock()
sys.modules['RPi.GPIO']   = MagicMock()
sys.modules['mfrc522']    = MagicMock()

# ── 2) Ajout des dossiers Api/ et App/ au PYTHONPATH ─────────────────────
HERE         = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, '..'))
API_PATH     = os.path.join(PROJECT_ROOT, 'Api')
APP_PATH     = os.path.join(PROJECT_ROOT, 'App')
for p in (API_PATH, APP_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── 3) Override URI SQLite vers une BDD en mémoire ───────────────────────
from src.Api.config import config  # noqa: E402  (import après modification sys.path : voulu)
config.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
config.app.config['TESTING'] = True

# ── 4) Imports des modules applicatifs (après la reconfig) ───────────────
import pytest                       # noqa: E402
from src.Api.db import db                   # noqa: E402
import src.Api.model                        # noqa: E402  (enregistre les tables)
import src.Api.run                       # noqa: E402  (enregistre les routes Flask)


@pytest.fixture
def client():
    """
    Crée un client de test Flask avec une BDD en mémoire fraîche.

    À chaque test, la BDD est entièrement supprimée puis recréée. Aucun
    test ne peut donc être perturbé par les données d'un autre test.
    """
    with config.app.app_context():
        db.drop_all()
        db.create_all()
        with config.app.test_client() as c:
            yield c
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seed_user(client):
    """Crée un utilisateur de test (sans carte) et retourne son id_util."""
    reponse = client.post('/ajouter_un_utilisateur', json={
        'nom':    'Dupont',
        'prenom': 'Jean',
        'droits': 'AT (Accès total)'
    })
    return reponse.get_json().get('id_util')


@pytest.fixture
def seed_user_ar(client):
    """Crée un utilisateur 'Accès Restreint' et retourne son id_util."""
    reponse = client.post('/ajouter_un_utilisateur', json={
        'nom':    'Martin',
        'prenom': 'Paul',
        'droits': 'AR (Accès restreint)'
    })
    return reponse.get_json().get('id_util')


@pytest.fixture
def seed_card(client):
    """Crée une carte de test non assignée et retourne son id_badge."""
    client.post('/ajouter_une_carte', json={
        'id_badge': 12345,
        'texte':    'Carte test',
        'id_util':  None
    })
    return 12345
