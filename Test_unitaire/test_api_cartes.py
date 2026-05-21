"""
Tests unitaires des routes de gestion des cartes RFID (Api/run.py).

Couvre la création, la consultation, la modification et la suppression des
badges, ainsi que les cas de cartes libres / déjà attribuées.
"""

import pytest


class TestAjouterUneCarte:
    """Route POST /ajouter_une_carte."""

    def test_ajout_carte_nominal(self, client):
        """Création d'une carte avec id et texte → 201."""
        reponse = client.post('/ajouter_une_carte', json={
            'id_badge': 100,
            'texte':    'Carte A',
            'id_util':  None
        })
        assert reponse.status_code == 201
        assert "Ajout" in str(reponse.get_json())

    def test_ajout_carte_doublon(self, client):
        """Ajouter deux fois la même id_badge → 404 (erreur de doublon)."""
        client.post('/ajouter_une_carte', json={
            'id_badge': 200, 'texte': 'X', 'id_util': None})
        reponse = client.post('/ajouter_une_carte', json={
            'id_badge': 200, 'texte': 'Y', 'id_util': None})
        assert reponse.status_code == 404
        assert "Erreur" in reponse.get_json()

    def test_ajout_carte_texte_vide(self, client):
        """Une carte sans libellé est acceptée (val_badge = None)."""
        reponse = client.post('/ajouter_une_carte', json={
            'id_badge': 300, 'texte': '', 'id_util': None})
        assert reponse.status_code == 201


class TestVerifierCarte:
    """Route GET /verifier_carte/<id>."""

    def test_carte_existante(self, client, seed_card):
        """Une carte existante doit être trouvée."""
        reponse = client.get(f'/verifier_carte/{seed_card}')
        assert reponse.status_code == 200
        data = reponse.get_json()
        assert data['existe'] is True

    def test_carte_inexistante(self, client):
        """Une carte inconnue doit retourner existe=False."""
        reponse = client.get('/verifier_carte/99999')
        assert reponse.status_code == 200
        data = reponse.get_json()
        assert data['existe'] is False


class TestModifierUneCarte:
    """Route GET/POST /modifier_une_carte/<id>."""

    def test_get_carte_existante(self, client, seed_card):
        """GET sur une carte existante retourne ses informations."""
        reponse = client.get(f'/modifier_une_carte/{seed_card}')
        assert reponse.status_code == 201
        data = reponse.get_json()
        assert data['id'] == seed_card
        assert data['texte'] == 'Carte test'

    def test_modification_texte(self, client, seed_card):
        """POST modifie correctement le libellé."""
        reponse = client.post(f'/modifier_une_carte/{seed_card}', json={
            'texte': 'Nouveau libellé'
        })
        assert reponse.status_code == 200
        # Vérifie que la modification est persistée
        check = client.get(f'/modifier_une_carte/{seed_card}').get_json()
        assert check['texte'] == 'Nouveau libellé'


class TestSupprimerUneCarte:
    """Route GET /supprimer_une_carte/<id>."""

    def test_suppression_carte_existante(self, client, seed_card):
        """Suppression d'une carte existante → 201."""
        reponse = client.get(f'/supprimer_une_carte/{seed_card}')
        assert reponse.status_code == 201
        # La carte ne doit plus exister
        check = client.get(f'/verifier_carte/{seed_card}').get_json()
        assert check['existe'] is False

    def test_suppression_carte_inexistante(self, client):
        """Suppression d'une carte inconnue → 404."""
        reponse = client.get('/supprimer_une_carte/99999')
        assert reponse.status_code == 404


class TestAfficherCartes:
    """Route GET /afficher_cartes."""

    def test_liste_vide_au_demarrage(self, client):
        """Sans aucune carte, la liste est vide."""
        reponse = client.get('/afficher_cartes')
        assert reponse.status_code == 201
        assert reponse.get_json()['cartes'] == []

    def test_liste_apres_plusieurs_ajouts(self, client):
        """Toutes les cartes ajoutées doivent apparaître dans la liste."""
        for i in range(3):
            client.post('/ajouter_une_carte', json={
                'id_badge': 400 + i, 'texte': f'Carte {i}', 'id_util': None})
        reponse = client.get('/afficher_cartes')
        assert reponse.status_code == 201
        assert len(reponse.get_json()['cartes']) == 3


class TestAfficherCartesLibres:
    """Route GET /afficher_cartes_libres."""

    def test_toutes_libres_au_depart(self, client, seed_card):
        """Une carte sans id_util doit apparaître dans la liste des libres."""
        reponse = client.get('/afficher_cartes_libres')
        assert reponse.status_code == 200
        ids = [c['id'] for c in reponse.get_json()['cartes']]
        assert seed_card in ids

    def test_carte_assignee_disparait(self, client, seed_card, seed_user):
        """Une carte assignée à un utilisateur n'est plus dans les libres."""
        client.post(f'/ajouter_une_carte_a_util/{seed_user}', json={
            'id_badge': seed_card})
        reponse = client.get('/afficher_cartes_libres')
        ids = [c['id'] for c in reponse.get_json()['cartes']]
        assert seed_card not in ids


class TestCreerEtAssignerCarte:
    """Route POST /creer_et_assigner_carte (cas B du flux d'ajout carte util)."""

    def test_creation_et_assignation_atomique(self, client, seed_user):
        """Une nouvelle carte est créée ET liée à l'utilisateur en une seule étape."""
        reponse = client.post('/creer_et_assigner_carte', json={
            'id_badge': 500,
            'texte':    'Carte créée',
            'id_util':  seed_user
        })
        assert reponse.status_code == 201
        # Vérifie que la carte est bien liée à l'utilisateur
        check = client.get('/verifier_carte/500').get_json()
        assert check['existe'] is True
        assert int(check['id_util']) == seed_user

    def test_creation_carte_existante_refusee(self, client, seed_card, seed_user):
        """Création refusée si la carte existe déjà → 409."""
        reponse = client.post('/creer_et_assigner_carte', json={
            'id_badge': seed_card, 'texte': 'x', 'id_util': seed_user})
        assert reponse.status_code == 409
