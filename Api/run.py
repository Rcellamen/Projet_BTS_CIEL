#from capteur import Lire_Badge
from db import db
from model import Badge
from model import Utilisateur
from datetime import datetime
from config import app
from flask import request


    # ────────────────────────────────────────────────────────────────────────
    #                       ROUTES CARTES
    # ────────────────────────────────────────────────────────────────────────

@app.route("/ajouter_une_carte<id_badges>", methods=["POST"])
def ajouter_une_carte():
    if not Badge.query.filter_by(id_badge=id).first():
        carte = Badge.query.filter_by(id_badge=id).first()
        data = request.get_json()
        if "id" in data:
            carte.id_badges = data['id']

        if "nom" in data:
            carte.nom = data['nom']

        if "prenom" in data:
            carte.prenom = data['prenom']

        if "badges" in data:
            carte.badges = data['badges']

        if "droits" in data:
            carte.droits = data['droits']
               
        db.session.add(carte)
        db.session.commit()
        # Retourne un dictionnaire propre
        return {"Ajouté": "La carte a bien été ajouté"}, 201
    return {"Erreur" : "La carte n'a pas pu être ajouté"}, 404

@app.route("/modifier_une_carte/<id_badge>", methods=["GET", "POST"])
def modifier_une_carte(id_badge):
    if  request.method == "GET":
        carte = Badge.query.filter_by(id_badge=id_badge).first()

        if carte:    
            return {"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout}, 201
    elif request.method == "POST":
        carte = Badge.query.filter_by(id_badge=id_badge).first()
        data = request.get_json()
        if "id" in data:
            carte.id_badge = data["id"]
        if "texte" in data:
            carte.val_badge = data["texte"].replace("\x00", "").strip()
        if "id_util" in data:
            carte.id_utilisateur = data["id_util"] if data["id_util"] not in ("None", "", None) else None
        db.session.commit()
        return {"Carte": "La modification a été effectuée"}, 200


    return {"error": "La carte n'existe pas"}, 404

@app.route("/supprimer_une_carte/<id_badge>", methods=["GET"])
def supprimer_une_carte(id_badge):
    carte = Badge.query.filter_by(id_badge=id_badge)
    if carte:
        db.session.delete(carte)
        db.session.commit()
        return {"Effacé" : "La carte à bien été supprimé"}, 201
    return {"Erreur" : "Erreur"}, 404


@app.route("/afficher_cartes", methods=["GET"])
def afficher_cartes():
    cartes = Badge.query.all()
    return {"cartes": [{"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout} for carte in cartes]}, 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)



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
    util = Utilisateur.query.all()
    return {"Utilisateurs": [{"identifiant": util.id, "nom": util.nom, "prenom": util.prenom, "badge": util.badges, "droits" : util.droits} for util in util]}, 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)