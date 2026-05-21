"""
Outils dédiés à la gestion des utilisateurs côté IHM.

Contient :
    - Les opérations CRUD sur les utilisateurs (chargement, ajout, modification,
      suppression).
    - La fenêtre modale de scan de carte utilisée pour assigner un badge à un
      utilisateur déjà sélectionné.
"""

import tkinter
from tkinter import messagebox, ttk
import json
import requests
import threading

from Outils.requete_api import envoi_requete
from Outils.parametres import *

def charger_util(self):
    """Récupère la liste des utilisateurs depuis l'API et remplit le tableau."""
    reponse = envoi_requete(RESEAU["IP"], port=5000, endpoint="/afficher_utilisateurs")
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
    """
    Ouvre le formulaire de création d'un nouvel utilisateur.

    Le formulaire propose en plus un combobox listant les ID des cartes RFID
    non encore attribuées (récupérées via /afficher_cartes_libres), pour
    permettre d'assigner immédiatement une carte au nouvel utilisateur.
    Sélectionner « Aucune » crée l'utilisateur sans carte.
    """
    # Récupère les cartes non assignées pour les proposer dans le formulaire
    cartes_libres = ["Aucune"]
    try:
        reponse_libres = envoi_requete(RESEAU["IP"], port=5000,
                                       endpoint="/afficher_cartes_libres")
        parsed = json.loads(reponse_libres)
        cartes_libres += [str(c["id"]) for c in parsed.get("cartes", [])]
    except Exception:
        # En cas d'erreur réseau, on conserve au moins « Aucune » dans le combo
        pass

    def valider(data, win):
        """Envoie la création de l'utilisateur à l'API et rafraîchit la liste."""
        # Normalise la valeur "Aucune" en None pour le payload JSON
        if data.get("id_badge") == "Aucune":
            data["id_badge"] = None
        try:
            reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000,
                           endpoint="/ajouter_un_utilisateur", valeur=data))
        except Exception as e:
            reponse = {"Ajoute": reponse.get("Erreur", "")}
        messagebox.showinfo("Resultat", reponse.get("Ajoute"), parent=win)
        win.destroy()
        charger_util(self)

    self._modale("Ajouter un utilisateur",
                [
                    ("nom",    "Nom"),
                    ("prenom", "Prenom"),
                    ("droits", "Droits", "combo",
                     ["-----", "AT (Accès total)", "AR (Accès restreint)"]),
                    ("id_badge", "Carte (optionnelle)", "combo", cartes_libres),
                ], valider)

def modifier_util(self):
    """Ouvre le formulaire de modification de l'utilisateur sélectionnée dans le tableau."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    vals = self.arbre_util.item(sel[0], "values")
    prerempli = {"id_util": vals[0], "nom": vals[1], "prenom": vals[2], "badges" : vals[3], "droits" : vals[4]}
    def valider(data, win):
        """Envoie la modification de l'utilisateur à l'API et rafraîchit la liste."""
        try:
            reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000,
                           endpoint=f"/modifier_un_utilisateur/{data['id_util']}",
                           valeur=data))
        except Exception:
            reponse = {"Modifie": reponse.get("Erreur", "")}
        messagebox.showinfo("Résultat", reponse.get("Modifie", ""))
        win.destroy()
        charger_util(self)

    self._modale("Modifier un utilisateur",
                [("id_util", "ID Utilisateur"),
                 ("nom", "Nom"),
                 ("prenom", "Prenom"),
                 ("badges", "Badges"),
                 ("droits", "Droits", "combo",
                 ["-----", "AT (Accès total)", "AR (Accès restreint)"])
                 ],
                 valider, prerempli=prerempli
                 )
    
def supprimer_util(self):
    """Supprime l'utilisateur sélectionné après confirmation de l'opérateur."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    id_util = self.arbre_util.item(sel[0], "values")[0]
    if not messagebox.askyesno("Confirmer", f"Supprimer l'utilisateur {id_util} ?"):
        return
    try:
        reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000,
                       endpoint=f"/supprimer_un_utilisateur/{id_util}"))
    except Exception:
        reponse = {"Efface": reponse.get("Erreur", "")}
    messagebox.showinfo("Résultat", reponse.get("Efface", ""))
    charger_util(self)


def ajouter_carte_util(self):
    """Ajoute une carte à un utilisateur selectionné"""
    sel = self.arbre_util.selection()
    if not sel:
        return
    id_util = self.arbre_util.item(sel[0], "values")[0]
    try: 
        reponse = json.loads(envoi_requete(RESEAU["IP"], port=5000, 
                                              endpoint=f"/ajouter_une_carte_a_util/{id_util}"))
    except Exception:
        reponse = {"Modifie" : reponse.get("Erreur", "")}
    messagebox.showinfo("Résultat", reponse.get("Modifie", ""))
    charger_util(self)


def fenetre_scan_util(self, quand_carte_scannee=None):
        """
        Ouvre la fenêtre 'Scanner une carte' utilisée dans le flux d'assignation
        d'un badge à un utilisateur. Le rappel `quand_carte_scannee` reçoit
        l'id de la carte lue ; il est ensuite responsable de vérifier si la carte
        existe en base et d'enchaîner avec la modale appropriée.

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
            Tente aussi de libérer le verrou côté API pour ne pas bloquer
            les futures lectures.
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
            """Thread d'arrière-plan : appelle `/lire_badge` puis remet la
            main au thread Tkinter via `win.after`. Détaille la cause de l'échec."""
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