import tkinter
from tkinter import messagebox, ttk
import json

from Outils.requete_api import envoi_requete
from Outils.parametres import *


def charger_carte(self):
    """Récupère la liste des cartes depuis le serveur et remplit le tableau."""
    response = envoi_requete(ip=IP, port=5000, endpoint="/afficher_cartes")
    try:
        parsed = json.loads(response)
        self.donnee_cartes = parsed.get("cartes", parsed) if isinstance(parsed, dict) else parsed
        self.arbre_carte.delete(*self.arbre_carte.get_children())
        for card in self.donnee_cartes:
            self.arbre_carte.insert("", "end", values=(
                card.get("id", ""),
                card.get("texte", ""),
                card.get("id_util", ""),
                card.get("date_ajout", "")
            ))
    except Exception:
        messagebox.showerror("Erreur",
                             f"Impossible de récupérer les cartes :\n{response}")
        
def ajouter_carte(self):
    """Ouvre le formulaire d'ajout d'une nouvelle carte."""
    def submit(data, win):
        res = envoi_requete(ip=IP, port=5000,
                           endpoint="/ajouter_une_carte", valeur=data)
        messagebox.showinfo("Résultat", res, parent=win)
        self.charger_carte()
        win.destroy()
    self._modal("Ajouter une carte",
                [("id", "ID Badge"), ("texte", "Texte"),
                 ("id_util", "ID Utilisateur")], submit)
    
def modifier_carte(self):
    """Ouvre le formulaire de modification de la carte sélectionnée dans le tableau."""
    sel = self.arbre_carte.selection()
    if not sel:
        return
    vals = self.arbre_carte.item(sel[0], "values")
    prefill = {"id": vals[0], "texte": vals[1], "id_util": vals[2]}
    def submit(data, win):
        res = envoi_requete(ip=IP, port=5000,
                           endpoint=f"/modifier_une_carte/{data['id']}",
                           valeur=data)
        messagebox.showinfo("Résultat", res, parent=win)
        self.charger_carte()
        win.destroy()
    self._modal("Modifier une carte",
                [("id", "ID Badge"), ("texte", "Texte"),
                 ("id_util", "ID Utilisateur")], submit, prefill=prefill)
    
def supprimer_carte(self):
    """Supprime la carte sélectionnée après confirmation de l'utilisateur."""
    sel = self.arbre_carte.selection()
    if not sel:
        return
    card_id = self.arbre_carte.item(sel[0], "values")[0]
    print(card_id, sel)
    if not messagebox.askyesno("Confirmer", f"Supprimer la carte {card_id} ?"):
        return
    res = envoi_requete(ip=IP, port=5000,
                       endpoint=f"/supprimer_une_carte/{card_id}")
    messagebox.showinfo("Résultat", res)
    charger_carte(self)