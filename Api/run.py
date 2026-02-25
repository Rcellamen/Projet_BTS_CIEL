from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from capteur import Lire_Badge
from model import Badge
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///LB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route("/ajouter_une_carte", methods=["GET", "POST"])
def ajouter_une_carte():
    id, text = Lire_Badge(False)
    carte = Badge(id_badge=id, texte=text, date_ajout=datetime.now())
    db.session.add(carte)
    db.session.commit()
    # Retourne un dictionnaire propre
    return {"id": id, "texte": text}, 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)

