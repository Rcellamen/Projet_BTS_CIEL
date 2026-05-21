"""
Tests unitaires des routes capteurs (Api/run.py).

Ces tests utilisent `unittest.mock.patch` pour neutraliser le hardware :
    - Lire_Badge  → simulé pour renvoyer un id_badge précis ou un timeout
    - Lire_PIR    → simulé pour renvoyer un état mouvement / pas de mouvement
    - Lire_Porte  → simulé pour renvoyer un état ouverte / fermée

Couvre le tableau de bord IHM : lecture d'un badge, évaluation des droits
selon le mode (Libre / Restreint), et lecture instantanée des capteurs
PIR et porte.
"""

import pytest
from unittest.mock import patch

# Module dans lequel les fonctions sont importées (et donc à patcher) :
RUN_MODULE = 'Api.run'


# ──────────────────────────────────────────────────────────────────────────
#                           /lire_badge
# ──────────────────────────────────────────────────────────────────────────

class TestLireBadge:
    """Route GET /lire_badge."""

    def test_lecture_badge_succes(self, client, seed_card):
        """Badge détecté + présent en BDD → 200 avec id et texte."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(seed_card, 'Carte test')):
            resp = client.get('/lire_badge')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id']    == str(seed_card)
        assert data['texte'] == 'Carte test'

    def test_lecture_badge_inconnu(self, client):
        """Badge détecté mais absent de la BDD → 200 quand même (id remonté)."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(42424242, '')):
            resp = client.get('/lire_badge')
        assert resp.status_code == 200
        assert resp.get_json()['id'] == '42424242'

    def test_lecture_badge_timeout(self, client):
        """Aucun badge détecté (id = -1) → 408."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(-1, '')):
            resp = client.get('/lire_badge')
        assert resp.status_code == 408
        assert "timeout" in resp.get_json()['Erreur'].lower()

    def test_lecture_badge_exception_hardware(self, client):
        """Erreur hardware côté Pi → 500."""
        with patch(f'{RUN_MODULE}.Lire_Badge',
                   side_effect=RuntimeError("SPI down")):
            resp = client.get('/lire_badge')
        assert resp.status_code == 500
        assert "Lecture impossible" in resp.get_json()['Erreur']


# ──────────────────────────────────────────────────────────────────────────
#                       /scanner_acces/<mode>
# ──────────────────────────────────────────────────────────────────────────

class TestScannerAcces:
    """Route GET /scanner_acces/<mode> : évaluation du droit d'accès."""

    def test_badge_inconnu_toujours_refuse(self, client):
        """Badge inconnu → autorise=False, motif='Badge inconnu'."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(11111, '')):
            resp = client.get('/scanner_acces/restreint')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['autorise'] is False
        assert data['motif']   == 'Badge inconnu'

    def test_badge_sans_utilisateur(self, client, seed_card):
        """Badge connu mais non assigné → refusé."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(seed_card, '')):
            resp = client.get('/scanner_acces/restreint')
        data = resp.get_json()
        assert data['autorise'] is False
        assert "non assigné" in data['motif']

    def test_mode_libre_autorise(self, client, seed_user_ar, seed_card):
        """Mode libre + utilisateur AR → autorisé (la zone est en accès libre)."""
        # Lier la carte à l'utilisateur AR (qui serait refusé en restreint)
        client.post(f'/ajouter_une_carte_a_util/{seed_user_ar}',
                    json={'id_badge': seed_card})
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(seed_card, '')):
            resp = client.get('/scanner_acces/libre')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['autorise'] is True
        assert data['nom']    == 'Martin'
        assert "Libre" in data['motif']

    def test_mode_restreint_droits_AT_autorise(self, client, seed_user, seed_card):
        """Mode restreint + utilisateur AT (Accès total) → autorisé."""
        # Lier la carte à l'utilisateur AT
        client.post(f'/ajouter_une_carte_a_util/{seed_user}',
                    json={'id_badge': seed_card})
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(seed_card, '')):
            resp = client.get('/scanner_acces/restreint')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['autorise'] is True
        assert data['nom']    == 'Dupont'
        assert "AT" in data['motif']

    def test_mode_restreint_droits_AR_refuse(self, client, seed_user_ar, seed_card):
        """Mode restreint + utilisateur AR (Accès restreint) → refusé."""
        client.post(f'/ajouter_une_carte_a_util/{seed_user_ar}',
                    json={'id_badge': seed_card})
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(seed_card, '')):
            resp = client.get('/scanner_acces/restreint')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['autorise'] is False
        assert "AR" in data['motif']

    def test_timeout_aucun_badge(self, client):
        """Aucun badge en 30s → 408."""
        with patch(f'{RUN_MODULE}.Lire_Badge', return_value=(-1, '')):
            resp = client.get('/scanner_acces/restreint')
        assert resp.status_code == 408


# ──────────────────────────────────────────────────────────────────────────
#                           /test_PIR
# ──────────────────────────────────────────────────────────────────────────

class TestCapteurPIR:
    """Route GET /test_PIR : lecture du capteur de mouvement."""

    def test_pir_mouvement_detecte(self, client):
        """Quand le PIR retourne HIGH → 'Mouvement détecté'."""
        fake_return = ({"statut": "ok",
                        "mouvement": True,
                        "message": "Mouvement détecté"}, 200)
        with patch(f'{RUN_MODULE}.Lire_PIR', return_value=fake_return):
            resp = client.get('/test_PIR')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['mouvement'] is True
        assert data['message']   == 'Mouvement détecté'

    def test_pir_aucun_mouvement(self, client):
        """Quand le PIR retourne LOW → 'Aucun mouvement'."""
        fake_return = ({"statut": "ok",
                        "mouvement": False,
                        "message": "Aucun mouvement"}, 200)
        with patch(f'{RUN_MODULE}.Lire_PIR', return_value=fake_return):
            resp = client.get('/test_PIR')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['mouvement'] is False

    def test_pir_erreur_hardware(self, client):
        """En cas d'erreur GPIO → 500 et statut='erreur'."""
        fake_return = ({"statut": "erreur",
                        "message": "GPIO failure"}, 500)
        with patch(f'{RUN_MODULE}.Lire_PIR', return_value=fake_return):
            resp = client.get('/test_PIR')
        assert resp.status_code == 500
        assert resp.get_json()['statut'] == 'erreur'


# ──────────────────────────────────────────────────────────────────────────
#                           /test_porte
# ──────────────────────────────────────────────────────────────────────────

class TestCapteurPorte:
    """Route GET /test_porte : lecture du détecteur d'ouverture."""

    def test_porte_ouverte(self, client):
        """Contact relâché (HIGH) → 'Porte Ouverte'."""
        fake_return = ({"statut": "ok",
                        "ouverte": True,
                        "message": "Porte Ouverte"}, 200)
        with patch(f'{RUN_MODULE}.Lire_Porte', return_value=fake_return):
            resp = client.get('/test_porte')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ouverte'] is True
        assert data['message'] == 'Porte Ouverte'

    def test_porte_fermee(self, client):
        """Contact fermé (LOW) → 'Porte Fermée'."""
        fake_return = ({"statut": "ok",
                        "ouverte": False,
                        "message": "Porte Fermée"}, 200)
        with patch(f'{RUN_MODULE}.Lire_Porte', return_value=fake_return):
            resp = client.get('/test_porte')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ouverte'] is False

    def test_porte_erreur_hardware(self, client):
        """En cas d'erreur GPIO → 500 et statut='erreur'."""
        fake_return = ({"statut": "erreur",
                        "message": "GPIO failure"}, 500)
        with patch(f'{RUN_MODULE}.Lire_Porte', return_value=fake_return):
            resp = client.get('/test_porte')
        assert resp.status_code == 500
        assert resp.get_json()['statut'] == 'erreur'


# ──────────────────────────────────────────────────────────────────────────
#                           /liberer_verrou
# ──────────────────────────────────────────────────────────────────────────

class TestLibererVerrou:
    """Route POST /liberer_verrou : relâche le verrou de lecture badge."""

    def test_liberer_sans_verrou_actif(self, client):
        """Appel quand aucune lecture en cours → 200 quand même."""
        resp = client.post('/liberer_verrou')
        assert resp.status_code == 200
        assert resp.get_json()['statut'] == 'ok'

    def test_liberer_libere_le_verrou(self, client):
        """Si le verrou est pris, liberer_verrou doit le libérer."""
        from src.Api.run import _badge_lock
        _badge_lock.acquire()
        assert _badge_lock.locked() is True
        resp = client.post('/liberer_verrou')
        assert resp.status_code == 200
        assert _badge_lock.locked() is False
