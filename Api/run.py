"""
Point d'entrée de l'API Flask du système de sûreté.

Expose les routes REST permettant à l'IHM (CustomTkinter) de :
    - Gérer les cartes RFID et les utilisateurs en base SQLite
    - Piloter et lire les capteurs hardware (RFID, PIR, porte)
    - Évaluer les droits d'accès (Accès Libre / Accès Restreint)
"""

from db import db
from model import Badge, Utilisateur
from datetime import datetime
from config import app
from flask import request
from capteur import Lire_PIR, Lire_Badge, Lire_Porte, _badge_lock


# ────────────────────────────────────────────────────────────────────────
#                       ROUTES CARTES
# ────────────────────────────────────────────────────────────────────────

@app.route("/ajouter_une_carte", methods=["POST"])
def ajouter_une_carte():
    """
    Ajoute une nouvelle carte RFID en base.

    Attend un JSON : {"id_badge": int, "texte": str, "id_util": int|None}
    Retourne 201 si la carte a été créée, 404 si l'id existe déjà.
    """
    data = request.get_json()
    id_badge = data.get('id_badge')
    texte = data.get('texte')
    id_util = data.get('id_util')
    if not Badge.query.filter_by(id_badge=id_badge).first():
        carte = Badge(
            id_badge=id_badge,
            val_badge=texte if texte not in ("None", "", None) else None,
            id_utilisateur=id_util if id_util not in ("None", "", None) else None,
            date_ajout=datetime.now()
        )
        db.session.add(carte)
        db.session.commit()
        return {"Ajouté": "La carte a bien été ajoutée"}, 201
    else:
        return {"Erreur": "La carte existe déjà"}, 404


@app.route("/verifier_carte/<int:id_badge>", methods=["GET"])
def verifier_carte(id_badge):
    """
    Vérifie si une carte est déjà présente en base.

    Retourne :
        {"existe": True,  "id_util": "<id_util ou None>"} si trouvée
        {"existe": False} sinon.
    """
    carte = Badge.query.filter_by(id_badge=id_badge).first()
    if carte:
        return {"existe": True, "id_util": str(carte.id_utilisateur)}, 200
    return {"existe": False}, 200


@app.route("/creer_et_assigner_carte", methods=["POST"])
def creer_et_assigner_carte():
    """
    Crée une nouvelle carte RFID et l'associe immédiatement à un utilisateur.

    Attend un JSON : {"id_badge": int, "texte": str, "id_util": int}.
    Retourne 201 si la création réussit, 409 si la carte existe déjà.
    """
    data = request.get_json()
    id_badge = data.get("id_badge")
    texte    = (data.get("texte") or "").strip()
    id_util  = data.get("id_util")

    if Badge.query.filter_by(id_badge=id_badge).first():
        return {"Erreur": "La carte existe déjà"}, 409

    carte = Badge(
        id_badge=id_badge,
        val_badge=texte,
        id_utilisateur=id_util if id_util not in ("None", "", None) else None,
        date_ajout=datetime.now()
    )
    db.session.add(carte)
    db.session.commit()
    return {"Ajouté": "Carte créée et assignée à l'utilisateur"}, 201


@app.route("/modifier_une_carte/<id_badge>", methods=["GET", "POST"])
def modifier_une_carte(id_badge):
    """
    GET  : retourne les informations d'une carte donnée.
    POST : modifie les champs (texte, id_util) de la carte.
    """
    if  request.method == "GET":
        carte = Badge.query.filter_by(id_badge=id_badge).first()

        if carte:
            return {
                "id": carte.id_badge,
                "texte": carte.val_badge,
                "id_util": carte.id_utilisateur,
                "derniere_connexion": carte.der_connexion,
                "date_ajout": carte.date_ajout
            }, 201
    elif request.method == "POST":
        carte = Badge.query.filter_by(id_badge=id_badge).first()
        data = request.get_json()
        if "id_badge" in data:
            carte.id_badge = data["id_badge"]
        if "texte" in data:
            carte.val_badge = data["texte"].replace("\x00", "").strip()
        if "id_util" in data:
            carte.id_utilisateur = data["id_util"] if data["id_util"] not in ("None", "", None) else None
        db.session.commit()
        return {"Carte": "La modification a été effectuée"}, 200

    return {"error": "La carte n'existe pas"}, 404


@app.route("/supprimer_une_carte/<id_badge>", methods=["GET"])
def supprimer_une_carte(id_badge):
    """Supprime une carte de la base à partir de son id_badge."""
    carte = Badge.query.filter_by(id_badge=id_badge).first()
    if carte:
        db.session.delete(carte)
        db.session.commit()
        return {"Effacé" : "La carte à bien été supprimé"}, 201
    return {"Erreur" : "Erreur"}, 404


@app.route("/afficher_cartes", methods=["GET"])
def afficher_cartes():
    """Retourne la liste de toutes les cartes enregistrées."""
    cartes = Badge.query.all()
    return {"cartes": [{
        "id": carte.id_badge,
        "texte": carte.val_badge,
        "id_util": carte.id_utilisateur,
        "derniere_connexion": carte.der_connexion,
        "date_ajout": carte.date_ajout
    } for carte in cartes]}, 201


# ────────────────────────────────────────────────────────────────────────
#                       ROUTES UTILISATEUR
# ────────────────────────────────────────────────────────────────────────

@app.route("/ajouter_un_utilisateur", methods=["POST"])
def ajouter_un_utilisateur():
    """
    Crée un nouvel utilisateur en base.

    Attend un JSON : {"nom": str, "prenom": str, "droits": str}.
    """
    data = request.get_json()
    util = Utilisateur(
        nom=data.get('nom', '').strip(),
        prenom=data.get('prenom', '').strip(),
        droits=data.get('droits', '')
    )
    db.session.add(util)
    db.session.commit()
    return {"Ajouté": "L'utilisateur a bien été ajouté"}, 201


@app.route("/modifier_un_utilisateur/<id_util>", methods=["GET", "POST"])
def modifier_un_utilisateur(id_util):
    """
    GET  : retourne les informations d'un utilisateur donné.
    POST : modifie les champs (nom, prénom, droits) de l'utilisateur.
    """
    if  request.method == "GET":
        util = Utilisateur.query.filter_by(id_util=id_util).first()

        if util:
            return {
                "id": util.id_util,
                "nom": util.nom,
                "prenom": util.prenom,
                "badges": [b.id_badge for b in util.badges],
                "droit": util.droits
            }, 201
    elif request.method == "POST":
        util = Utilisateur.query.filter_by(id_util=id_util).first()
        data = request.get_json()
        if "id_util" in data:
            util.id_util = data["id_util"]
        if "nom" in data:
            util.nom = data["nom"].replace("\x00", "").strip()
        if "prenom" in data:
            util.prenom = data["prenom"].replace("\x00", "").strip()
        if "droits" in data:
            util.droits = data["droits"]
        db.session.commit()
        return {"Utilisateur": "La modification a été effectuée"}, 200

    return {"error": "L'utilisateur n'existe pas"}, 404


@app.route("/supprimer_un_utilisateur/<id_util>", methods=["GET"])
def supprimer_un_utilisateur(id_util):
    """Supprime un utilisateur de la base à partir de son id_util."""
    util = Utilisateur.query.filter_by(id_util=id_util).first()
    if util:
        db.session.delete(util)
        db.session.commit()
        return {"Effacé": "L'utilisateur à bien été supprimé"}, 201
    return {"Erreur" : "Erreur"}, 404


@app.route("/ajouter_une_carte_a_util/<int:id_util>", methods=["POST"])
def ajouter_une_carte_a_util(id_util):
    """
    Assigne une carte EXISTANTE à un utilisateur EXISTANT.

    Attend un JSON : {"id_badge": int}.
    Retourne 200 si l'assignation réussit, 404 si badge ou utilisateur absent.
    """
    data = request.get_json()
    id_badge = data.get('id_badge')

    badge = Badge.query.filter_by(id_badge=id_badge).first()
    if not badge:
        return {"Erreur": "Badge introuvable"}, 404

    util = Utilisateur.query.filter_by(id_util=id_util).first()
    if not util:
        return {"Erreur": "Utilisateur introuvable"}, 404

    badge.id_utilisateur = id_util
    db.session.commit()
    return {"Modifié": f"Badge {id_badge} assigné à l'utilisateur {id_util}"}, 200


@app.route("/afficher_utilisateurs", methods=["GET"])
def afficher_util():
    """Retourne la liste de tous les utilisateurs enregistrés."""
    utils = Utilisateur.query.all()
    return {"utils": [
        {
            "id_util":  util.id_util,
            "nom":      util.nom,
            "prenom":   util.prenom,
            "badges":   [b.id_badge for b in util.badges],
            "droits":   util.droits
        }
        for util in utils
    ]}, 200


# ────────────────────────────────────────────────────────────────────────
#                           CAPTEURS / ACCÈS
# ────────────────────────────────────────────────────────────────────────

@app.route("/lire_badge", methods=["GET"])
def lire_badge():
    """
    Lance une lecture RFID (polling, timeout 30s) et met à jour la dernière
    connexion de la carte si elle existe en base. Retourne toujours du JSON
    pour faciliter le traitement côté IHM.

    Codes HTTP :
        200 : badge lu avec succès
        408 : timeout, aucun badge détecté
        429 : une lecture est déjà en cours
        500 : erreur hardware côté Pi
    """
    if _badge_lock.locked():
        return {"Erreur": "Lecture déjà en cours"}, 429
    try:
        id_badge, text = Lire_Badge(False, timeout=30)
    except Exception as e:
        return {"Erreur": f"Lecture impossible : {e}"}, 500

    if id_badge == -1:
        return {"Erreur": "Aucun badge détecté (timeout)"}, 408

    carte = Badge.query.filter_by(id_badge=id_badge).first()
    if carte:
        carte.der_connexion = datetime.now()
        db.session.commit()
    return {"id" : str(id_badge), "texte": (text or "").strip()}, 200


@app.route("/test_PIR", methods=["GET"])
def test_PIR():
    """Retourne l'état instantané du capteur de mouvement PIR."""
    return Lire_PIR()


@app.route("/test_porte", methods=["GET"])
def test_porte():
    """Retourne l'état instantané du détecteur d'ouverture de porte."""
    return Lire_Porte()


@app.route("/test_LB", methods=["GET"])
def test_LB():
    """Test simple du lecteur de badge : retourne id + dernière connexion."""
    if _badge_lock.locked():
        return {"Erreur": "Lecture déjà en cours"}, 429
    try:
        id_badge, text = Lire_Badge(False, timeout=30)
    except Exception as e:
        return {"Erreur": f"Lecture impossible : {e}"}, 500

    if id_badge == -1:
        return {"Erreur": "Aucun badge détecté (timeout)"}, 408

    carte = Badge.query.filter_by(id_badge=id_badge).first()
    if carte:
        carte.der_connexion = datetime.now()
        db.session.commit()
    der = carte.der_connexion if carte else None
    return {"id" : str(id_badge), "dernière connexion": der}, 200


@app.route("/scanner_acces/<mode>", methods=["GET"])
def scanner_acces(mode):
    """
    Scanne un badge RFID et évalue le droit d'accès selon le mode de la zone.

    :param mode: 'libre'     → tout badge connu est autorisé
                 'restreint' → seuls les utilisateurs ayant un droit
                               'AT (Accès total)' sont autorisés.

    Retourne un JSON :
        {
            "id_badge":  str,
            "nom":       str ou None,
            "prenom":    str ou None,
            "droits":    str ou None,
            "autorise":  bool,
            "motif":     str  (raison de la décision)
        }
    """
    if _badge_lock.locked():
        return {"Erreur": "Lecture déjà en cours"}, 429

    try:
        id_badge, _ = Lire_Badge(False, timeout=30)
    except Exception as e:
        return {"Erreur": f"Lecture impossible : {e}"}, 500

    if id_badge == -1:
        return {"Erreur": "Aucun badge détecté (timeout)"}, 408

    carte = Badge.query.filter_by(id_badge=id_badge).first()

    # Cas 1 : badge inconnu → toujours refusé
    if not carte:
        return {
            "id_badge": str(id_badge),
            "nom": None,
            "prenom": None,
            "droits": None,
            "autorise": False,
            "motif": "Badge inconnu"
        }, 200

    # Met à jour la date de dernière connexion
    carte.der_connexion = datetime.now()
    db.session.commit()

    # Cas 2 : badge connu mais non assigné → refusé
    util = Utilisateur.query.filter_by(id_util=carte.id_utilisateur).first()
    if not util:
        return {
            "id_badge": str(id_badge),
            "nom": None,
            "prenom": None,
            "droits": None,
            "autorise": False,
            "motif": "Badge non assigné à un utilisateur"
        }, 200

    # Cas 3 : badge connu + utilisateur trouvé → décision selon le mode
    mode = (mode or "").lower().strip()
    if mode == "libre":
        autorise = True
        motif = "Droit AL - Accès autorisé"
    else:  # 'restreint' ou tout autre valeur par défaut
        autorise = util.droits.startswith("AT")
        motif = ("Droit AT - Accès autorisé" if autorise
                 else "Accès refusé - Droits insuffisant")

    return {
        "id_badge": str(id_badge),
        "nom":      util.nom,
        "prenom":   util.prenom,
        "droits":   util.droits,
        "autorise": autorise,
        "motif":    motif
    }, 200


@app.route("/kill_thread", methods=["POST"])
def kill_thread():
    """Tente de relâcher le verrou du lecteur de badge (debug)."""
    try:
        _badge_lock.release()
    except RuntimeError:
        pass
    return {"statut": "ok"}, 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)
