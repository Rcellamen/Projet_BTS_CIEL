"""
Tests unitaires pour la fonction `hors_horaires` (App/Outils/parametres.py).

Cette fonction est critique car elle conditionne le déclenchement de
l'alarme dans l'IHM : si elle se trompe sur la plage horaire, l'alarme
peut soit ne jamais se déclencher, soit hurler en pleine journée.
"""

import pytest
from src.App.Outils.parametres import (
    hors_horaires,
    HEURE_DEBUT_TRAVAIL,
    HEURE_FIN_TRAVAIL,
)


class TestHorsHoraires:
    """Tests de la logique des horaires de travail (7h-20h par défaut)."""

    # ── Bornes inclusives / exclusives ───────────────────────────────────
    def test_heure_debut_inclusive(self):
        """7h00 doit être considéré comme HEURE DE TRAVAIL (borne incluse)."""
        assert hors_horaires(HEURE_DEBUT_TRAVAIL) is False

    def test_heure_fin_exclusive(self):
        """20h00 doit être considéré comme HORS HORAIRES (borne exclue)."""
        assert hors_horaires(HEURE_FIN_TRAVAIL) is True

    # ── Heures dans la plage de travail ──────────────────────────────────
    @pytest.mark.parametrize("heure", [7, 8, 12, 15, 18, 19])
    def test_heure_dans_plage_travail(self, heure):
        """Toutes les heures de la plage de travail doivent retourner False."""
        assert hors_horaires(heure) is False

    # ── Heures hors plage de travail ─────────────────────────────────────
    @pytest.mark.parametrize("heure", [0, 1, 5, 6, 20, 21, 22, 23])
    def test_heure_hors_plage_travail(self, heure):
        """Toutes les heures hors plage doivent retourner True."""
        assert hors_horaires(heure) is True

    # ── Acceptation de strings (le combobox de l'IHM renvoie des str) ────
    def test_heure_str_dans_plage(self):
        """L'IHM passe l'heure sous forme de chaîne ('12') : doit fonctionner."""
        assert hors_horaires("12") is False

    def test_heure_str_hors_plage(self):
        """Idem avec une heure hors plage en chaîne ('23')."""
        assert hors_horaires("23") is True

    def test_heure_str_avec_zero(self):
        """Format '07' avec un zéro initial doit aussi fonctionner."""
        assert hors_horaires("07") is False

    # ── Robustesse face aux entrées invalides ────────────────────────────
    def test_heure_none_retourne_false(self):
        """None ne doit pas planter, mais retourner False (mode permissif)."""
        assert hors_horaires(None) is False

    def test_heure_str_invalide_retourne_false(self):
        """Une chaîne non numérique ne doit pas planter."""
        assert hors_horaires("midi") is False

    def test_heure_vide_retourne_false(self):
        """Une chaîne vide ne doit pas planter."""
        assert hors_horaires("") is False
