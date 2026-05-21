"""
Outils dédiés à la gestion des cartes RFID côté IHM.

Contient :
    - Les opérations CRUD sur les cartes (chargement, modification, suppression).
    - La fenêtre modale de scan de carte (utilisée pour ajouter une carte).
"""

import tkinter
from tkinter import messagebox, ttk
import json
import threading
import requests

from src.app.Outils.requete_api import envoi_requete
from src.app.Outils.parametres import *


def charger_carte(self):
    """Récupère la liste des cartes depuis le serveur et remplit le tableau."""
    reponse = envoi_requete(RESEAU["IP"], port=5000, endpoint="/afficher_cartes")
    try:
        parsed = json.loads(reponse)
        self.donnee_cartes = parsed.get("cartes", parsed) if isinstance(parsed, dict) else parsed
        self.arbre_carte.delete(*self.arbre_carte.get_children())
        for card in self.donnee_cartes:
            self.arbre_carte.insert("", "end", values=(
                card.get("id", ""),
                card.get("texte", ""),
                card.get("id_util", ""),
                card.get("date_ajout", ""),
                card.get("der_connexion", "")
            ))
    except Exception:
        messagebox.showerror("Erreur",
                             f"Impossible de récupérer les cartes :\n{reponse}")
        
    
def modifier_carte(self):
    """Ouvre le formulaire de modification de la carte sélectionnée dans le tableau."""
    sel = self.arbre_carte.selection()
    if not sel:
        return
    vals = self.arbre_carte.item(sel[0], "values")
    prerempli = {"id_badge": vals[0], "texte": vals[1], "id_util": vals[2]}
    def valider(data, win):
        """Envoie la modification de la carte à l'API et rafraîchit la liste."""
        try:
            reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000,
                    endpoint=f"/modifier_une_carte/{data['id_badge']}",valeur=data))
        except Exception:
            reponse = {"Efface" : reponse.get("Erreur", "")}
        messagebox.showinfo("Résultat", reponse.get("Efface", ""), parent=win)
        win.destroy()
        charger_carte(self)

    self._modale("Modifier une carte",
                [("id_badge", "ID Badge"), ("texte", "Texte"),
                 ("id_util", "ID Utilisateur")], valider, prerempli=prerempli)
    
def supprimer_carte(self):
    """Supprime la carte sélectionnée après confirmation de l'utilisateur."""
    sel = self.arbre_carte.selection()
    if not sel:
        return
    id_carte = self.arbre_carte.item(sel[0], "values")[0]
    if not messagebox.askyesno("Confirmer", f"Supprimer la carte {id_carte} ?"):
        return
    try:
        reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000,
            endpoint=f"/supprimer_une_carte/{id_carte}"))
    except Exception:
        reponse = {"Efface": reponse.get("Erreur", "")}
    messagebox.showinfo("Résultat", reponse.get("Efface", ""))
    charger_carte(self)

def fenetre_scan_carte(self, quand_carte_scannee=None):
        """
        Ouvre une fenêtre 'Scanner une carte' qui interroge l'API en arrière-plan
        et appelle `quand_carte_scannee(id_badge)` dès qu'un badge est lu.

        :param quand_carte_scannee: rappel recevant l'id de la carte scannée.
        """
        win = tkinter.Toplevel(self)
        win.title("Scanner une carte")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        tkinter.Label(win, text="Scanner une carte", bg=BG, fg=TEXT,
                    font=FONT_BOLD).pack(anchor="w", padx=20, pady=(16, 4))
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20)

        body = tkinter.Frame(win, bg=BG, padx=20, pady=16)
        body.pack(fill="both")

        status_var = tkinter.StringVar(value="Veuillez approcher votre carte…")
        tkinter.Label(body, textvariable=status_var,
                    bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(pady=(0, 10))

        annule = [False]  # flag mutable accessible dans le thread

        def annuler():
            """
            Annule la demande de scan et ferme la fenêtre.
            Tente aussi de libérer le verrou côté API (au cas où une lecture
            précédente serait restée bloquée), pour ne pas bloquer la suivante.
            """
            annule[0] = True
            try:
                requests.post(f"http://{RESEAU['IP']}:5000/liberer_verrou", timeout=2)
            except Exception:
                pass
            win.destroy()

        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20)
        footer = tkinter.Frame(win, bg=BG, padx=20, pady=12)
        footer.pack(fill="x")
        tkinter.Button(footer, text="Annuler", command=annuler,
                   bg=BG, fg=TEXT, relief="flat", bd=0,
                   padx=10, pady=5, font=FONT_UI,
                   activebackground=BORDER, cursor="hand2").pack(side="right")

        win.geometry("360x160")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

        def tache_lecture_badge():
            """
            Thread d'arrière-plan qui interroge `/lire_badge` puis remet
            la main au thread Tkinter pour la mise à jour visuelle.
            Détaille la cause de l'échec (verrou bloqué, réseau, etc.).
            """
            result = None
            erreur = None
            try:
                resp = requests.get(f"http://{RESEAU['IP']}:5000/lire_badge", timeout=60)
                try:
                    result = resp.json()
                except ValueError:
                    erreur = f"Réponse non-JSON (HTTP {resp.status_code})"
            except Exception as e:
                erreur = str(e)

            if annule[0]:
                return

            def rappel():
                """Met à jour la fenêtre dans le thread principal Tkinter."""
                if not win.winfo_exists():
                    return
                if result and "id" in result and result["id"] not in (None, "-1", -1):
                    win.destroy()
                    if quand_carte_scannee:
                        quand_carte_scannee(result["id"])
                elif result and "Erreur" in result:
                    # Cas typique : verrou bloqué (HTTP 429)
                    status_var.set(
                        f"Échec : {result['Erreur']}.\n"
                        "Cliquez sur 'Réinitialiser le lecteur' depuis l'accueil."
                    )
                else:
                    status_var.set(
                        f"Échec de la lecture : {erreur or 'aucun badge détecté'}."
                    )

            win.after(0, rappel)
        threading.Thread(target=tache_lecture_badge, daemon=True).start()

