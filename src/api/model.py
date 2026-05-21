from src.Api.db import db


class Badge(db.Model):
    __tablename__ = 'badge'
    
    id_badge = db.Column(db.Integer, unique=True, primary_key=True)
    val_badge = db.Column(db.Integer, unique=False, nullable=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_util'))  
    der_connexion = db.Column(db.DateTime, unique=False)
    date_ajout = db.Column(db.DateTime, unique=True, nullable=False)  

    def __repr__(self):
        return f'<Badge {self.id_badge}>'


class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    
    id_util = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(20), unique=False, nullable=False)
    prenom = db.Column(db.String(20), unique=False, nullable=False)
    badges = db.relationship('Badge', backref='utilisateur', lazy=True)
    droits = db.Column(db.String(30),unique=False, nullable=False)

    def __repr__(self):
        return f'<Utilisateur {self.nom}>'
