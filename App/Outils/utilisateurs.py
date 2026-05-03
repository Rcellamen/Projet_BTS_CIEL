import tkinter
from tkinter import messagebox, ttk
import json
import requests
import threading

from Outils.requete_api import envoi_requete
from Outils.parametres import *

def charger_util(self):
    url = f"http://{IP}:5000/afficher_utilisateurs"
    reponse = envoi_requete(ip=IP, port=5000, endpoint="/afficher_utilisateurs")
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
        print(f"[DEBUG] reponse {reponse}")
        messagebox.showinfo("Résultat", reponse, parent=win)
        win.destroy()
        charger_util(self)

    self._modal("Ajouter un utilisateur",
                [
                    ("nom",    "Nom"),
                    ("prenom", "Prenom"),
                    ("droits", "Droits", "combo",          # ← type
                     ["-----", "AT (Accès total)", "AR (Accès restreint)"])
                ], submit)

def modifier_util(self):
    """Ouvre le formulaire de modification de l'utilisateur sélectionnée dans le tableau."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    vals = self.arbre_util.item(sel[0], "values")
    prefill = {"id_util": vals[0], "nom": vals[1], "prenom": vals[2], "badges" : vals[3], "droits" : vals[4]}
    def submit(data, win):
        reponse = envoi_requete(ip=IP, port=5000,
                           endpoint=f"/modifier_un_utilisateur/{data['id_util']}",
                           valeur=data)
        messagebox.showinfo("Résultat", reponse, parent=win)
        win.destroy()
        charger_util(self)
        
    self._modal("Modifier un utilisateur",
                [("id_util", "ID Utilisateur"),
                 ("nom", "Nom"),
                 ("prenom", "Prenom"),
                 ("badges", "Badges"),
                 ("droits", "Droits", "combo",
                 ["-----", "AT (Accès total)", "AR (Accès restreint)"])
                 ],
                 submit, prefill=prefill
                 )
    
def supprimer_util(self):
    """Supprime l'utilisateur sélectionné après confirmation de l'opérateur."""
    sel = self.arbre_util.selection()
    if not sel:
        return
    id_util = self.arbre_util.item(sel[0], "values")[0]
    if not messagebox.askyesno("Confirmer", f"Supprimer l'utilisateur {id_util} ?"):
        return
    reponse = envoi_requete(ip=IP, port=5000,
                       endpoint=f"/supprimer_un_utilisateur/{id_util}")
    messagebox.showinfo("Résultat", reponse)
    charger_util(self)


def ajouter_carte_util(self):
    """Ajoute une carte à un utilisateur selectionné"""
    sel = self.arbre_util.selection()
    if not sel:
        return
    id_util = self.arbre_util.item(sel[0], "values")[0]
    reponse = envoi_requete(ip=IP, port=5000, endpoint=f"/ajouter_une_carte_a_util/{id_util}")
    messagebox.showinfo("Résultat", reponse)
    charger_util(self)


def fenetre_scan_util(self, on_card_scanned=None):
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

        cancelled = [False]  # flag mutable accessible dans le thread

        def annuler():
            cancelled[0] = True
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

        def lire_badge_thread():
            try:
                resp = requests.get(f"http://{IP}:5000/lire_badge", timeout=30)
                result = resp.json()
            except Exception as e:
                result = None

            if cancelled[0]:
                return

            def callback():
                if not win.winfo_exists():
                    return
                if result and "id" in result:
                    win.destroy()
                    if on_card_scanned:
                        on_card_scanned(result["id"])
                else:
                    status_var.set("Échec de la lecture, réessayez.")

            win.after(0, callback)
        threading.Thread(target=lire_badge_thread, daemon=True).start()