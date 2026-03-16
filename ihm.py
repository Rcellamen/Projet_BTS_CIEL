import tkinter
from tkinter import messagebox, ttk
import requests
import json

# ════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

IP = "172.20.10.5"

BG       = "#f5f5f5"
SURFACE  = "#ffffff"
BORDER   = "#d0d0d0"
ACCENT   = "#2563eb"
TEXT     = "#1a1a1a"
TEXT_DIM = "#6b7280"
DANGER   = "#dc2626"

FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEAD = ("Segoe UI", 13, "bold")


# ════════════════════════════════════════════════════════════════════════════
#                           UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════

def send_request(ip, port=80, endpoint="/", valeur=None):
    """
    Envoie une requête HTTP au serveur.

    Si `valeur` est None, effectue un GET.
    Sinon, effectue un POST avec `valeur` sérialisé en JSON.
    Retourne le texte de la réponse, ou un message d'erreur en cas d'échec.
    """
    try:
        url = f"http://{ip}:{port}{endpoint}"
        if valeur is None:
            return requests.get(url, timeout=5).text
        return requests.post(url, timeout=5, json=valeur).text
    except requests.exceptions.RequestException as e:
        return f"Erreur: {e}"


# ════════════════════════════════════════════════════════════════════════════
#                           APPLICATION
# ════════════════════════════════════════════════════════════════════════════

class App(tkinter.Tk):
    """Fenêtre principale de l'application de gestion de sûreté."""

    def __init__(self):
        super().__init__()
        self.title("Maquette système Sûreté")
        self.geometry("900x580")
        self.minsize(700, 480)
        self.configure(bg=BG)
        self.cards_data = []
        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        """Configure les styles ttk pour le Treeview et la scrollbar."""
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("T.Treeview",
            background=SURFACE, foreground=TEXT,
            fieldbackground=SURFACE, rowheight=26,
            borderwidth=0, font=FONT)
        s.configure("T.Treeview.Heading",
            background=BG, foreground=TEXT_DIM,
            borderwidth=0, font=FONT_BOLD, relief="flat")
        s.map("T.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")])

        s.configure("T.Vertical.TScrollbar",
            background=BORDER, troughcolor=BG,
            bordercolor=BORDER, arrowcolor=TEXT_DIM,
            relief="flat", width=8)

    def _create_widgets(self):
        """Construit l'interface : sidebar + zone de contenu."""
        body = tkinter.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self._create_sidebar(body)
        tkinter.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        self.content = tkinter.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.show_dashboard()

    def _create_sidebar(self, parent):
        """Crée la barre latérale avec les boutons de navigation et le bouton Quitter."""
        sidebar = tkinter.Frame(parent, bg=SURFACE, width=160)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tkinter.Label(sidebar, text="Navigation",
                      bg=SURFACE, fg=TEXT_DIM,
                      font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(16, 4))

        self.nav_btns = {}
        for label, key, cmd in [
            ("Accueil",      "dashboard", self.show_dashboard),
            ("Cartes",       "cards",     self.show_cards_tab),
            ("Utilisateurs", "users",     self.show_users_tab),
        ]:
            btn = tkinter.Button(sidebar, text=label, command=cmd,
                                 bg=SURFACE, fg=TEXT, font=FONT,
                                 relief="flat", anchor="w", bd=0,
                                 padx=16, pady=8,
                                 activebackground=BG,
                                 activeforeground=ACCENT,
                                 cursor="hand2")
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        tkinter.Button(sidebar, text="Quitter", command=self.quit,
                       bg=SURFACE, fg=DANGER, font=FONT,
                       relief="flat", bd=0, padx=16, pady=8, anchor="w",
                       activebackground=BG, activeforeground=DANGER,
                       cursor="hand2").pack(fill="x", side="bottom")

    def _set_active_nav(self, key):
        """Met en évidence le bouton de navigation de la page courante."""
        for k, btn in self.nav_btns.items():
            btn.configure(fg=ACCENT if k == key else TEXT)

    def _clear_content(self):
        """Supprime tous les widgets de la zone de contenu."""
        for w in self.content.winfo_children():
            w.destroy()

    def _page_title(self, text):
        """Affiche un titre de section suivi d'un séparateur horizontal."""
        tkinter.Label(self.content, text=text,
                      bg=BG, fg=TEXT, font=FONT_HEAD).pack(
            anchor="w", padx=24, pady=(20, 4))
        tkinter.Frame(self.content, bg=BORDER, height=1).pack(
            fill="x", padx=24, pady=(0, 12))

    # ────────────────────────────────────────────────────────────────────────
    #                           DASHBOARD
    # ────────────────────────────────────────────────────────────────────────

    def show_dashboard(self):
        """Affiche la page d'accueil avec les informations de connexion au serveur."""
        self._set_active_nav("dashboard")
        self._clear_content()
        self._page_title("Tableau de bord")

        tkinter.Label(self.content, text=f"Serveur : {IP}:5000",
                      bg=BG, fg=TEXT_DIM, font=FONT).pack(anchor="w", padx=24)

    # ────────────────────────────────────────────────────────────────────────
    #                       GESTION DES CARTES
    # ────────────────────────────────────────────────────────────────────────

    def show_cards_tab(self):
        """Affiche l'onglet de gestion des cartes avec le tableau et la barre d'outils."""
        self._set_active_nav("cards")
        self._clear_content()
        self._page_title("Cartes")

        # Barre d'outils
        toolbar = tkinter.Frame(self.content, bg=BG)
        toolbar.pack(fill="x", padx=24, pady=(0, 8))

        tkinter.Button(toolbar, text="Ajouter", command=self.add_card,
                       bg=ACCENT, fg="white", relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground="#1d4ed8", activeforeground="white",
                       cursor="hand2").pack(side="left", padx=(0, 6))

        self.btn_modifier = tkinter.Button(toolbar, text="Modifier",
                                         command=self.modify_card,
                                         state="disabled", relief="flat", bd=0,
                                         bg=BG, fg=TEXT, padx=10, pady=5,
                                         font=FONT, cursor="hand2",
                                         activebackground=BORDER)
        self.btn_modifier.pack(side="left", padx=(0, 6))

        self.btn_supprimer = tkinter.Button(toolbar, text="Supprimer",
                                         command=self.delete_card,
                                         state="disabled", relief="flat", bd=0,
                                         bg=BG, fg=DANGER, padx=10, pady=5,
                                         font=FONT, cursor="hand2",
                                         activebackground=BORDER)
        self.btn_supprimer.pack(side="left")

        tkinter.Button(toolbar, text="Actualiser", command=self.load_cards,
                       bg=BG, fg=TEXT, relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground=BORDER, cursor="hand2").pack(side="right")

        # Tableau
        frame = tkinter.Frame(self.content, bg=BORDER, bd=1)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        scroll = ttk.Scrollbar(frame, style="T.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y")

        self.cards_tree = ttk.Treeview(frame,
            columns=("id", "texte", "id_util", "date_ajout"),
            show="headings", style="T.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.cards_tree.yview)

        for col, label, width in [
            ("id",      "ID Badge",       140),
            ("texte",   "Texte",          200),
            ("id_util", "ID Utilisateur", 180),
            ("date_ajout", "Date de création", 140),
        ]:
            self.cards_tree.heading(col, text=label)
            self.cards_tree.column(col, width=width, anchor="center")

        self.cards_tree.pack(fill="both", expand=True)
        self.cards_tree.bind("<<TreeviewSelect>>", self._on_card_select)

        self.load_cards()

    def _on_card_select(self, event=None):
        """Active les boutons Modifier et Supprimer lorsqu'une carte est sélectionnée."""
        state = "normal" if self.cards_tree.selection() else "disabled"
        self.btn_modifier.configure(state=state)
        self.btn_supprimer.configure(state=state)

    def charger_carte(self):
        """Récupère la liste des cartes depuis le serveur et remplit le tableau."""
        response = send_request(ip=IP, port=5000, endpoint="/afficher_cartes")
        try:
            parsed = json.loads(response)
            self.cards_data = parsed.get("cartes", parsed) if isinstance(parsed, dict) else parsed
            self.cards_tree.delete(*self.cards_tree.get_children())
            for card in self.cards_data:
                self.cards_tree.insert("", "end", values=(
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
            res = send_request(ip=IP, port=5000,
                               endpoint="/ajouter_une_carte", valeur=data)
            messagebox.showinfo("Résultat", res, parent=win)
            self.load_cards()
            win.destroy()

        self._modal("Ajouter une carte",
                    [("id", "ID Badge"), ("texte", "Texte"),
                     ("id_util", "ID Utilisateur")], submit)

    def modifier_carte(self):
        """Ouvre le formulaire de modification de la carte sélectionnée dans le tableau."""
        sel = self.cards_tree.selection()
        if not sel:
            return
        vals = self.cards_tree.item(sel[0], "values")
        prefill = {"id": vals[0], "texte": vals[1], "id_util": vals[2]}

        def submit(data, win):
            res = send_request(ip=IP, port=5000,
                               endpoint=f"/modifier_une_carte/{data['id']}",
                               valeur=data)
            messagebox.showinfo("Résultat", res, parent=win)
            self.load_cards()
            win.destroy()

        self._modal("Modifier une carte",
                    [("id", "ID Badge"), ("texte", "Texte"),
                     ("id_util", "ID Utilisateur")], submit, prefill=prefill)

    def supprimer_carte(self):
        """Supprime la carte sélectionnée après confirmation de l'utilisateur."""
        sel = self.cards_tree.selection()
        if not sel:
            return
        card_id = self.cards_tree.item(sel[0], "values")[0]
        if not messagebox.askyesno("Confirmer", f"Supprimer la carte {card_id} ?"):
            return
        res = send_request(ip=IP, port=5000,
                           endpoint=f"/supprimer_une_carte/{card_id}")
        messagebox.showinfo("Résultat", res)
        self.load_cards()

    # ────────────────────────────────────────────────────────────────────────
    #                       MODAL GÉNÉRIQUE
    # ────────────────────────────────────────────────────────────────────────

    def _modal(self, title, fields, on_submit, prefill=None):
        """
        Crée une fenêtre modale générique avec un formulaire dynamique.

        Paramètres :
        - title      : titre affiché en haut de la fenêtre
        - fields     : liste de tuples (clé, libellé) définissant les champs
        - on_submit  : fonction(data, win) appelée à la validation
        - prefill    : dictionnaire optionnel pour pré-remplir les champs
        """
        win = tkinter.Toplevel(self)
        win.title(title)
        win.configure(bg=BG)
        win.resizable(True, True)
        win.grab_set()

        tkinter.Label(win, text=title, bg=BG, fg=TEXT,
                      font=FONT_BOLD).pack(anchor="w", padx=20, pady=(16, 4))
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20)

        body = tkinter.Frame(win, bg=BG, padx=20, pady=9)
        body.pack(fill="both")

        entries = {}
        for key, label in fields:
            tkinter.Label(body, text=label, bg=BG, fg=TEXT_DIM,
                          font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
            entry = tkinter.Entry(body, bg=SURFACE, fg=TEXT,
                                  insertbackground=ACCENT,
                                  relief="solid", bd=1, font=FONT,
                                  highlightthickness=0)
            entry.pack(fill="x", ipady=5)
            if prefill and key in prefill:
                entry.insert(0, prefill[key])
            entries[key] = entry

        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20)
        footer = tkinter.Frame(win, bg=BG, padx=20, pady=12)
        footer.pack(fill="x")

        tkinter.Button(footer, text="Annuler", command=win.destroy,
                       bg=BG, fg=TEXT, relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground=BORDER, cursor="hand2").pack(
            side="right", padx=(6, 0))

        def submit():
            on_submit({k: e.get() for k, e in entries.items()}, win)

        tkinter.Button(footer, text="Valider", command=submit,
                       bg=ACCENT, fg="white", relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground="#1d4ed8", cursor="hand2").pack(side="right")

        win.geometry(f"380x{120 + len(fields) * 62}")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    # ────────────────────────────────────────────────────────────────────────
    #                          UTILISATEURS
    # ────────────────────────────────────────────────────────────────────────

    def show_users_tab(self):
        """Affiche l'onglet de gestion des utilisateurs (fonctionnalités à venir)."""
        self._set_active_nav("users")
        self._clear_content()
        self._page_title("Utilisateurs")

        tkinter.Label(self.content, text="Fonctionnalités à venir.",
                      bg=BG, fg=TEXT_DIM, font=FONT).pack(anchor="w", padx=24)


if __name__ == "__main__":
    app = App()
    app.mainloop()