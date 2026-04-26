import tkinter
from tkinter import messagebox, ttk
import json
import threading
import requests

from Outils.requete_api import envoi_requete
from Outils.parametres import *
 


def charger_carte(self):
    """Récupère la liste des cartes depuis le serveur et remplit le tableau."""
    reponse = envoi_requete(ip=IP, port=5000, endpoint="/afficher_cartes")
    try:
        parsed = json.loads(reponse)
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
                             f"Impossible de récupérer les cartes :\n{reponse}")
        
# def ajouter_carte(self):
#     """Ouvre le formulaire d'ajout d'une nouvelle carte."""
#     def submit(data, win):
#         reponse = envoi_requete(ip=IP, port=5000,
#                            endpoint="/ajouter_une_carte", valeur=data)
#         messagebox.showinfo("Résultat", reponse, parent=win)
#         self.charger_carte()
#         win.destroy()
#     # self._modal("Ajouter une carte",
#     #             [("id_badge", "ID Badge"), ("texte", "Texte"),
#     #              ("id_util", "ID Utilisateur")], submit)
    
def modifier_carte(self):
    """Ouvre le formulaire de modification de la carte sélectionnée dans le tableau."""
    sel = self.arbre_carte.selection()
    if not sel:
        return
    vals = self.arbre_carte.item(sel[0], "values")
    prefill = {"id_badge": vals[0], "texte": vals[1], "id_util": vals[2]}
    def submit(data, win):
        reponse = envoi_requete(ip=IP, port=5000,
                           endpoint=f"/modifier_une_carte/{data['id_badge']}",
                           valeur=data)
        messagebox.showinfo("Résultat", reponse, parent=win)        
        win.destroy()
        charger_carte(self)
        
    self._modal("Modifier une carte",
                [("id_badge", "ID Badge"), ("texte", "Texte"),
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
    reponse = envoi_requete(ip=IP, port=5000,
                       endpoint=f"/supprimer_une_carte/{card_id}")
    messagebox.showinfo("Résultat", reponse)
    charger_carte(self)

def fenetre_scan(self, on_card_scanned=None):
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
                    bg=BG, fg=TEXT_DIM, font=("Segoe UI", 9)).pack(pady=(0, 10))

        cancelled = [False]  # flag mutable accessible dans le thread

        def annuler():
            cancelled[0] = True
            win.destroy()

        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20)
        footer = tkinter.Frame(win, bg=BG, padx=20, pady=12)
        footer.pack(fill="x")
        tkinter.Button(footer, text="Annuler", command=annuler,
                   bg=BG, fg=TEXT, relief="flat", bd=0,
                   padx=10, pady=5, font=FONT,
                   activebackground=BORDER, cursor="hand2").pack(side="right")

        win.geometry("360x160")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

        def lire_badge_thread():
            try:
                resp = requests.get(f"http://{IP}:5000/lire_badge", timeout=30)
                print(f"[DEBUG] Réponse brute : {resp.text}")
                result = resp.json()
                print(f"[DEBUG] Result parsé : {result}")
            except Exception as e:
                print(f"[DEBUG] Erreur thread : {type(e).__name__} → {e}")
                result = None

            print(f"[DEBUG] cancelled : {cancelled[0]}")
            print(f"[DEBUG] on_card_scanned : {on_card_scanned}")

            if cancelled[0]:
                return

            def callback():
                print(f"[DEBUG] callback exécuté")
                print(f"[DEBUG] win exists : {win.winfo_exists()}")
                if not win.winfo_exists():
                    return
                if result and "id" in result:
                    print(f"[DEBUG] ID trouvé : {result['id']}, appel on_card_scanned")
                    win.destroy()
                    if on_card_scanned:
                        on_card_scanned(result["id"])
                else:
                    print(f"[DEBUG] Pas d'ID dans result : {result}")
                    status_var.set("Échec de la lecture, réessayez.")

            win.after(0, callback)
        threading.Thread(target=lire_badge_thread, daemon=True).start()    
