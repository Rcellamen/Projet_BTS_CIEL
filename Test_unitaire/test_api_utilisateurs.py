"""
Tests unitaires des routes de gestion des utilisateurs (Api/run.py).

Couvre la création (avec ou sans assignation simultanée d'une carte),
la consultation, la modification, la suppression, et le listing des
utilisateurs, ainsi que l'assignation d'une carte existante.
"""

import pytest


class TestAjouterUnUtilisateur:
    """Route POST /ajouter_un_utilisateur."""

    def test_ajout_utilisateur_nominal(self, client):
        """Création simple d'un utilisateur sans carte → 201."""
        resp = client.post('/ajouter_un_utilisateur', json={
            'nom':    'Durand',
            'prenom': 'Marie',
            'droits': 'AT (Accès total)'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'id_util' in data
        assert isinstance(data['id_util'], int)
        assert "Ajout" in data['Ajoute']

    def test_ajout_utilisateur_avec_id_badge(self, client, seed_card):
        """Ajout avec id_badge → la carte doit être liée à l'utilisateur."""
        resp = client.post('/ajouter_un_utilisateur', json={
            'nom':      'Petit',
            'prenom':   'Luc',
            'droits':   'AR (Accès restreint)',
            'id_badge': seed_card
        })
        assert resp.status_code == 201
        data = resp.get_json()
        id_util = data['id_util']
        # Vérifie que la carte est bien liée
        check = client.get(f'/verifier_carte/{seed_card}').get_json()
        assert int(check['id_util']) == id_util
        assert f"carte {seed_card}" in data['Ajoute']

    def test_ajout_utilisateur_id_badge_aucune(self, client):
        """id_badge='Aucune' doit créer l'utilisateur sans assignation."""
        resp = client.post('/ajouter_un_utilisateur', json={
            'nom':      'Roux',
            'prenom':   'Anne',
            'droits':   'AT (Accès total)',
            'id_badge': 'Aucune'
        })
        assert resp.status_code == 201
        # Pas de carte assignée → message simple sans mention de carte
        assert "carte" not in resp.get_json()['Ajoute']

    def test_ajout_utilisateur_id_badge_inconnu(self, client):
        """id_badge inexistant → utilisateur créé mais aucune assignation."""
        resp = client.post('/ajouter_un_utilisateur', json={
            'nom':      'Blanc',
            'prenom':   'Eric',
            'droits':   'AR (Accès restreint)',
            'id_badge': 99999
        })
        assert resp.status_code == 201
        # L'utilisateur est créé mais le message ne mentionne pas la carte
        assert "carte 99999" not in resp.get_json()['Ajoute']


class TestModifierUnUtilisateur:
    """Route GET/POST /modifier_un_utilisateur/<id>."""

    def test_get_utilisateur_existant(self, client, seed_user):
        """GET sur utilisateur existant retourne ses informations."""
        resp = client.get(f'/modifier_un_utilisateur/{seed_user}')
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['id']     == seed_user
        assert data['nom']    == 'Dupont'
        assert data['prenom'] == 'Jean'
        assert data['droit']  == 'AT (Accès total)'

    def test_get_utilisateur_inexistant(self, client):
        """GET sur utilisateur inconnu → 404."""
        resp = client.get('/modifier_un_utilisateur/99999')
        assert resp.status_code == 404

    def test_modification_nom_prenom(self, client, seed_user):
        """POST modifie nom et prénom correctement."""
        resp = client.post(f'/modifier_un_utilisateur/{seed_user}', json={
            'nom':    'Nouveau',
            'prenom': 'Prenom'
        })
        assert resp.status_code == 200
        # Vérifie la persistance
        check = client.get(f'/modifier_un_utilisateur/{seed_user}').get_json()
        assert check['nom']    == 'Nouveau'
        assert check['prenom'] == 'Prenom'

    def test_modification_droits(self, client, seed_user):
        """POST modifie les droits correctement."""
        resp = client.post(f'/modifier_un_utilisateur/{seed_user}', json={
            'droits': 'AR (Accès restreint)'
        })
        assert resp.status_code == 200
        check = client.get(f'/modifier_un_utilisateur/{seed_user}').get_json()
        assert check['droit'] == 'AR (Accès restreint)'


class TestSupprimerUnUtilisateur:
    """Route GET /supprimer_un_utilisateur/<id>."""

    def test_suppression_utilisateur_existant(self, client, seed_user):
        """Suppression d'un utilisateur existant → 201."""
        resp = client.get(f'/supprimer_un_utilisateur/{seed_user}')
        assert resp.status_code == 201
        # L'utilisateur ne doit plus exister
        check = client.get(f'/modifier_un_utilisateur/{seed_user}')
        assert check.status_code == 404

    def test_suppression_utilisateur_inexistant(self, client):
        """Suppression d'un utilisateur inconnu → 404."""
        resp = client.get('/supprimer_un_utilisateur/99999')
        assert resp.status_code == 404


class TestAfficherUtilisateurs:
    """Route GET /afficher_utilisateurs."""

    def test_liste_vide_au_demarrage(self, client):
        """Sans utilisateur, retourne 200 et liste vide."""
        resp = client.get('/afficher_utilisateurs')
        assert resp.status_code == 200
        assert resp.get_json()['utils'] == []

    def test_liste_apres_plusieurs_ajouts(self, client):
        """Plusieurs ajouts → tous les utilisateurs apparaissent."""
        for i in range(3):
            client.post('/ajouter_un_utilisateur', json={
                'nom': f'Nom{i}', 'prenom': f'Prenom{i}',
                'droits': 'AT (Accès total)'
            })
        resp = client.get('/afficher_utilisateurs')
        assert resp.status_code == 200
        utils = resp.get_json()['utils']
        assert len(utils) == 3
        # Chaque utilisateur doit avoir les champs attendus
        for u in utils:
            assert 'id_util' in u
            assert 'nom'     in u
            assert 'prenom'  in u
            assert 'droits'  in u
            assert 'badges'  in u


class TestAjouterUneCarteAUtil:
    """Route POST /ajouter_une_carte_a_util/<id_util>."""

    def test_assignation_nominale(self, client, seed_user, seed_card):
        """Assignation carte existante → utilisateur existant → 200."""
        resp = client.post(f'/ajouter_une_carte_a_util/{seed_user}', json={
            'id_badge': seed_card
        })
        assert resp.status_code == 200
        # Vérifie la liaison
        check = client.get(f'/verifier_carte/{seed_card}').get_json()
        assert int(check['id_util']) == seed_user

    def test_assignation_badge_inexistant(self, client, seed_user):
        """Badge inconnu → 404."""
        resp = client.post(f'/ajouter_une_carte_a_util/{seed_user}', json={
            'id_badge': 99999
        })
        assert resp.status_code == 404
        assert "Badge" in resp.get_json()['Erreur']

    def test_assignation_utilisateur_inexistant(self, client, seed_card):
        """Utilisateur inconnu → 404."""
        resp = client.post('/ajouter_une_carte_a_util/99999', json={
            'id_badge': seed_card
        })
        assert resp.status_code == 404
        assert "Utilisateur" in resp.get_json()['Erreur']
