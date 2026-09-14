"""Rendering tests for the liasse PDF template.

Guards the two things that were silently wrong before 2026-09-14:
- the Amort/Prov column was hardcoded to 0
- the coherence report was computed but never displayed
"""

import re

import pytest
from jinja2 import Environment, FileSystemLoader

from app.services.financial_engine import compute_financial_statements

TEMPLATE_DIR = "app/templates"
TEMPLATE_NAME = "liasse_template.html"


@pytest.fixture(scope="module")
def template():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    return env.get_template(TEMPLATE_NAME)


def render(template, rows):
    statements = compute_financial_statements(rows)
    return template.render(
        statements=statements, client_info={}, ai_commentary=None, exercice="2026"
    )


@pytest.fixture
def rows_equilibre():
    """Actif net 800k (1M brut - 200k amort) == Passif 800k."""
    return [
        {"compte": "241", "debit": 1_000_000, "credit": 0},
        {"compte": "2841", "debit": 0, "credit": 200_000},
        {"compte": "101", "debit": 0, "credit": 800_000},
    ]


@pytest.fixture
def rows_desequilibre():
    """Actif net 800k vs Passif 650k: 141 (non mappe) absorbs 150k."""
    return [
        {"compte": "241", "debit": 1_000_000, "credit": 0},
        {"compte": "2841", "debit": 0, "credit": 200_000},
        {"compte": "141", "debit": 0, "credit": 150_000},
        {"compte": "101", "debit": 0, "credit": 650_000},
    ]


@pytest.mark.unit
class TestColonneAmortissements:
    def test_la_colonne_amort_nest_plus_codee_en_dur(self, template, rows_equilibre):
        html = render(template, rows_equilibre)
        ligne = re.search(r"Immobilisations incorporelles.*?</tr>", html, re.S)
        montants = re.findall(r'class="amount">([^<]*)<', ligne.group(0))

        # brut, amort, net, net_n_1
        assert montants[0] == "1 000 000"
        assert montants[1] == "200 000", "la colonne Amort/Prov restait a 0"
        assert montants[2] == "800 000"

    def test_le_total_actif_agrege_les_amortissements(self, template, rows_equilibre):
        html = render(template, rows_equilibre)
        ligne = re.search(r"TOTAL ACTIF.*?</tr>", html, re.S)
        montants = re.findall(r'class="amount">([^<]*)<', ligne.group(0))

        assert montants[1] == "200 000"


@pytest.mark.unit
class TestBandeauCoherence:
    def test_bandeau_absent_quand_equilibre(self, template, rows_equilibre):
        assert "BILAN NON ÉQUILIBRÉ" not in render(template, rows_equilibre)

    def test_bandeau_present_quand_desequilibre(self, template, rows_desequilibre):
        html = render(template, rows_desequilibre)
        assert "BILAN NON ÉQUILIBRÉ" in html
        assert "150 000" in html
        assert "actif &gt; passif" in html or "actif > passif" in html


@pytest.mark.unit
class TestAnnexeDeControle:
    def test_annexe_toujours_presente(self, template, rows_equilibre):
        assert "ANNEXE DE CONTRÔLE" in render(template, rows_equilibre)

    def test_annexe_confirme_lequilibre(self, template, rows_equilibre):
        html = render(template, rows_equilibre)
        assert "Bilan équilibré" in html
        assert "COMPTES SUSPECTS" not in html

    def test_annexe_liste_les_classes_et_les_suspects(self, template, rows_desequilibre):
        html = render(template, rows_desequilibre)

        assert "TOTAUX PAR CLASSE" in html
        assert "Classe 1 - Ressources durables" in html
        assert "COMPTES SUSPECTS" in html
        assert "141" in html
        assert "non mappe" in html

    def test_rendu_sans_cle_coherence_ne_casse_pas(self, template, rows_equilibre):
        """Older payloads without the coherence key must still render."""
        statements = compute_financial_statements(rows_equilibre)
        statements.pop("coherence")

        html = template.render(
            statements=statements, client_info={}, ai_commentary=None, exercice="2026"
        )
        assert "ANNEXE DE CONTRÔLE" not in html
        assert "TOTAL ACTIF" in html
