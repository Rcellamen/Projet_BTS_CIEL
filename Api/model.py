from flask import Flask
from run import db


class Badge(db.Model):
    __tablename__ = 'badge'
    
    id_badge = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    der_connexion = db.Column(db.DateTime, unique=False, nullable=False)

    def __repr__(self):
        return f'<Badge {self.id_badge}>'


class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), unique=False, nullable=False)
    badges = db.relationship('Badge', backref='utilisateur', lazy=True)
    
    def __repr__(self):
        return f'<Utilisateur {self.nom}>'
