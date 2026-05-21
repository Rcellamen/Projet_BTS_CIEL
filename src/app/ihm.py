"""
IHM principale du système de sûreté (CustomTkinter).

Tableau de bord, gestion des cartes RFID et des utilisateurs.
Communication avec l'API Flask (Raspberry Pi) exclusivement via HTTP.
"""

import json
import threading
import tkinter
from tkinter import messagebox, ttk

import requests
import customtkinter as ctk

from src.App.Outils.cartes import *
from src.App.Outils.utilisateurs import *
from src.App.Outils.parametres import hors_horaires, ALARME_ON, ALARME_OFF, SUCCESS, WARNING, FONT_BIG

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
        self.geometry("1100x720")
        self.minsize(820, 560)
        self.configure(fg_color=BG)
        self.donnee_cartes = []
        self.donnee_util   = []

        # État de l'alarme (clignotement du voyant sur le dashboard)
        self._alarme_active = False
        self._alarme_etat   = False  # alterne True/False pendant le clignotement

        # État des boucles de test PIR / Porte (mode polling)
        self._pir_running   = False
        self._porte_running = False
        # Contributions individuelles à l'alarme globale
        self._pir_alarme    = False
        self._porte_alarme  = False

        self._configurer_style_tableau()

        # 1. On cache la fenêtre principale au démarrage
        self.withdraw()

        # 2. On lance la fenêtre de connexion par-dessus
        self._afficher_fenetre_connexion()

    # ── Fenêtre de Connexion au Démarrage ───────────────────────────────────
    def _afficher_fenetre_connexion(self):
        """Affiche la modale de connexion permettant de saisir l'IP du Raspberry."""
        self.win_connexion = ctk.CTkToplevel(self)
        self.win_connexion.title("Connexion au Serveur")
        self.win_connexion.geometry("420x260")
        self.win_connexion.resizable(False, False)
        self.win_connexion.configure(fg_color=BG)
        self.win_connexion.grab_set()

        self.win_connexion.update_idletasks()
        x = (self.win_connexion.winfo_screenwidth() - 420) // 2
        y = (self.win_connexion.winfo_screenheight() - 260) // 2
        self.win_connexion.geometry(f"{420}x{260}+{x}+{y}")

        ctk.CTkLabel(self.win_connexion, text="Connexion au système",
                     font=FONT_HEAD, text_color=TEXT).pack(pady=(25, 5))
        ctk.CTkLabel(self.win_connexion, text="Entrez le Hostname ou l'IP du Raspberry Pi :",
                     font=FONT_SMALL, text_color=TEXT_DIM).pack(pady=(0, 20))

        self.entry_ip = ctk.CTkEntry(self.win_connexion, width=280, font=FONT_UI, height=38, justify="center")
        self.entry_ip.pack(pady=10)
        self.entry_ip.insert(0, RESEAU["IP"])

        btn_connect = ctk.CTkButton(self.win_connexion, text="Se connecter",
                                    command=self._valider_connexion,
                                    fg_color=ACCENT, hover_color="#1d4ed8", text_color="white",
                                    font=FONT_BOLD, height=38, corner_radius=7, cursor="hand2")
        btn_connect.pack(pady=15)

        self.win_connexion.protocol("WM_DELETE_WINDOW", self.destroy)

    def _valider_connexion(self):
        """Valide l'IP saisie, ferme la modale et affiche l'IHM principale."""
        RESEAU["IP"] = self.entry_ip.get().strip()
        self.win_connexion.destroy()
        self._construire_interface()
        self.deiconify()

    # ── Style TTK pour Treeview ─────────────────────────────────────────────
    def _configurer_style_tableau(self):
        """Configure le style des Treeview pour rester cohérent avec le thème."""
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Light.Treeview",
            background=SURFACE, foreground=TEXT,
            fieldbackground=SURFACE, rowheight=32,
            borderwidth=0, font=FONT_UI)
        s.configure("Light.Treeview.Heading",
            background=BG, foreground=TEXT_DIM, borderwidth=0,
            font=FONT_BOLD, relief="flat", padding=(8, 6))
        s.map("Light.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")])

        s.configure("Light.Vertical.TScrollbar",
            background=BORDER, troughcolor=BG, bordercolor=BORDER,
            arrowcolor=TEXT_DIM, relief="flat", width=6)

    # ── Construction de la fenêtre ──────────────────────────────────────────
    def _construire_interface(self):
        """Construit la disposition principale (sidebar + contenu)."""
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self._creer_barre_laterale(body)

        sep = tkinter.Frame(body, bg=BORDER, width=1)
        sep.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self._afficher_tableau_bord()

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _creer_barre_laterale(self, parent):
        """Construit la barre latérale de navigation."""
        sidebar = ctk.CTkFrame(parent, fg_color=SIDEBAR, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(22, 18))

        ctk.CTkLabel(brand, text="🔐", font=("Segoe UI", 20),
                     text_color=ACCENT).pack(side="left")
        title_col = ctk.CTkFrame(brand, fg_color="transparent")
        title_col.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(title_col, text="Système Sûreté", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Gestion des accès et de l'intrusion", font=FONT_TINY,
                     text_color=TEXT_DIM).pack(anchor="w")

        tkinter.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(sidebar, text="NAVIGATION", font=FONT_TINY,
                     text_color=TEXT_LIGHT).pack(anchor="w", padx=18, pady=(0, 6))

        self.nav_btns = {}
        for label, key, cmd in [
            ("Accueil",             "dashboard",    self._afficher_tableau_bord),
            ("Gestion des cartes",  "cartes",       self._affichage_onglet_carte),
            ("Gestion des utilisateurs",        "utilisateurs", self._affichage_onglet_util),
        ]:
            btn = ctk.CTkButton(sidebar, text=label, command=cmd, anchor="w",
                fg_color="transparent", text_color=TEXT_DIM,
                hover_color=ACCENT_SOFT, font=FONT_UI,
                height=38, corner_radius=8, cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_btns[key] = btn

        tkinter.Frame(sidebar, bg=BORDER, height=1).pack(
            fill="x", padx=16, pady=(10, 8), side="bottom")
        ctk.CTkButton(sidebar, text="Quitter", command=self.quit, anchor="w",
            fg_color="transparent", text_color=DANGER,
            hover_color=DANGER_SOFT, font=FONT_UI,
            height=38, corner_radius=8, cursor="hand2"
        ).pack(fill="x", padx=10, pady=(0, 10), side="bottom")

    def _definir_nav_active(self, key):
        """Met en évidence l'élément actif dans la sidebar."""
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color=ACCENT_SOFT, text_color=ACCENT, font=FONT_BOLD)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_DIM, font=FONT_UI)

    def _effacer_contenu(self):
        """
        Vide le panneau de contenu principal, arrête toute alarme en cours
        et coupe les boucles de test PIR / Porte éventuellement actives.
        """
        # Coupe les boucles avant de détruire les widgets
        self._pir_running   = False
        self._porte_running = False
        self._pir_alarme    = False
        self._porte_alarme  = False
        self._arreter_alarme()
        for w in self.content.winfo_children():
            w.destroy()

    def _titre_page(self, texte, sous_titre=""):
        """Insère le titre + sous-titre + séparateur en haut du panneau."""
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(anchor="w", padx=32, pady=(28, 0))
        ctk.CTkLabel(header, text=texte, font=FONT_HEAD,
                     text_color=TEXT).pack(anchor="w")
        if sous_titre:
            ctk.CTkLabel(header, text=sous_titre, font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(anchor="w", pady=(2, 0))
        tkinter.Frame(self.content, bg=BORDER, height=1).pack(
            fill="x", padx=32, pady=(14, 0))

    # ── Helpers boutons ─────────────────────────────────────────────────────
    def _barre_outils(self):
        """Retourne un conteneur de barre d'outils standardisé."""
        tb = ctk.CTkFrame(self.content, fg_color="transparent")
        tb.pack(fill="x", padx=32, pady=(14, 10))
        return tb

    def _btn_principal(self, parent, text, command):
        """Bouton style primaire (bleu)."""
        return ctk.CTkButton(parent, text=text, command=command,
            fg_color=ACCENT, hover_color="#1d4ed8",
            text_color="white", font=FONT_UI,
            height=34, corner_radius=7, cursor="hand2")

    def _btn_secondaire(self, parent, text, command, state="normal"):
        """Bouton style secondaire (blanc bordé)."""
        return ctk.CTkButton(parent, text=text, command=command, state=state,
            fg_color=SURFACE, hover_color=ACCENT_SOFT,
            text_color=TEXT, font=FONT_UI,
            border_width=1, border_color=BORDER,
            height=34, corner_radius=7, cursor="hand2")

    def _btn_danger(self, parent, text, command, state="normal"):
        """Bouton style danger (texte rouge)."""
        return ctk.CTkButton(parent, text=text, command=command, state=state,
            fg_color=SURFACE, hover_color=DANGER_SOFT,
            text_color=DANGER, font=FONT_UI,
            border_width=1, border_color=BORDER,
            height=34, corner_radius=7, cursor="hand2")

    # ── Activation boutons sur sélection ────────────────────────────────────
    def _quand_selection(self, event=None):
        """Active/désactive les boutons d'action selon la sélection courante."""
        widget = event.widget
        state  = "normal" if widget.selection() else "disabled"

        if hasattr(self, "arbre_carte") and widget == self.arbre_carte:
            self.btn_modifier.configure(state=state)
            self.btn_supprimer.configure(state=state)

        elif hasattr(self, "arbre_util") and widget == self.arbre_util:
            self.btn_modifier.configure(state=state)
            self.btn_supprimer.configure(state=state)
            self.btn_ajouter_carte_util.configure(state=state)

    # ════════════════════════════════════════════════════════════════════════
    #                           DASHBOARD
    # ════════════════════════════════════════════════════════════════════════

    def _afficher_tableau_bord(self):
        """Affiche le tableau de bord avec les 3 panneaux de test matériel."""
        self._definir_nav_active("dashboard")
        self._effacer_contenu()
        self._titre_page("Tableau de bord")

        # Conteneur scrollable pour que tout tienne sur les petits écrans
        outer = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=32, pady=20)

        # ── Bannière statut + voyant d'alarme ──────────────────────────────
        bandeau = ctk.CTkFrame(outer, fg_color="transparent")
        bandeau.pack(fill="x", pady=(0, 20))
        bandeau.columnconfigure(0, weight=1)

        status_card = ctk.CTkFrame(bandeau, fg_color=ACCENT_SOFT, corner_radius=10)
        status_card.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(padx=20, pady=14)
        ctk.CTkLabel(status_inner, text="●", font=("Segoe UI", 10),
                     text_color=SUCCESS).pack(side="left")
        ctk.CTkLabel(status_inner,
            text="  Système opérationnel  —  Raspberry Pi",
            font=FONT_UI, text_color=ACCENT).pack(side="left")

        # Voyant d'alarme (cercle de couleur + label)
        alarme_card = ctk.CTkFrame(bandeau, fg_color=SURFACE, corner_radius=10,
                                   border_width=1, border_color=BORDER)
        alarme_card.grid(row=0, column=1, sticky="e")
        alarme_inner = ctk.CTkFrame(alarme_card, fg_color="transparent")
        alarme_inner.pack(padx=14, pady=10)
        self.alarme_voyant = ctk.CTkLabel(alarme_inner, text="●",
            font=("Segoe UI", 28), text_color=ALARME_OFF)
        self.alarme_voyant.pack(side="left")
        self.alarme_label = ctk.CTkLabel(alarme_inner, text="Alarme inactive",
            font=FONT_BOLD, text_color=TEXT_DIM)
        self.alarme_label.pack(side="left", padx=(8, 4))

        # ── Sélecteur d'heure simulée (partagé par PIR et Porte) ──────────
        heure_card = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10,
                                  border_width=1, border_color=BORDER)
        heure_card.pack(fill="x", pady=(0, 16))
        heure_inner = ctk.CTkFrame(heure_card, fg_color="transparent")
        heure_inner.pack(padx=20, pady=12, anchor="w")

        ctk.CTkLabel(heure_inner, text="🕐 Heure simulée :",
                     font=FONT_BOLD, text_color=TEXT).pack(side="left")
        self.heure_simulee = ctk.StringVar(value="12")
        ctk.CTkComboBox(heure_inner, variable=self.heure_simulee,
            values=[f"{h:02d}" for h in range(24)],
            font=FONT_UI, fg_color=BG, text_color=TEXT,
            button_color=BORDER, button_hover_color=ACCENT_SOFT,
            border_color=BORDER, dropdown_fg_color=SURFACE,
            dropdown_text_color=TEXT, dropdown_hover_color=ACCENT_SOFT,
            state="readonly", width=90, height=32
        ).pack(side="left", padx=(12, 24))
        ctk.CTkLabel(heure_inner,
            text="Horaires de travail : 07h00 → 20h00 — hors plage → déclanchement de l'alarme",
            font=FONT_SMALL, text_color=TEXT_DIM).pack(side="left")

        # Titre section
        ctk.CTkLabel(outer, text="Tests matériel", font=FONT_BOLD,
                     text_color=TEXT_DIM).pack(anchor="w", pady=(0, 10))

        # ── Grille 3 colonnes pour les 3 cartes ───────────────────────────
        grid = ctk.CTkFrame(outer, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2), weight=1, uniform="col")

        self._panneau_rfid(grid, col=0)
        self._panneau_pir(grid,  col=1)
        self._panneau_porte(grid, col=2)

    # ── Panneau RFID ────────────────────────────────────────────────────────
    def _panneau_rfid(self, parent, col):
        """Construit la carte 'Lecteur de badge' du dashboard (Tâche 2)."""
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        ctk.CTkLabel(card, text="Lecteur de badge", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card, text="Vérifier la lecture RFID et le droit d'accès.",
            font=FONT_SMALL, text_color=TEXT_DIM,
            wraplength=260, justify="left").pack(anchor="w", padx=20)

        # Sélecteur du mode de la zone
        ctk.CTkLabel(card, text="Mode de la zone", font=FONT_SMALL,
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(14, 2))
        self.mode_zone = ctk.StringVar(value="Accès Restreint")
        ctk.CTkComboBox(card, variable=self.mode_zone,
            values=["Zone Libre", "Zone Restreinte"],
            font=FONT_UI, fg_color=BG, text_color=TEXT,
            button_color=BORDER, button_hover_color=ACCENT_SOFT,
            border_color=BORDER, dropdown_fg_color=SURFACE,
            dropdown_text_color=TEXT, dropdown_hover_color=ACCENT_SOFT,
            state="readonly", height=32
        ).pack(fill="x", padx=20)

        # Zone de résultats
        self.rfid_result = ctk.CTkFrame(card, fg_color=BG, corner_radius=7,
                                        border_width=1, border_color=BORDER)
        self.rfid_result.pack(fill="x", padx=20, pady=(14, 8))
        self.rfid_badge_lbl = ctk.CTkLabel(self.rfid_result, text="N° badge : —",
            font=FONT_UI, text_color=TEXT, anchor="center", justify="center")
        self.rfid_badge_lbl.pack(fill="x", padx=12, pady=(10, 2))
        self.rfid_user_lbl = ctk.CTkLabel(self.rfid_result, text="Propriétaire : —",
            font=FONT_UI, text_color=TEXT, anchor="center", justify="center")
        self.rfid_user_lbl.pack(fill="x", padx=12, pady=(0, 2))
        self.rfid_status_lbl = ctk.CTkLabel(self.rfid_result, text="Statut : —",
            font=FONT_BIG, text_color=TEXT_DIM,
            anchor="center", justify="center")
        self.rfid_status_lbl.pack(fill="x", padx=12, pady=(4, 10))

        # Ligne de boutons centrés : Réinitialiser + Lancer le test
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(pady=(4, 16))
        ctk.CTkButton(boutons, text="↻ Réinitialiser",
            command=self._reinitialiser_lecteur,
            fg_color=SURFACE, hover_color=ACCENT_SOFT,
            text_color=TEXT_DIM, font=FONT_SMALL,
            border_width=1, border_color=BORDER,
            height=34, corner_radius=7, cursor="hand2"
        ).pack(side="left", padx=4)
        ctk.CTkButton(boutons, text="Lancer le test", command=self._tester_rfid,
            fg_color=ACCENT, hover_color="#1d4ed8",
            text_color="white", font=FONT_UI,
            height=34, corner_radius=7, cursor="hand2"
        ).pack(side="left", padx=4)

    # ── Panneau PIR ─────────────────────────────────────────────────────────
    def _panneau_pir(self, parent, col):
        """Construit la carte 'Capteur PIR' du dashboard (Tâche 3)."""
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        ctk.CTkLabel(card, text="Capteur PIR", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card, text="Détection de mouvement infrarouge passif.",
            font=FONT_SMALL, text_color=TEXT_DIM,
            wraplength=260, justify="left").pack(anchor="w", padx=20)

        # Résultat
        self.pir_status_lbl = ctk.CTkLabel(card, text="État : —",
            font=FONT_BIG, text_color=TEXT_DIM,
            anchor="center", justify="center")
        self.pir_status_lbl.pack(fill="x", padx=20, pady=(18, 4))
        self.pir_alarme_lbl = ctk.CTkLabel(card, text="",
            font=FONT_SMALL, text_color=TEXT_DIM,
            wraplength=260, justify="center", anchor="center")
        self.pir_alarme_lbl.pack(fill="x", padx=20, pady=(0, 8))

        # Bouton toggle centré : démarrer / arrêter la lecture en boucle
        self.btn_pir = ctk.CTkButton(card, text="▶ Démarrer le test",
            command=self._basculer_test_pir,
            fg_color=ACCENT, hover_color="#1d4ed8",
            text_color="white", font=FONT_UI,
            height=34, corner_radius=7, cursor="hand2")
        self.btn_pir.pack(pady=(4, 16))

    # ── Panneau Porte ───────────────────────────────────────────────────────
    def _panneau_porte(self, parent, col):
        """Construit la carte 'Détecteur de porte' du dashboard (Tâche 4)."""
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        ctk.CTkLabel(card, text="Détecteur de porte", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card, text="État du contact d'ouverture, lecture en continu.",
            font=FONT_SMALL, text_color=TEXT_DIM,
            wraplength=260, justify="left").pack(anchor="w", padx=20)

        # Résultat
        self.porte_status_lbl = ctk.CTkLabel(card, text="État : —",
            font=FONT_BIG, text_color=TEXT_DIM,
            anchor="center", justify="center")
        self.porte_status_lbl.pack(fill="x", padx=20, pady=(18, 4))
        self.porte_alarme_lbl = ctk.CTkLabel(card, text="",
            font=FONT_SMALL, text_color=TEXT_DIM,
            wraplength=260, justify="center", anchor="center")
        self.porte_alarme_lbl.pack(fill="x", padx=20, pady=(0, 8))

        # Bouton toggle centré : démarrer / arrêter la lecture en boucle
        self.btn_porte = ctk.CTkButton(card, text="▶ Démarrer le test",
            command=self._basculer_test_porte,
            fg_color=ACCENT, hover_color="#1d4ed8",
            text_color="white", font=FONT_UI,
            height=34, corner_radius=7, cursor="hand2")
        self.btn_porte.pack(pady=(4, 16))

    # ════════════════════════════════════════════════════════════════════════
    #                           ALARME (clignotement)
    # ════════════════════════════════════════════════════════════════════════

    def _demarrer_alarme(self, motif=""):
        """
        Démarre le clignotement du voyant d'alarme sur le dashboard.
        Idempotente : si l'alarme tourne déjà, on met juste à jour le motif
        et on évite de relancer une seconde chaîne de clignotement.

        :param motif: texte affiché à côté du voyant pour expliquer la cause.
        """
        if hasattr(self, "alarme_label") and self.alarme_label.winfo_exists():
            self.alarme_label.configure(text=f"ALARME — {motif}" if motif else "ALARME",
                                        text_color=DANGER)
        if not self._alarme_active:
            self._alarme_active = True
            self._basculer_alarme()

    def _mettre_a_jour_alarme(self):
        """
        Décide si le voyant global doit clignoter en fonction des contributions
        individuelles des capteurs PIR et porte (alarme = OU logique).
        """
        if self._pir_alarme or self._porte_alarme:
            motifs = []
            if self._pir_alarme:
                motifs.append("mouvement")
            if self._porte_alarme:
                motifs.append("porte ouverte")
            self._demarrer_alarme(motif=" + ".join(motifs) + " hors horaires")
        else:
            self._arreter_alarme()

    def _arreter_alarme(self):
        """Arrête le clignotement du voyant d'alarme et le remet en état repos."""
        self._alarme_active = False
        self._alarme_etat = False
        if hasattr(self, "alarme_voyant") and self.alarme_voyant.winfo_exists():
            self.alarme_voyant.configure(text_color=ALARME_OFF)
        if hasattr(self, "alarme_label") and self.alarme_label.winfo_exists():
            self.alarme_label.configure(text="Alarme inactive", text_color=TEXT_DIM)

    def _basculer_alarme(self):
        """Bascule la couleur du voyant pour produire le clignotement."""
        if not self._alarme_active:
            return
        if not (hasattr(self, "alarme_voyant") and self.alarme_voyant.winfo_exists()):
            self._alarme_active = False
            return
        self._alarme_etat = not self._alarme_etat
        couleur = ALARME_ON if self._alarme_etat else ALARME_OFF
        self.alarme_voyant.configure(text_color=couleur)
        # Re-déclenche après 500 ms tant que l'alarme est active
        self.after(500, self._basculer_alarme)

    # ════════════════════════════════════════════════════════════════════════
    #                           TESTS MATÉRIEL
    # ════════════════════════════════════════════════════════════════════════

    def _reinitialiser_lecteur(self):
        """
        Force la libération du verrou du lecteur RFID côté API.

        Utile lorsqu'une lecture précédente est restée bloquée (IHM fermée
        en cours de scan, perte réseau, etc.) et que toutes les nouvelles
        lectures retournent « Lecture déjà en cours ».
        """
        def tache():
            """Appelle /liberer_verrou en arrière-plan."""
            try:
                resp = requests.post(
                    f"http://{RESEAU['IP']}:5000/liberer_verrou", timeout=5)
                ok = resp.ok
                msg = resp.text
            except Exception as e:
                ok, msg = False, str(e)

            def rappel():
                if ok:
                    messagebox.showinfo("Lecteur réinitialisé",
                        "Le verrou du lecteur a été libéré.\n"
                        "Vous pouvez relancer un scan.")
                else:
                    messagebox.showerror("Erreur",
                        f"Impossible de réinitialiser le lecteur :\n{msg}")
            self.after(0, rappel)

        threading.Thread(target=tache, daemon=True).start()

    def _tester_rfid(self):
        """
        Lance un test RFID : scanne la carte, récupère l'utilisateur associé
        et affiche le statut « Accès Autorisé / Refusé » selon le mode choisi.
        Le scan étant bloquant côté API, l'appel est effectué dans un thread.
        """
        mode = "libre" if self.mode_zone.get() == "Zone Libre" else "restreinte"
        self.rfid_badge_lbl.configure(text="N° badge : (lecture en cours…)")
        self.rfid_user_lbl.configure(text="Propriétaire : —")
        self.rfid_status_lbl.configure(text="Statut : …", text_color=TEXT_DIM)

        def tache():
            try:
                resp = requests.get(
                    f"http://{RESEAU['IP']}:5000/scanner_acces/{mode}",
                    timeout=60
                )
                data = resp.json()
            except Exception as e:
                data = {"_erreur": str(e)}

            # Retour vers le thread principal pour mettre à jour l'IHM
            self.after(0, lambda: self._afficher_resultat_rfid(data))

        threading.Thread(target=tache, daemon=True).start()

    def _afficher_resultat_rfid(self, data):
        """Met à jour l'affichage du panneau RFID à partir du JSON reçu."""
        if "_erreur" in data:
            self.rfid_badge_lbl.configure(text="N° badge : —")
            self.rfid_user_lbl.configure(text="Propriétaire : —")
            self.rfid_status_lbl.configure(text="Statut : Erreur API",
                                           text_color=DANGER)
            messagebox.showerror("Erreur",
                f"Impossible de contacter le Raspberry :\n{data['_erreur']}")
            return

        # Cas d'une erreur explicite renvoyée par l'API (ex : verrou bloqué)
        if "Erreur" in data:
            self.rfid_badge_lbl.configure(text="N° badge : —")
            self.rfid_user_lbl.configure(text="Propriétaire : —")
            self.rfid_status_lbl.configure(text=f"⚠ {data['Erreur']}",
                                           text_color=DANGER)
            messagebox.showwarning("Lecteur indisponible",
                f"{data['Erreur']}\n\n"
                "Cliquez sur « Réinitialiser le lecteur » pour libérer le verrou.")
            return

        id_badge = data.get("id_badge", "—")
        nom      = data.get("nom") or "—"
        prenom   = data.get("prenom") or ""
        autorise = bool(data.get("autorise"))
        motif    = data.get("motif", "")

        self.rfid_badge_lbl.configure(text=f"N° badge : {id_badge}")
        self.rfid_user_lbl.configure(
            text=f"Propriétaire : {nom} {prenom}".strip())

        if autorise:
            self.rfid_status_lbl.configure(text="✓ ",
                                           text_color=SUCCESS)
        else:
            self.rfid_status_lbl.configure(text="✗ ",
                                           text_color=DANGER)

        # Affiche le motif dans une infobulle simple (popup léger)
        if motif:
            self.rfid_status_lbl.configure(text=f"{self.rfid_status_lbl.cget('text')} {motif}")

    # ── PIR : toggle, boucle de polling, affichage ──────────────────────────

    def _basculer_test_pir(self):
        """Bascule entre démarrage et arrêt de la lecture PIR en continu."""
        if self._pir_running:
            self._arreter_boucle_pir()
        else:
            self._demarrer_boucle_pir()

    def _demarrer_boucle_pir(self):
        """
        Démarre la lecture PIR en boucle (polling). Le bouton passe en rouge
        « ⏹ Arrêter le test » jusqu'à ce que l'utilisateur reclique dessus.
        """
        self._pir_running = True
        self.btn_pir.configure(text="⏹ Arrêter le test",
            fg_color=DANGER, hover_color="#b91c1c")
        self.pir_status_lbl.configure(text="État : (démarrage…)",
                                      text_color=TEXT_DIM)
        self.pir_alarme_lbl.configure(text="")
        self._lire_pir_periodique()

    def _arreter_boucle_pir(self):
        """
        Arrête la lecture PIR en boucle, remet le bouton en mode démarrage
        et purge la contribution du PIR à l'alarme globale.
        """
        self._pir_running = False
        self._pir_alarme  = False
        if hasattr(self, "btn_pir") and self.btn_pir.winfo_exists():
            self.btn_pir.configure(text="▶ Démarrer le test",
                fg_color=ACCENT, hover_color="#1d4ed8")
        if hasattr(self, "pir_status_lbl") and self.pir_status_lbl.winfo_exists():
            self.pir_status_lbl.configure(text="État : —", text_color=TEXT_DIM)
        if hasattr(self, "pir_alarme_lbl") and self.pir_alarme_lbl.winfo_exists():
            self.pir_alarme_lbl.configure(text="")
        self._mettre_a_jour_alarme()

    def _lire_pir_periodique(self):
        """
        Effectue une lecture PIR via l'API en arrière-plan puis planifie la
        suivante (toutes les ~1 s) tant que la boucle est active.
        """
        if not self._pir_running:
            return

        def tache():
            """Appelle /test_PIR puis remet la main au thread Tkinter."""
            try:
                resp = requests.get(
                    f"http://{RESEAU['IP']}:5000/test_PIR", timeout=10)
                data = resp.json()
            except Exception as e:
                data = {"_erreur": str(e)}

            def rappel():
                """Affiche le résultat puis enchaîne avec le prochain poll."""
                self._afficher_resultat_pir(data)
                if self._pir_running:
                    self.after(1000, self._lire_pir_periodique)
            self.after(0, rappel)

        threading.Thread(target=tache, daemon=True).start()

    def _afficher_resultat_pir(self, data):
        """Met à jour l'affichage du panneau PIR et met à jour l'alarme globale."""
        if "_erreur" in data:
            self.pir_status_lbl.configure(text="État : Erreur API",
                                          text_color=DANGER)
            # Sur erreur, on coupe la boucle pour ne pas spammer l'utilisateur
            messagebox.showerror("Erreur",
                f"Impossible de lire le PIR :\n{data['_erreur']}")
            self._arreter_boucle_pir()
            return

        mouvement = bool(data.get("mouvement"))
        heure = self.heure_simulee.get() if hasattr(self, "heure_simulee") else "12"
        hors  = hors_horaires(heure)

        if mouvement:
            self.pir_status_lbl.configure(text="● Mouvement détecté",
                                          text_color=WARNING)
        else:
            self.pir_status_lbl.configure(text="○ Aucun mouvement",
                                          text_color=SUCCESS)

        if mouvement and hors:
            self.pir_alarme_lbl.configure(
                text=f"⚠ Intrusion suspectée à {heure}h "
                     "(hors horaires de travail).", text_color=DANGER)
            self._pir_alarme = True
        else:
            if mouvement:
                self.pir_alarme_lbl.configure(
                    text=f"Mouvement à {heure}h — dans les horaires : pas d'alarme.",
                    text_color=TEXT_DIM)
            else:
                self.pir_alarme_lbl.configure(
                    text="Pas d'alarme.", text_color=TEXT_DIM)
            self._pir_alarme = False

        self._mettre_a_jour_alarme()

    # ── Porte : toggle, boucle de polling, affichage ────────────────────────

    def _basculer_test_porte(self):
        """Bascule entre démarrage et arrêt de la lecture porte en continu."""
        if self._porte_running:
            self._arreter_boucle_porte()
        else:
            self._demarrer_boucle_porte()

    def _demarrer_boucle_porte(self):
        """
        Démarre la lecture porte en boucle (polling). Le bouton passe en rouge
        « ⏹ Arrêter le test » jusqu'à ce que l'utilisateur reclique dessus.
        """
        self._porte_running = True
        self.btn_porte.configure(text="⏹ Arrêter le test",
            fg_color=DANGER, hover_color="#b91c1c")
        self.porte_status_lbl.configure(text="État : (démarrage…)",
                                        text_color=TEXT_DIM)
        self.porte_alarme_lbl.configure(text="")
        self._lire_porte_periodique()

    def _arreter_boucle_porte(self):
        """
        Arrête la lecture porte en boucle, remet le bouton en mode démarrage
        et purge la contribution de la porte à l'alarme globale.
        """
        self._porte_running = False
        self._porte_alarme  = False
        if hasattr(self, "btn_porte") and self.btn_porte.winfo_exists():
            self.btn_porte.configure(text="▶ Démarrer le test",
                fg_color=ACCENT, hover_color="#1d4ed8")
        if hasattr(self, "porte_status_lbl") and self.porte_status_lbl.winfo_exists():
            self.porte_status_lbl.configure(text="État : —", text_color=TEXT_DIM)
        if hasattr(self, "porte_alarme_lbl") and self.porte_alarme_lbl.winfo_exists():
            self.porte_alarme_lbl.configure(text="")
        self._mettre_a_jour_alarme()

    def _lire_porte_periodique(self):
        """
        Effectue une lecture porte via l'API en arrière-plan puis planifie la
        suivante (toutes les ~1 s) tant que la boucle est active.
        """
        if not self._porte_running:
            return

        def tache():
            """Appelle /test_porte puis remet la main au thread Tkinter."""
            try:
                resp = requests.get(
                    f"http://{RESEAU['IP']}:5000/test_porte", timeout=10)
                data = resp.json()
            except Exception as e:
                data = {"_erreur": str(e)}

            def rappel():
                """Affiche le résultat puis enchaîne avec le prochain poll."""
                self._afficher_resultat_porte(data)
                if self._porte_running:
                    self.after(1000, self._lire_porte_periodique)
            self.after(0, rappel)

        threading.Thread(target=tache, daemon=True).start()

    def _afficher_resultat_porte(self, data):
        """Met à jour l'affichage du panneau porte et met à jour l'alarme globale."""
        if "_erreur" in data:
            self.porte_status_lbl.configure(text="État : Erreur API",
                                            text_color=DANGER)
            messagebox.showerror("Erreur",
                f"Impossible de lire la porte :\n{data['_erreur']}")
            self._arreter_boucle_porte()
            return

        ouverte = bool(data.get("ouverte"))
        heure = self.heure_simulee.get() if hasattr(self, "heure_simulee") else "12"
        hors  = hors_horaires(heure)

        if ouverte:
            self.porte_status_lbl.configure(text="🚪 Porte Ouverte",
                                            text_color=WARNING)
        else:
            self.porte_status_lbl.configure(text="🚪 Porte Fermée",
                                            text_color=SUCCESS)

        if ouverte and hors:
            self.porte_alarme_lbl.configure(
                text=f"⚠ Porte ouverte à {heure}h "
                     "(hors horaires de travail).", text_color=DANGER)
            self._porte_alarme = True
        else:
            if ouverte:
                self.porte_alarme_lbl.configure(
                    text=f"Porte ouverte à {heure}h — dans les horaires : pas d'alarme.",
                    text_color=TEXT_DIM)
            else:
                self.porte_alarme_lbl.configure(
                    text="Pas d'alarme.", text_color=TEXT_DIM)
            self._porte_alarme = False

        self._mettre_a_jour_alarme()

    # ════════════════════════════════════════════════════════════════════════
    #                           ONGLET CARTE
    # ════════════════════════════════════════════════════════════════════════

    def _affichage_onglet_carte(self):
        """Affiche l'onglet 'Gestion des cartes' (CRUD sur les badges)."""
        self._definir_nav_active("cartes")
        self._effacer_contenu()
        self._titre_page("Gestion des cartes",
                         sous_titre="Badges RFID enregistrés dans le système")

        tb = self._barre_outils()
        self._btn_principal(tb, "+ Ajouter",
                          lambda: self._ouvrir_scan_puis_modale("carte")
                          ).pack(side="left", padx=(0, 6))
        self.btn_modifier = self._btn_secondaire(tb, "Modifier",
                            lambda: modifier_carte(self), state="disabled")
        self.btn_modifier.pack(side="left", padx=(0, 6))
        self.btn_supprimer = self._btn_danger(tb, "Supprimer",
                             lambda: supprimer_carte(self), state="disabled")
        self.btn_supprimer.pack(side="left")
        self._btn_secondaire(tb, "↻ Actualiser",
                            lambda: charger_carte(self)
                            ).pack(side="right")

        wrap = ctk.CTkFrame(self.content, fg_color=SURFACE,
                            corner_radius=10, border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        scroll = ttk.Scrollbar(wrap, style="Light.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y", pady=2)

        self.arbre_carte = ttk.Treeview(wrap,
            columns=("id", "texte", "id_util", "date_ajout", "der_connexion"),
            show="headings", style="Light.Treeview",
            yscrollcommand=scroll.set)
        scroll.config(command=self.arbre_carte.yview)

        for col, label, width in [
            ("id",         "ID Badge",          100),
            ("texte",      "Texte",             100),
            ("id_util",    "ID Utilisateur",    20),
            ("date_ajout", "Date de création",  160),
            ("der_connexion", "Dernier badgeage", 160)
        ]:
            self.arbre_carte.heading(col, text=label)
            self.arbre_carte.column(col, width=width, anchor="center")

        self.arbre_carte.pack(fill="both", expand=True, padx=2, pady=2)
        self.arbre_carte.bind("<<TreeviewSelect>>", self._quand_selection)
        charger_carte(self)

    # ════════════════════════════════════════════════════════════════════════
    #                           ONGLET UTILISATEURS
    # ════════════════════════════════════════════════════════════════════════

    def _affichage_onglet_util(self):
        """Affiche l'onglet 'Gestion des utilisateurs' (CRUD)."""
        self._definir_nav_active("utilisateurs")
        self._effacer_contenu()
        self._titre_page("Gestion des utilisateurs",
                         sous_titre="Personnes autorisées à accéder au système")

        tb = self._barre_outils()
        self._btn_principal(tb, "+ Ajouter",
                          lambda: ajouter_util(self)
                          ).pack(side="left", padx=(0, 6))
        self.btn_modifier = self._btn_secondaire(tb, "Modifier",
                            lambda: modifier_util(self), state="disabled")
        self.btn_modifier.pack(side="left", padx=(0, 6))
        self.btn_supprimer = self._btn_danger(tb, "Supprimer",
                             lambda: supprimer_util(self), state="disabled")
        self.btn_supprimer.pack(side="left", padx=(0, 6))
        self.btn_ajouter_carte_util = self._btn_secondaire(tb, "Ajouter une carte",
            lambda: self._ouvrir_scan_puis_modale("util"), state="disabled")
        self.btn_ajouter_carte_util.pack(side="left")
        self._btn_secondaire(tb, "↻ Actualiser",
                            lambda: charger_util(self)
                            ).pack(side="right")

        wrap = ctk.CTkFrame(self.content, fg_color=SURFACE,
                            corner_radius=10, border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        scroll = ttk.Scrollbar(wrap, style="Light.Vertical.TScrollbar")
        scroll.pack(side="right", fill="y", pady=2)

        self.arbre_util = ttk.Treeview(wrap,
            columns=("id", "nom", "prenom", "badges", "droits"),
            show="headings", style="Light.Treeview",
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
            self.arbre_util.column(col, width=width, anchor="center")

        self.arbre_util.pack(fill="both", expand=True, padx=2, pady=2)
        self.arbre_util.bind("<<TreeviewSelect>>", self._quand_selection)
        charger_util(self)

    # ════════════════════════════════════════════════════════════════════════
    #                           FENÊTRE MODALE GÉNÉRIQUE
    # ════════════════════════════════════════════════════════════════════════

    def _modale(self, titre, champs, quand_validation, prerempli=None):
        """
        Affiche une fenêtre modale générique de saisie.

        :param titre:            titre de la fenêtre.
        :param champs:           liste de tuples (clé, label, [type, [choix]]).
        :param quand_validation: rappel (data, win) appelé au clic sur Valider.
        :param prerempli:        dict optionnel pour pré-remplir les champs.
        """
        win = ctk.CTkToplevel(self)
        win.title(titre)
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.grab_set()

        # En-tête
        header = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=titre, font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(18, 16))
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x")

        # Formulaire
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", padx=24, pady=(12, 0))

        champs_saisie = {}
        est_util  = titre in ("Ajouter un utilisateur",  "Modifier un utilisateur")
        est_carte = titre in ("Ajouter une carte", "Modifier une carte",
                              "Créer et assigner la carte")

        def _creer_champ(cle, libelle, lecture_seule=False):
            ctk.CTkLabel(body, text=libelle, font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(anchor="w", pady=(10, 2))
            e = ctk.CTkEntry(body, font=FONT_UI, fg_color=SURFACE,
                text_color=TEXT, border_color=BORDER, border_width=1,
                placeholder_text_color=TEXT_LIGHT, height=36)
            e.pack(fill="x")
            if prerempli and cle in prerempli:
                e.insert(0, prerempli[cle])
            if lecture_seule:
                e.configure(state="disabled",
                            fg_color="#f3f4f6", text_color=TEXT_DIM)
            champs_saisie[cle] = e

        if est_util:
            for champ in champs:
                cle, libelle, *options = champ
                type_widget = options[0] if options else "entry"
                choix       = options[1] if len(options) > 1 else []
                if type_widget == "combo":
                    ctk.CTkLabel(body, text=libelle, font=FONT_SMALL,
                                 text_color=TEXT_DIM).pack(anchor="w", pady=(10, 2))
                    cb = ctk.CTkComboBox(body, values=choix, font=FONT_UI,
                        fg_color=SURFACE, text_color=TEXT,
                        button_color=BORDER, button_hover_color=ACCENT_SOFT,
                        border_color=BORDER, dropdown_fg_color=SURFACE,
                        dropdown_text_color=TEXT, dropdown_hover_color=ACCENT_SOFT,
                        state="readonly", height=36)
                    cb.set(choix[0] if choix else "")
                    if prerempli and cle in prerempli and prerempli[cle]:
                        cb.set(prerempli[cle])
                    cb.pack(fill="x")
                    champs_saisie[cle] = cb
                else:
                    _creer_champ(cle, libelle, lecture_seule=(cle == "id_util"))

        elif est_carte:
            for champ in champs:
                cle, libelle, *_ = champ
                _creer_champ(cle, libelle, lecture_seule=(cle == "id_badge"))

        # Pied de page
        tkinter.Frame(win, bg=BORDER, height=1).pack(fill="x", pady=(16, 0))
        footer = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
        footer.pack(fill="x")

        def valider():
            data = {}
            for k, e in champs_saisie.items():
                if isinstance(e, ctk.CTkComboBox):
                    data[k] = e.get()
                else:
                    etat_precedent = e.cget("state")
                    e.configure(state="normal")
                    data[k] = e.get()
                    e.configure(state=etat_precedent)
            quand_validation(data, win)

        ctk.CTkButton(footer, text="Annuler", command=win.destroy,
            fg_color="transparent", hover_color=ACCENT_SOFT,
            text_color=TEXT_DIM, font=FONT_UI,
            border_width=1, border_color=BORDER,
            height=34, corner_radius=7,
            cursor="hand2").pack(side="right", padx=(6, 20), pady=14)

        ctk.CTkButton(footer, text="Valider", command=valider,
            fg_color=ACCENT, hover_color="#1d4ed8",
            text_color="white", font=FONT_BOLD,
            height=34, corner_radius=7,
            cursor="hand2").pack(side="right", pady=14)

        win.geometry(f"400x{180 + len(champs) * 72}")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    # ════════════════════════════════════════════════════════════════════════
    #                   FONCTION OUVRIR FENETRE SCAN PUIS MODAL
    # ════════════════════════════════════════════════════════════════════════

    def _ouvrir_scan_puis_modale(self, nature):
        """
        Lance le flux scan-puis-modal selon la nature de l'action.

        :param nature: 'carte' → ajouter une nouvelle carte (libre).
                       'util'  → assigner une carte à un utilisateur sélectionné.
                                 Cas A : carte connue → assignation directe.
                                 Cas B : carte inconnue → ouverture automatique
                                         d'une modale 'Ajouter une carte' puis
                                         assignation à l'utilisateur.
        """
        if nature == "carte":
            champs_carte = [
                ("id_badge", "ID Badge"),
                ("texte",    "Texte / libellé"),
                ("id_util",  "ID Utilisateur"),
            ]

            def valider(data, win):
                """Envoie la création de carte à l'API."""
                reponse = envoi_requete(ip=RESEAU["IP"], port=5000,
                                        endpoint="/ajouter_une_carte",
                                        valeur=data)
                messagebox.showinfo("Résultat", reponse, parent=win)
                charger_carte(self)
                win.destroy()

            def apres_scan(id_badge):
                """Ouvre la modale d'ajout pré-remplie avec l'id scanné."""
                self._modale(titre="Ajouter une carte",
                            champs=champs_carte,
                            quand_validation=valider,
                            prerempli={"id_badge": id_badge})

            fenetre_scan_carte(self, quand_carte_scannee=apres_scan)
            return

        if nature == "util":
            sel = self.arbre_util.selection()
            if not sel:
                messagebox.showwarning("Attention",
                    "Sélectionnez d'abord un utilisateur.")
                return
            id_util = self.arbre_util.item(sel[0], "values")[0]

            def apres_scan(id_badge):
                """
                Étape 1 — Vérifie en base si la carte existe.
                Cas A : assignation directe.
                Cas B : ouverture automatique de la modale d'ajout.
                """
                try:
                    resp = requests.get(
                        f"http://{RESEAU['IP']}:5000/verifier_carte/{id_badge}",
                        timeout=10)
                    result = resp.json()
                except Exception as e:
                    messagebox.showerror("Erreur",
                        f"Impossible de vérifier la carte :\n{e}")
                    return

                if result.get("existe"):
                    # ── Cas A : carte connue → assignation directe ─────────
                    reponse = envoi_requete(
                        ip=RESEAU["IP"], port=5000,
                        endpoint=f"/ajouter_une_carte_a_util/{id_util}",
                        valeur={"id_badge": id_badge})
                    messagebox.showinfo("Résultat", reponse)
                    charger_util(self)
                else:
                    # ── Cas B : carte inconnue → modale 'Ajouter une carte' ─
                    def valider_creation(data, win):
                        """Crée la carte ET l'assigne à l'utilisateur courant."""
                        data["id_badge"] = id_badge
                        data["id_util"]  = id_util
                        reponse = envoi_requete(
                            ip=RESEAU["IP"], port=5000,
                            endpoint="/creer_et_assigner_carte",
                            valeur=data)
                        messagebox.showinfo("Résultat", reponse, parent=win)
                        win.destroy()
                        charger_util(self)

                    self._modale(
                        titre="Créer et assigner la carte",
                        champs=[
                            ("id_badge", "ID Badge"),
                            ("texte",    "Libellé"),
                        ],
                        quand_validation=valider_creation,
                        prerempli={"id_badge": id_badge})

            fenetre_scan_util(self, quand_carte_scannee=apres_scan)


if __name__ == "__main__":
    app = App()
    app.mainloop()
