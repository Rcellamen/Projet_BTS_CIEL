import tkinter
from tkinter import messagebox, ttk
import json

from Outils.requete_api import envoi_requete
from Outils.parametres import *

def charger_util(self):
    url = f"http://{IP}:5000/afficher_utilisateurs"
    print(f"[DEBUG] URL appelée : {url}")
    reponse = envoi_requete(ip=IP, port=5000, endpoint="/afficher_utilisateurs")
    print(f"[DEBUG] Réponse : {reponse}")
    try:
        parsed = json.loads(reponse)
        self.donnee_util = parsed.get("utils", [])
        self.arbre_util.delete(*self.arbre_util.get_children())
        for util in self.donnee_util:
            self.arbre_util.insert("", "end", values=(
                util.get("id_util",  ""),
                util.get("nom",      ""),
                util.get("prenom",   ""),
                util.get("badges",   ""),
                util.get("droits",   "")
            ))
    except Exception:
        messagebox.showerror("Erreur",
                             f"Impossible de récupérer les utilisateurs :\n{reponse}")
         


def ajouter_util(self):
    def submit(data, win):
        reponse = envoi_requete(ip=IP, port=5000,
                           endpoint="/ajouter_un_utilisateur", valeur=data)
        messagebox.showinfo("Résultat", reponse, parent=win)
        win.destroy()
        charger_util(self)

    self._modal("Ajouter un utilisateur",
                [
                    ("id",     "ID Utilisateur"),
                    ("nom",    "Nom"),
                    ("prenom", "Prenom"),
                    ("Badges", "Cartes"),
                    ("droits", "Droits", "combo",          # ← type
                     ["-----", "AT (Accès total)", "AR (Accès restreint)"]),
                ], submit)

def modifier_util(self):
    """Ouvre le formulaire de modification de l'utilisateur sélectionnée dans le tableau."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    vals = self.arbre_util.item(sel[0], "values")
    prefill = {"id": vals[0], "nom": vals[1], "prenom": vals[2], "badges" : vals[3], "droits" : vals[4]}
    def submit(data, win):
        reponse = envoi_requete(ip=IP, port=5000,
                           endpoint=f"/modifier_un_utilisateur/{data['id']}",
                           valeur=data)
        messagebox.showinfo("Résultat", reponse, parent=win)
        self.charger_util()
        win.destroy()
    self._modal("Modifier un utilisateur",
                [("id", "ID Utilisateur"), ("nom", "Nom"),
                 ("prenom", "Prenom"), ("badges", "Badges"), ("droits", "Droits")], submit, prefill=prefill)
    
def supprimer_util(self):
    """Supprime l'utilisateur sélectionné après confirmation de l'opérateur."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    id_util = self.arbre_carte.item(sel[0], "values")[0]
    if not messagebox.askyesno("Confirmer", f"Supprimer l'utilisateur {id_util} ?"):
        return
    reponse = envoi_requete(ip=IP, port=5000,
                       endpoint=f"/supprimer_un_utilisateur/{id_util}")
    messagebox.showinfo("Résultat", reponse)
    self.charger_util()

