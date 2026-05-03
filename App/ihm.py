import tkinter
from tkinter import messagebox, ttk
import customtkinter as ctk

from Outils.cartes import *
from Outils.utilisateurs import *

# ── Thème global customTkinter ──────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ════════════════════════════════════════════════════════════════════════════
#                           APPLICATION
# ════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    """Fenêtre principale de l'application de gestion de sûreté."""

    def __init__(self):
        super().__init__()
        self.title("Maquette système sûreté")
        self.geometry("1020x640")
        self.minsize(760, 500)
        self.configure(fg_color=BG)
        self.donnee_cartes = []
        self.donnee_util   = []
        self._setup_treeview_style()
        self._create_widgets()

    # ── Style TTK pour Treeview ─────────────────────────────────────────────
    def _setup_treeview_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Light.Treeview",
            background=SURFACE,
            foreground=TEXT,
            fieldbackground=SURFACE,
            rowheight=32,
            borderwidth=0,
            font=FONT_UI)
        s.configure("Light.Treeview.Heading",
            background=BG,
            foreground=TEXT_DIM,
            borderwidth=0,
            font=FONT_BOLD,
            relief="flat",
            padding=(8, 6))
        s.map("Light.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")])

        s.configure("Light.Vertical.TScrollbar",
            background=BORDER,
            troughcolor=BG,
            bordercolor=BORDER,
            arrowcolor=TEXT_DIM,
            relief="flat",
            width=6)

    # ── Construction de la fenêtre ──────────────────────────────────────────
    def _create_widgets(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self._create_sidebar(body)

        sep = tkinter.Frame(body, bg=BORDER, width=1)
        sep.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self._show_dashboard()

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _create_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=SIDEBAR,
                               width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # En-tête marque
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(22, 18))

        ctk.CTkLabel(brand, text="🔐",
                     font=("Segoe UI", 20),
                     text_color=ACCENT).pack(side="left")
        title_col = ctk.CTkFrame(brand, fg_color="transparent")
        title_col.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(title_col, text="Sûreté",
                     font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Gestion des accès",
                     font=FONT_TINY,
                     text_color=TEXT_DIM).pack(anchor="w")

        # Séparateur
        tkinter.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(sidebar, text="NAVIGATION",
                     font=FONT_TINY,
                     text_color=TEXT_LIGHT).pack(anchor="w", padx=18, pady=(0, 6))

        self.nav_btns = {}
        for label, key, cmd in [
            ("Accueil",             "dashboard",    self._show_dashboard),
            ("Gestion des cartes",  "cartes",       self._affichage_onglet_carte),
            ("Utilisateurs",        "utilisateurs", self._affichage_onglet_util),
        ]:
            btn = ctk.CTkButton(
                sidebar, text=label,
                command=cmd,
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_DIM,
                hover_color=ACCENT_SOFT,
                font=FONT_UI,
                height=38,
                corner_radius=8,
                cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_btns[key] = btn

        # Quitter en bas
        tkinter.Frame(sidebar, bg=BORDER, height=1).pack(
            fill="x", padx=16, pady=(10, 8), side="bottom")
        ctk.CTkButton(
            sidebar, text="Quitter",
            command=self.quit,
            anchor="w",
            fg_color="transparent",
            text_color=DANGER,
            hover_color=DANGER_SOFT,
            font=FONT_UI,
            height=38,
            corner_radius=8,
            cursor="hand2").pack(fill="x", padx=10, pady=(0, 10), side="bottom")

    def _set_active_nav(self, key):
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color=ACCENT_SOFT, text_color=ACCENT,
                               font=FONT_BOLD)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_DIM,
                               font=FONT_UI)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _page_title(self, text, subtitle=""):
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(anchor="w", padx=32, pady=(28, 0))
        ctk.CTkLabel(header, text=text,
                     font=FONT_HEAD,
                     text_color=TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle,
                         font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(anchor="w", pady=(2, 0))
        tkinter.Frame(self.content, bg=BORDER, height=1).pack(
            fill="x", padx=32, pady=(14, 0))

    # ── Helpers boutons ─────────────────────────────────────────────────────
    def _toolbar(self):
        tb = ctk.CTkFrame(self.content, fg_color="transparent")
        tb.pack(fill="x", padx=32, pady=(14, 10))
        return tb

    def _btn_primary(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command,
                             fg_color=ACCENT, hover_color="#1d4ed8",
                             text_color="white", font=FONT_UI,
                             height=34, corner_radius=7, cursor="hand2")

    def _btn_secondary(self, parent, text, command, state="normal"):
        return ctk.CTkButton(parent, text=text, command=command,
                             state=state,
                             fg_color=SURFACE, hover_color=ACCENT_SOFT,
                             text_color=TEXT, font=FONT_UI,
                             border_width=1, border_color=BORDER,
                             height=34, corner_radius=7, cursor="hand2")

    def _btn_danger(self, parent, text, command, state="normal"):
        return ctk.CTkButton(parent, text=text, command=command,
                             state=state,
                             fg_color=SURFACE, hover_color=DANGER_SOFT,
                             text_color=DANGER, font=FONT_UI,
                             border_width=1, border_color=BORDER,
                             height=34, corner_radius=7, cursor="hand2")

    # ── Activation boutons sur sélection ────────────────────────────────────
    def _on_select(self, event=None):
        widget = event.widget
        state  = "normal" if widget.selection() else "disabled"

        if hasattr(self, "arbre_carte") and widget == self.arbre_carte:
            self.btn_modifier.configure(state=state)
            self.btn_supprimer.configure(state=state)

        elif hasattr(self, "arbre_util") and widget == self.arbre_util:
            self.btn_modifier.configure(state=state)
            self.btn_supprimer.configure(state=state)
            self.btn_ajouter_carte_util.configure(state=state)

    # ── Tests matériel ──────────────────────────────────────────────────────
    def _testPIR(self):
        try:
            response = envoi_requete(ip=IP, port=5000, endpoint="/test_PIR")
            messagebox.showinfo("Test PIR", response)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de contacter le Raspberry : {e}")

    def _testLB(self):
        try:
            reponse = envoi_requete(ip=IP, port=5000, endpoint="/test_LB")
            messagebox.showinfo("Test LB", reponse)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le badge : {e}")

    # ════════════════════════════════════════════════════════════════════════
    #                           DASHBOARD
    # ════════════════════════════════════════════════════════════════════════

    def _show_dashboard(self):
        self._set_active_nav("dashboard")
        self._clear_content()
        self._page_title("Tableau de bord",
                         subtitle=f"Connecté à {IP}:5000")

        outer = ctk.CTkFrame(self.content, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=32, pady=20)

        # Bannière statut
        status_card = ctk.CTkFrame(outer, fg_color=ACCENT_SOFT,
                                   corner_radius=10)
        status_card.pack(fill="x", pady=(0, 20))
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(padx=20, pady=14)
        ctk.CTkLabel(status_inner, text="●",
                     font=("Segoe UI", 10),
                     text_color="#16a34a").pack(side="left")
        ctk.CTkLabel(status_inner,
                     text=f"  Système opérationnel  —  Raspberry Pi {IP}:5000",
                     font=FONT_UI,
                     text_color=ACCENT).pack(side="left")

        # Titre section
        ctk.CTkLabel(outer, text="Tests matériel",
                     font=FONT_BOLD,
                     text_color=TEXT_DIM).pack(anchor="w", pady=(0, 10))

        # Grille 2 colonnes
        grid = ctk.CTkFrame(outer, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="col")

        for col_idx, (titre, desc, cmd) in enumerate([
            ("Capteur PIR",
             "Tester la détection de mouvement infrarouge passif.",
             self._testPIR),
            ("Lecteur de badge",
             "Vérifier la lecture d'une carte RFID / NFC.",
             self._testLB),
        ]):
            card = ctk.CTkFrame(grid, fg_color=SURFACE,
                                corner_radius=10,
                                border_width=1, border_color=BORDER)
            card.grid(row=0, column=col_idx,
                      padx=(0, 10) if col_idx == 0 else (10, 0),
                      sticky="nsew")
            ctk.CTkLabel(card, text=titre,
                         font=FONT_BOLD,
                         text_color=TEXT).pack(anchor="w", padx=20, pady=(18, 4))
            ctk.CTkLabel(card, text=desc,
                         font=FONT_SMALL,
                         text_color=TEXT_DIM,
                         wraplength=280,
                         justify="left").pack(anchor="w", padx=20)
            ctk.CTkButton(card, text="Lancer le test", command=cmd,
                          fg_color=ACCENT, hover_color="#1d4ed8",
                          text_color="white", font=FONT_UI,
                          height=32, corner_radius=7,
                          cursor="hand2").pack(anchor="e", padx=20, pady=16)

    # ════════════════════════════════════════════════════════════════════════
    #                           ONGLET CARTE
    # ════════════════════════════════════════════════════════════════════════

    def _affichage_onglet_carte(self):
        self._set_active_nav("cartes")
        self._clear_content()
        self._page_title("Gestion des cartes",
                         subtitle="Badges RFID enregistrés dans le système")

        tb = self._toolbar()
        self._btn_primary(tb, "+ Ajouter",
                          lambda: self._ouvrir_scan_puis_modal("carte")
                          ).pack(side="left", padx=(0, 6))
        self.btn_modifier = self._btn_secondary(tb, "Modifier",
                            lambda: modifier_carte(self), state="disabled")
        self.btn_modifier.pack(side="left", padx=(0, 6))
        self.btn_supprimer = self._btn_danger(tb, "Supprimer",
                             lambda: supprimer_carte(self), state="disabled")
        self.btn_supprimer.pack(side="left")
        self._btn_secondary(tb, "↻ Actualiser",
                            lambda: charger_carte(self)
                            ).pack(side="right")

        wrap = ctk.CTkFrame(self.content, fg_color=SURFACE,
                            corner_radius=10,
                            border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        scroll = ttk.Scrollbar(wrap, style="Light.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y", pady=2)

        self.arbre_carte = ttk.Treeview(
            wrap,
            columns=("id", "texte", "id_util", "date_ajout"),
            show="headings",
            style="Light.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.arbre_carte.yview)

        for col, label, width in [
            ("id",         "ID Badge",          160),
            ("texte",      "Texte",              200),
            ("id_util",    "ID Utilisateur",     180),
            ("date_ajout", "Date de création",   160),
        ]:
            self.arbre_carte.heading(col, text=label)
            self.arbre_carte.column(col, width=width, anchor="w")

        self.arbre_carte.pack(fill="both", expand=True, padx=2, pady=2)
        self.arbre_carte.bind("<<TreeviewSelect>>", self._on_select)
        charger_carte(self)

    # ════════════════════════════════════════════════════════════════════════
    #                           ONGLET UTILISATEURS
    # ════════════════════════════════════════════════════════════════════════

    def _affichage_onglet_util(self):
        self._set_active_nav("utilisateurs")
        self._clear_content()
        self._page_title("Gestion des utilisateurs",
                         subtitle="Personnes autorisées à accéder au système")

        tb = self._toolbar()
        self._btn_primary(tb, "+ Ajouter",
                          lambda: ajouter_util(self)
                          ).pack(side="left", padx=(0, 6))
        self.btn_modifier = self._btn_secondary(tb, "Modifier",
                            lambda: modifier_util(self), state="disabled")
        self.btn_modifier.pack(side="left", padx=(0, 6))
        self.btn_supprimer = self._btn_danger(tb, "Supprimer",
                             lambda: supprimer_util(self), state="disabled")
        self.btn_supprimer.pack(side="left", padx=(0, 6))
        self.btn_ajouter_carte_util = self._btn_secondary(
            tb, "Ajouter une carte",
            lambda: self._ouvrir_scan_puis_modal("util"),
            state="disabled")
        self.btn_ajouter_carte_util.pack(side="left")
        self._btn_secondary(tb, "↻ Actualiser",
                            lambda: charger_util(self)
                            ).pack(side="right")

        wrap = ctk.CTkFrame(self.content, fg_color=SURFACE,
                            corner_radius=10,
                            border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        scroll = ttk.Scrollbar(wrap, style="Light.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y", pady=2)

        self.arbre_util = ttk.Treeview(
            wrap,
            columns=("id", "nom", "prenom", "badges", "droits"),
            show="headings",
            style="Light.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.arbre_util.yview)

        for col, label, width in [
            ("id",     "ID Utilisateur", 160),
            ("nom",    "Nom",            180),
            ("prenom", "Prénom",         180),
            ("badges", "ID Badge",       160),
            ("droits", "Droits",         100),
        ]:
            self.arbre_util.heading(col, text=label)
            self.arbre_util.column(col, width=width, anchor="w")

        self.arbre_util.pack(fill="both", expand=True, padx=2, pady=2)
        self.arbre_util.bind("<<TreeviewSelect>>", self._on_select)
        charger_util(self)

    # ════════════════════════════════════════════════════════════════════════
    #                           FENÊTRE MODALE GÉNÉRIQUE
    # ════════════════════════════════════════════════════════════════════════

    def _modal(self, title, fields, on_submit, prefill=None):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.grab_set()

        # En-tête
        header = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=title,
                     font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(18, 16))
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x")

        # Formulaire
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", padx=24, pady=(12, 0))

        entries = {}
        is_util  = title in ("Ajouter un utilisateur",  "Modifier un utilisateur")
        is_carte = title in ("Ajouter une carte",        "Modifier une carte")

        def _make_entry(key, label_text, readonly=False):
            ctk.CTkLabel(body, text=label_text,
                         font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(anchor="w", pady=(10, 2))
            e = ctk.CTkEntry(body,
                             font=FONT_UI,
                             fg_color=SURFACE,
                             text_color=TEXT,
                             border_color=BORDER,
                             border_width=1,
                             placeholder_text_color=TEXT_LIGHT,
                             height=36)
            e.pack(fill="x")
            if prefill and key in prefill:
                e.insert(0, prefill[key])
            if readonly:
                e.configure(state="disabled",
                            fg_color="#f3f4f6",
                            text_color=TEXT_DIM)
            entries[key] = e

        if is_util:
            for field in fields:
                key, label_text, *opts = field
                widget_type = opts[0] if opts else "entry"
                choices     = opts[1] if len(opts) > 1 else []
                if widget_type == "combo":
                    ctk.CTkLabel(body, text=label_text,
                                 font=FONT_SMALL,
                                 text_color=TEXT_DIM).pack(anchor="w", pady=(10, 2))
                    cb = ctk.CTkComboBox(body, values=choices,
                                         font=FONT_UI,
                                         fg_color=SURFACE,
                                         text_color=TEXT,
                                         button_color=BORDER,
                                         button_hover_color=ACCENT_SOFT,
                                         border_color=BORDER,
                                         dropdown_fg_color=SURFACE,
                                         dropdown_text_color=TEXT,
                                         dropdown_hover_color=ACCENT_SOFT,
                                         state="readonly",
                                         height=36)
                    cb.set(choices[0] if choices else "")
                    cb.pack(fill="x")
                    entries[key] = cb
                else:
                    _make_entry(key, label_text, readonly=(key == "id_util"))

        elif is_carte:
            for field in fields:
                key, label_text, *_ = field
                _make_entry(key, label_text, readonly=(key == "id_badge"))

        # Pied de page
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", pady=(16, 0))
        footer = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
        footer.pack(fill="x")

        def submit():
            data = {}
            for k, e in entries.items():
                if isinstance(e, ctk.CTkComboBox):
                    data[k] = e.get()
                else:
                    prev = e.cget("state")
                    e.configure(state="normal")
                    data[k] = e.get()
                    e.configure(state=prev)
            on_submit(data, win)

        ctk.CTkButton(footer, text="Annuler", command=win.destroy,
                      fg_color="transparent", hover_color=ACCENT_SOFT,
                      text_color=TEXT_DIM, font=FONT_UI,
                      border_width=1, border_color=BORDER,
                      height=34, corner_radius=7,
                      cursor="hand2").pack(side="right", padx=(6, 20), pady=14)

        ctk.CTkButton(footer, text="Valider", command=submit,
                      fg_color=ACCENT, hover_color="#1d4ed8",
                      text_color="white", font=FONT_BOLD,
                      height=34, corner_radius=7,
                      cursor="hand2").pack(side="right", pady=14)

        win.geometry(f"400x{180 + len(fields) * 72}")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    # ════════════════════════════════════════════════════════════════════════
    #                   FONCTION OUVRIR FENETRE SCAN PUIS MODAL
    # ════════════════════════════════════════════════════════════════════════

    def _ouvrir_scan_puis_modal(self, nature):
        if nature == "carte":
            fields_carte = [
                ("id_badge", "ID Badge"),
                ("texte",    "Texte / libellé"),
                ("id_util",  "ID Utilisateur"),
            ]

            def submit(data, win):
                reponse = envoi_requete(ip=IP, port=5000,
                                        endpoint="/ajouter_une_carte",
                                        valeur=data)
                messagebox.showinfo("Résultat", reponse, parent=win)
                charger_carte(self)
                win.destroy()

            def apres_scan(id_badge):
                self._modal(title="Ajouter une carte",
                            fields=fields_carte,
                            on_submit=submit,
                            prefill={"id_badge": id_badge})

            fenetre_scan_carte(self, on_card_scanned=apres_scan)

        elif nature == "util":
            sel = self.arbre_util.selection()
            if not sel:
                messagebox.showwarning("Attention",
                                       "Sélectionnez d'abord un utilisateur.")
                return
            id_util = self.arbre_util.item(sel[0], "values")[0]

            def apres_scan(id_badge):
                reponse = envoi_requete(
                    ip=IP, port=5000,
                    endpoint=f"/ajouter_une_carte_a_util/{id_util}",
                    valeur={"id_badge": id_badge})
                messagebox.showinfo("Résultat", reponse)
                charger_util(self)

            fenetre_scan_util(self, on_card_scanned=apres_scan)


if __name__ == "__main__":
    app = App()
    app.mainloop()