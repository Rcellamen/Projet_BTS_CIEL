from capteur import Lire_Badge
from db import db
from model import Badge
from datetime import datetime
from config import app
from flask import request


@app.route("/ajouter_une_carte", methods=["GET"])
def ajouter_une_carte():
    id, text = Lire_Badge(False)
    if not Badge.query.filter_by(id_badge=id).first():
        carte = Badge(id_badge=id, val_badge=text, date_ajout=datetime.now())
        db.session.add(carte)
        db.session.commit()
        # Retourne un dictionnaire propre
        return {"id": id, "texte": text}, 201
    return {"Erreur" : "Erreur"}, 404

@app.route("/modifier_une_carte/<id_badge>", methods=["GET", "POST"])
def modifier_une_carte(id_badge):
    if  request.method == "GET":
        carte = Badge.query.filter_by(id_badge=id_badge).first()
    
        if carte:    
            return {"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout}, 201
    return {"error": "Carte not found"}, 404

@app.route("/afficher_cartes", methods=["GET"])
def afficher_cartes():
    cartes = Badge.query.all()
    return {"cartes": [{"id": carte.id_badge, "texte": carte.val_badge, "id_util": carte.id_utilisateur, "derniere_connexion": carte.der_connexion, "date_ajout": carte.date_ajout} for carte in cartes]}, 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)

