"""
Paramètres globaux de l'IHM : configuration réseau, palette de couleurs,
polices et règles métier (horaires de travail).
"""

# ── Configuration réseau (modifiable depuis la fenêtre de connexion) ─────
RESEAU = {
    "IP": "192.168.4.1"
}

# ── Palette de couleurs ─────────────────────────────────────────────────
BG          = "#f5f5f7"
SURFACE     = "#ffffff"
SIDEBAR     = "#fafafa"
BORDER      = "#e4e4e7"
ACCENT      = "#2563eb"
ACCENT_SOFT = "#eff6ff"
DANGER      = "#dc2626"
DANGER_SOFT = "#fef2f2"
SUCCESS     = "#16a34a"
SUCCESS_SOFT = "#ecfdf5"
WARNING     = "#f59e0b"
WARNING_SOFT = "#fffbeb"
TEXT        = "#111827"
TEXT_DIM    = "#6b7280"
TEXT_LIGHT  = "#9ca3af"

# ── Couleurs spécifiques voyant d'alarme ─────────────────────────────────
ALARME_ON   = "#dc2626"   # rouge vif (alarme active)
ALARME_OFF  = "#e5e7eb"   # gris clair (alarme inactive)

# ── Polices ──────────────────────────────────────────────────────────────
FONT_UI     = ("Segoe UI", 11)
FONT_BOLD   = ("Segoe UI", 11, "bold")
FONT_HEAD   = ("Segoe UI", 17, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_TINY   = ("Segoe UI", 8)
FONT_BIG    = ("Segoe UI", 14, "bold")

# ── Règles métier ────────────────────────────────────────────────────────
# Horaires de travail : tout évènement détecté en dehors de cette plage
# déclenche l'alarme visuelle (clignotement).
HEURE_DEBUT_TRAVAIL = 7    # 07h00 inclus
HEURE_FIN_TRAVAIL   = 20   # 20h00 exclus


def hors_horaires(heure):
    """
    Détermine si une heure (entier 0-23) est en dehors des horaires de travail.

    :param heure: heure simulée par l'opérateur (0-23).
    :return: True si l'heure est hors plage [HEURE_DEBUT, HEURE_FIN[, sinon False.
    """
    try:
        h = int(heure)
    except (TypeError, ValueError):
        return False
    return not (HEURE_DEBUT_TRAVAIL <= h < HEURE_FIN_TRAVAIL)
