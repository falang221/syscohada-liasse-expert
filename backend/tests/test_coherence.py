"""Tests for the SYSCOHADA balance-sheet coherence rule.

Fixtures only - no real accounting data is used.
"""

import pytest

from app.core.coherence import (
    TOLERANCE_XOF,
    check_balance_coherence,
    format_anomaly_report,
    get_account_class,
)
from app.core.syscohada_rules import get_category_for_account
from app.services.financial_engine import compute_financial_statements


@pytest.fixture
def bilan_equilibre():
    """Balanced sheet: Actif 1 500 000 == Passif 1 500 000.

    Actif : 241 materiel 1 000 000 + 311 stocks 300 000 + 521 banque 200 000
    Passif: 101 capital 1 200 000 + 401 fournisseurs 300 000
    """
    return [
        {"compte": "241", "debit": 1_000_000, "credit": 0},
        {"compte": "311", "debit": 300_000, "credit": 0},
        {"compte": "521", "debit": 200_000, "credit": 0},
        {"compte": "101", "debit": 0, "credit": 1_200_000},
        {"compte": "401", "debit": 0, "credit": 300_000},
    ]


@pytest.fixture
def bilan_desequilibre():
    """Unbalanced sheet: Actif 1 500 000 vs Passif 1 200 000, gap 300 000.

    The 401 fournisseurs entry is missing, which is the classic symptom of a
    truncated trial-balance export.
    """
    return [
        {"compte": "241", "debit": 1_000_000, "credit": 0},
        {"compte": "311", "debit": 300_000, "credit": 0},
        {"compte": "521", "debit": 200_000, "credit": 0},
        {"compte": "101", "debit": 0, "credit": 1_200_000},
    ]


@pytest.mark.unit
class TestBilanEquilibre:
    def test_detecte_un_bilan_equilibre(self, bilan_equilibre):
        report = check_balance_coherence(bilan_equilibre)

        assert report.is_balanced is True
        assert report.total_actif == 1_500_000.0
        assert report.total_passif == 1_500_000.0
        assert report.ecart == 0.0
        assert report.sens_ecart == "equilibre"

    def test_aucune_anomalie_quand_equilibre(self, bilan_equilibre):
        report = check_balance_coherence(bilan_equilibre)
        assert report.anomalies == []

    def test_totaux_par_classe(self, bilan_equilibre):
        report = check_balance_coherence(bilan_equilibre)

        # Classe 2 (immo) 1 000 000, classe 3 (stocks) 300 000,
        # classe 5 (tresorerie) 200 000, classe 1 (capital) 1 200 000,
        # classe 4 (tiers) 300 000
        assert report.totaux_par_classe == {
            "1": 1_200_000.0,
            "2": 1_000_000.0,
            "3": 300_000.0,
            "4": 300_000.0,
            "5": 200_000.0,
        }

    def test_ecart_dans_la_tolerance_reste_equilibre(self):
        """A one-franc rounding gap must not be reported as an imbalance."""
        rows = [
            {"compte": "521", "debit": 1_000_001, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 1_000_000},
        ]
        report = check_balance_coherence(rows)

        assert report.ecart == 1.0
        assert report.ecart <= TOLERANCE_XOF
        assert report.is_balanced is True

    def test_rapport_texte_quand_equilibre(self, bilan_equilibre):
        text = format_anomaly_report(check_balance_coherence(bilan_equilibre))
        assert "BILAN EQUILIBRE" in text


@pytest.mark.unit
class TestBilanDesequilibre:
    def test_detecte_le_desequilibre(self, bilan_desequilibre):
        report = check_balance_coherence(bilan_desequilibre)

        assert report.is_balanced is False
        assert report.total_actif == 1_500_000.0
        assert report.total_passif == 1_200_000.0
        assert report.ecart == 300_000.0
        assert report.sens_ecart == "actif > passif"

    def test_sens_inverse_quand_passif_superieur(self):
        rows = [
            {"compte": "521", "debit": 100_000, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 500_000},
        ]
        report = check_balance_coherence(rows)

        assert report.ecart == -400_000.0
        assert report.sens_ecart == "passif > actif"

    def test_signale_un_compte_de_sens_inverse(self):
        """A credit balance on an actif account is an inverted-sign anomaly."""
        rows = [
            {"compte": "241", "debit": 0, "credit": 50_000},  # actif, credit -> anormal
            {"compte": "101", "debit": 0, "credit": 100_000},
        ]
        report = check_balance_coherence(rows)

        assert report.is_balanced is False
        comptes = [a.compte for a in report.anomalies]
        assert "241" in comptes

        anomaly = next(a for a in report.anomalies if a.compte == "241")
        assert anomaly.classe == "2"
        assert anomaly.classe_label == "Classe 2 - Actif immobilise"
        assert anomaly.side == "actif"
        assert "sens inverse" in anomaly.motif

    def test_signale_un_compte_de_bilan_non_mappe(self):
        """Account 14 (subventions d'investissement) is still absent from
        MAPPING_RULES: it silently drops out of both totals, which is a prime
        cause of imbalance. The detector must name it."""
        rows = [
            {"compte": "241", "debit": 500_000, "credit": 0},
            {"compte": "141", "debit": 0, "credit": 200_000},  # classe 1, non mappe
            {"compte": "101", "debit": 0, "credit": 300_000},
        ]
        report = check_balance_coherence(rows)

        assert report.is_balanced is False
        anomaly = next(a for a in report.anomalies if a.compte == "141")
        assert anomaly.classe == "1"
        assert anomaly.side == "hors_bilan"
        assert "non mappe" in anomaly.motif

    def test_anomalies_triees_par_montant_decroissant(self):
        rows = [
            {"compte": "241", "debit": 0, "credit": 10_000},
            {"compte": "311", "debit": 0, "credit": 900_000},
            {"compte": "101", "debit": 0, "credit": 100_000},
        ]
        report = check_balance_coherence(rows)

        soldes = [abs(a.solde) for a in report.anomalies]
        assert soldes == sorted(soldes, reverse=True)

    def test_rapport_texte_liste_les_classes(self, bilan_desequilibre):
        text = format_anomaly_report(check_balance_coherence(bilan_desequilibre))

        assert "RAPPORT D'ANOMALIES" in text
        assert "actif > passif" in text
        assert "Classe 2 - Actif immobilise" in text
        assert "Classe 1 - Ressources durables" in text

    def test_serialisation_dict(self, bilan_desequilibre):
        payload = check_balance_coherence(bilan_desequilibre).to_dict()

        assert payload["is_balanced"] is False
        assert payload["ecart"] == 300_000.0
        assert set(payload) >= {
            "total_actif",
            "total_passif",
            "ecart",
            "sens_ecart",
            "anomalies",
            "totaux_par_classe",
        }


@pytest.mark.unit
class TestCasLimites:
    def test_balance_vide(self):
        report = check_balance_coherence([])
        assert report.is_balanced is True
        assert report.total_actif == 0.0
        assert report.total_passif == 0.0

    def test_balance_none(self):
        assert check_balance_coherence(None).is_balanced is True

    def test_ignore_les_lignes_sans_compte(self):
        rows = [
            {"compte": "", "debit": 999, "credit": 0},
            {"debit": 999, "credit": 0},
            {"compte": "521", "debit": 100, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 100},
        ]
        report = check_balance_coherence(rows)
        assert report.is_balanced is True
        assert report.total_actif == 100.0

    def test_comptes_de_gestion_exclus_du_bilan(self):
        """Classes 6 and 7 must not move the balance-sheet totals."""
        rows = [
            {"compte": "521", "debit": 100_000, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 100_000},
            {"compte": "601", "debit": 50_000, "credit": 0},  # charge
            {"compte": "701", "debit": 0, "credit": 80_000},  # produit
        ]
        report = check_balance_coherence(rows)

        assert report.is_balanced is True
        assert report.total_actif == 100_000.0
        assert report.total_passif == 100_000.0
        assert "6" not in report.totaux_par_classe
        assert "7" not in report.totaux_par_classe

    def test_tolerance_personnalisee(self):
        rows = [
            {"compte": "521", "debit": 1_000_100, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 1_000_000},
        ]
        assert check_balance_coherence(rows).is_balanced is False
        assert check_balance_coherence(rows, tolerance=200.0).is_balanced is True

    @pytest.mark.parametrize(
        "compte,classe",
        [("101", "1"), ("241", "2"), ("311", "3"), ("401", "4"), ("521", "5"), ("601", "6")],
    )
    def test_extraction_de_la_classe(self, compte, classe):
        assert get_account_class(compte) == classe


@pytest.mark.unit
class TestMappingCorrige:
    """Regression tests for the MAPPING_RULES gaps fixed on 2026-09-14."""

    def test_151_provision_is_passif(self):
        """Account 151 (provisions pour risques) is a passif resource.

        Before the fix it matched no rule, vanished from both totals and made
        an otherwise sound balance sheet look 200k short.
        """
        rows = [
            {"compte": "241", "debit": 500_000, "credit": 0},
            {"compte": "151", "debit": 0, "credit": 200_000},
            {"compte": "101", "debit": 0, "credit": 300_000},
        ]
        report = check_balance_coherence(rows)

        assert report.is_balanced is True
        assert report.ecart == 0.0
        assert report.total_actif == 500_000.0
        assert report.total_passif == 500_000.0
        assert report.anomalies == []

    def test_28_amort_reduces_actif(self):
        """Gross 1M of immobilisations minus 200k of amortissements nets 800k."""
        rows = [
            {"compte": "241", "debit": 1_000_000, "credit": 0},
            {"compte": "2841", "debit": 0, "credit": 200_000},  # amortissement
            {"compte": "101", "debit": 0, "credit": 800_000},
        ]
        report = check_balance_coherence(rows)

        assert report.total_actif == 800_000.0, "l'amortissement doit etre deduit"
        assert report.total_actif != 1_000_000.0, "le brut ne doit pas etre retenu"
        assert report.is_balanced is True

        # And the engine must present it brut / amort / net.
        statements = compute_financial_statements(rows)
        immo = statements["bilan_actif"]["Immobilisations incorporelles et corporelles"]
        assert immo["brut"] == 1_000_000.0
        assert immo["amort"] == 200_000.0
        assert immo["net"] == 800_000.0

    def test_39_depreciation_stocks_est_deduite(self):
        """Regression: 39 used to match the broad ("3",) rule and be ADDED."""
        rows = [
            {"compte": "311", "debit": 500_000, "credit": 0},
            {"compte": "391", "debit": 0, "credit": 100_000},  # depreciation
            {"compte": "101", "debit": 0, "credit": 400_000},
        ]
        report = check_balance_coherence(rows)

        assert report.total_actif == 400_000.0
        assert report.is_balanced is True

        stocks = compute_financial_statements(rows)["bilan_actif"]["Stocks"]
        assert (stocks["brut"], stocks["amort"], stocks["net"]) == (
            500_000.0, 100_000.0, 400_000.0,
        )

    @pytest.mark.parametrize(
        "compte_contra,compte_actif,categorie",
        [
            ("491", "411", "Créances et emplois assimilés"),
            ("591", "521", "Trésorerie-Actif"),
            ("291", "261", "Immobilisations financières"),
        ],
    )
    def test_depreciations_deduites(self, compte_contra, compte_actif, categorie):
        rows = [
            {"compte": compte_actif, "debit": 300_000, "credit": 0},
            {"compte": compte_contra, "debit": 0, "credit": 50_000},
            {"compte": "101", "debit": 0, "credit": 250_000},
        ]
        report = check_balance_coherence(rows)

        assert report.total_actif == 250_000.0
        assert report.is_balanced is True

        bucket = compute_financial_statements(rows)["bilan_actif"][categorie]
        assert bucket["net"] == 250_000.0

    def test_amort_avant_immobilisation_dans_la_balance(self):
        """Row order must not matter: a contra row may precede its asset."""
        rows = [
            {"compte": "2841", "debit": 0, "credit": 200_000},
            {"compte": "241", "debit": 1_000_000, "credit": 0},
            {"compte": "101", "debit": 0, "credit": 800_000},
        ]
        immo = compute_financial_statements(rows)["bilan_actif"][
            "Immobilisations incorporelles et corporelles"
        ]
        assert (immo["brut"], immo["amort"], immo["net"]) == (
            1_000_000.0, 200_000.0, 800_000.0,
        )

    def test_tiers_debiteur_va_en_actif(self):
        rows = [
            {"compte": "471", "debit": 150_000, "credit": 0},  # solde debiteur
            {"compte": "101", "debit": 0, "credit": 150_000},
        ]
        report = check_balance_coherence(rows)

        assert report.total_actif == 150_000.0
        assert report.total_passif == 150_000.0
        assert report.is_balanced is True

    def test_tiers_crediteur_va_en_passif(self):
        rows = [
            {"compte": "471", "debit": 0, "credit": 150_000},  # solde crediteur
            {"compte": "521", "debit": 150_000, "credit": 0},
        ]
        report = check_balance_coherence(rows)

        assert report.total_actif == 150_000.0
        assert report.total_passif == 150_000.0
        assert report.is_balanced is True

    @pytest.mark.parametrize(
        "prefixe,type_attendu",
        [
            ("151", "bilan_passif"), ("181", "bilan_passif"), ("191", "bilan_passif"),
            ("251", "bilan_actif"), ("551", "bilan_actif"), ("571", "bilan_actif"),
            ("581", "bilan_actif"),
        ],
    )
    def test_prefixes_manquants_desormais_mappes(self, prefixe, type_attendu):
        assert get_category_for_account(prefixe)["type"] == type_attendu

    @pytest.mark.parametrize("compte", ["281", "291", "391", "491", "591"])
    def test_comptes_contra_marques(self, compte):
        assert get_category_for_account(compte)["contra"] is True

    def test_sens_inverse_sur_un_compte_damortissement(self):
        """A debit balance on a 28 account is itself an anomaly."""
        rows = [
            {"compte": "2841", "debit": 50_000, "credit": 0},  # sens inverse
            {"compte": "101", "debit": 0, "credit": 10_000},
        ]
        report = check_balance_coherence(rows)

        assert report.is_balanced is False
        anomaly = next(a for a in report.anomalies if a.compte == "2841")
        assert "sens inverse" in anomaly.motif
