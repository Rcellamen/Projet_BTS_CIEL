import tkinter
from tkinter import messagebox, ttk
import json

from Outils.cartes import *
from Outils.utilisateurs import *



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
            ("Gestion des cartes",       "cartes",    self.affichage_onglet_carte),
            ("Gestion des utilisateurs", "utilisateurs", self.affichage_onglet_util),
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


    def _on_select(self, event=None):
        """Active les boutons Modifier et Supprimer lorsqu'une carte est sélectionnée."""
        state = "normal" if self.arbre_carte.selection() else "disabled"
        self.btn_modifier.configure(state=state)
        self.btn_supprimer.configure(state=state)


    def affichage_onglet_carte(self):
        """Affiche l'onglet de gestion des cartes avec le tableau et la barre d'outils."""
        self._set_active_nav("cards")
        self._clear_content()
        self._page_title("Gestion des cartes")

        # Barre d'outils
        toolbar = tkinter.Frame(self.content, bg=BG)
        toolbar.pack(fill="x", padx=24, pady=(0, 8))
        tkinter.Button(toolbar, text="Ajouter", command=ajouter_carte,
                       bg=ACCENT, fg="white", relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground="#1d4ed8", activeforeground="white",
                       cursor="hand2").pack(side="left", padx=(0, 6))
        
        self.btn_modifier = tkinter.Button(toolbar, text="Modifier",
                        command=modifier_carte,
                        state="disabled", relief="flat", bd=0,
                        bg=BG, fg=TEXT, padx=10, pady=5,
                        font=FONT, cursor="hand2",
                        activebackground=BORDER)
        self.btn_modifier.pack(side="left", padx=(0, 6))
        self.btn_supprimer = tkinter.Button(toolbar, text="Supprimer",
                                         command=supprimer_carte,
                                         state="disabled", relief="flat", bd=0,
                                         bg=BG, fg=DANGER, padx=10, pady=5,
                                         font=FONT, cursor="hand2",
                                         activebackground=BORDER)
        self.btn_supprimer.pack(side="left")
        self.btn_charger = tkinter.Button(toolbar, text="Actualiser", command=charger_carte,
                       bg=BG, fg=TEXT, relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground=BORDER, cursor="hand2").pack(side="right")

        # Tableau
        frame = tkinter.Frame(self.content, bg=BORDER, bd=1)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        scroll = ttk.Scrollbar(frame, style="T.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y")
        self.arbre_carte = ttk.Treeview(frame,
            columns=("id", "texte", "id_util", "date_ajout"),
            show="headings", style="T.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.arbre_carte.yview)

        for col, label, width in [
            ("id",      "ID Badge",       140),
            ("texte",   "Texte",          200),
            ("id_util", "ID Utilisateur", 180),
            ("date_ajout", "Date de création", 140),
        ]:
            self.arbre_carte.heading(col, text=label)
            self.arbre_carte.column(col, width=width, anchor="center")

        self.arbre_carte.pack(fill="both", expand=True)
        self.arbre_carte.bind("<<TreeviewSelect>>", self._on_select)

        charger_carte




    def affichage_onglet_util(self):
        """Affiche l'onglet des utilisateurs."""
        self._set_active_nav("utilisateurs")
        self._clear_content()
        self._page_title("Utilisateurs")

        # Barre d'outils
        toolbar = tkinter.Frame(self.content, bg=BG)
        toolbar.pack(fill="x", padx=24, pady=(0, 8))

        self.btn_ajouter = tkinter.Button(toolbar, text="Ajouter", command=ajouter_util,
                       bg=ACCENT, fg="white", relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground="#1d4ed8", activeforeground="white",
                       cursor="hand2").pack(side="left", padx=(0, 6))

        self.btn_modifier = tkinter.Button(toolbar, text="Modifier",
                                         command=modifier_util,
                                         state="disabled", relief="flat", bd=0,
                                         bg=BG, fg=TEXT, padx=10, pady=5,
                                         font=FONT, cursor="hand2",
                                         activebackground=BORDER)
        self.btn_modifier.pack(side="left", padx=(0, 6))

        self.btn_supprimer = tkinter.Button(toolbar, text="Supprimer",
                                         command=supprimer_util,
                                         state="disabled", relief="flat", bd=0,
                                         bg=BG, fg=DANGER, padx=10, pady=5,
                                         font=FONT, cursor="hand2",
                                         activebackground=BORDER)
        self.btn_supprimer.pack(side="left")

        tkinter.Button(toolbar, text="Actualiser", command=charger_util,
                       bg=BG, fg=TEXT, relief="flat", bd=0,
                       padx=10, pady=5, font=FONT,
                       activebackground=BORDER, cursor="hand2").pack(side="right")

        # Tableau
        frame = tkinter.Frame(self.content, bg=BORDER, bd=1)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        scroll = ttk.Scrollbar(frame, style="T.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y")

        self.arbre_util = ttk.Treeview(frame,
            columns=("id", "nom", "prenom", "badges", "droits"),
            show="headings", style="T.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.arbre_util.yview)

        for col, label, width in [
            ("id",      "ID Utilisateur",       140),
            ("nom",   "Nom",          200),
            ("prenom", "Prénom", 180),
            ("badges", "ID Badge", 140),
            ("droits", "Droits", 100)
        ]:
            self.arbre_util.heading(col, text=label)
            self.arbre_util.column(col, width=width, anchor="center")

        self.arbre_util.pack(fill="both", expand=True)
        self.arbre_util.bind("<<TreeviewSelect>>", self._on_select)

        charger_util
    
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
 

if __name__ == "__main__":
    app = App()
    app.mainloop()