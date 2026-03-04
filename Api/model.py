from db import db


class Badge(db.Model):
    __tablename__ = 'badge'
    
    id_badge = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    val_badge = db.Column(db.Integer, unique=False, nullable=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))  
    der_connexion = db.Column(db.DateTime, unique=False)
    date_ajout = db.Column(db.DateTime, nullable=False)  



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
