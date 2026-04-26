from db import db
from model import Badge
from model import Utilisateur
from datetime import datetime
from config import app
from flask import request
from capteur import Lire_PIR, Lire_Badge, _badge_lock


    # ────────────────────────────────────────────────────────────────────────
    #                       ROUTES CARTES
    # ────────────────────────────────────────────────────────────────────────

@app.route("/ajouter_une_carte", methods=["POST"])
def ajouter_une_carte():
    data = request.get_json() 
    id_badge = data.get('id_badge')
    texte = data.get('texte')
    id_util = data.get('id_util')
    if not Badge.query.filter_by(id_badge=id_badge).first():
        carte = Badge(id_badge=id_badge, val_badge=texte, id_utilisateur=id_util if id_util not in ("None", "", None) else None, date_ajout=datetime.now())
        db.session.add(carte)
        db.session.commit()

        return {"Ajouté": "La carte a bien été ajoutée"}, 201
    else:
        return {"Erreur": "La carte existe déjà"}, 404

@app.route("/lire_badge", methods=["GET"])
def lire_badge():
    if _badge_lock.locked():  # ← si une lecture est déjà en cours, on refuse
        return {"Erreur": "Lecture déjà en cours"}, 429
    id, text = Lire_Badge(False)
    return {"id": str(id), "texte": text.strip()}, 200

@app.route("/modifier_une_carte/<id_badge>", methods=["GET", "POST"])
def modifier_une_carte(id_badge):
    if  request.method == "GET":
        carte = Badge.query.filter_by(id_badge=id_badge).first()

        if carte:    
            return {"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout}, 201
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
    carte = Badge.query.filter_by(id_badge=id_badge).first()
    print(carte)
    if carte:
        db.session.delete(carte)
        db.session.commit()
        return {"Effacé" : "La carte à bien été supprimé"}, 201
    return {"Erreur" : "Erreur"}, 404


@app.route("/afficher_cartes", methods=["GET"])
def afficher_cartes():
    cartes = Badge.query.all()
    return {"cartes": [{"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout} for carte in cartes]}, 201

    # ────────────────────────────────────────────────────────────────────────
    #                       ROUTES UTILISATEUR
    # ────────────────────────────────────────────────────────────────────────


@app.route("/ajouter_un_utilisateur/<id>", methods=["POST"])
def ajouter_un_utilisateur():
    if not Utilisateur.query.filter_by(id=id).first():
        util = Utilisateur.query.filter_by(id=id).first()
        data = request.get_json()
        if "id" in data:
            util.id = data['id']

        if "nom" in data:
            util.nom = data['nom']

        if "prenom" in data:
            util.prenom = data['prenom']

        if "badges" in data:
            util.badges = data['badges']

        if "droits" in data:
            util.droits = data['droits']

        db.session.add(util)
        db.session.commit()
        # Retourne un dictionnaire propre
        return {"Ajouté": "L'utilisateur a bien été ajouté"}, 201
    return {"Erreur" : "L'utilisateur n'a pas pu être ajouté"}, 404


@app.route("/modifier_un_utilisateur/<id>", methods=["GET", "POST"])
def modifier_un_utilisateur(id):
    if  request.method == "GET":
        util = Utilisateur.query.filter_by(id=id).first()

        if util:    
            return {"id": util.id, "nom": util.nom, "prenom": util.prenom, "badges": util.badges, "droit": util.droits}, 201
    elif request.method == "POST":
        util = Utilisateur.query.filter_by(id=id).first()
        data = request.get_json()
        if "id" in data:
            util.id = data["id"]
        if "nom" in data:
            util.nom = data["nom"].replace("\x00", "").strip()
        if "prenom" in data:
            util.prenom = data["prenom"].replace("\x00", "").strip()
        db.session.commit()
        return {"Utilisateur": "La modification a été effectuée"}, 200


    return {"error": "L'utilisateur n'existe pas"}, 404


@app.route("/supprimer_un_utilisateur/<id>", methods=["GET"])
def supprimer_un_utilisateur(id):
    util = Utilisateur.query.filter_by(id=id)
    if util:
        db.session.delete(util)
        db.session.commit()
        return {"Effacé" : "L'utilisateur à bien été supprimé"}, 201
    return {"Erreur" : "Erreur"}, 404


@app.route("/afficher_utilisateurs", methods=["GET"])
def afficher_util():
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
#                           TEST
# ────────────────────────────────────────────────────────────────────────

@app.route("/test_PIR", methods=["GET"])
def test_PIR():
    return Lire_PIR()

@app.route("/test_LB", methods=["GET"])
def test_LB():
    return lire_badge()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)