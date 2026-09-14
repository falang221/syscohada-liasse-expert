"""SYSCOHADA balance-sheet coherence checks.

Core invariant of the revised SYSCOHADA framework: a balance sheet must satisfy
Total Actif == Total Passif. When it does not, the imbalance is traced back to
the account classes that could have caused it (classes 1-5).

Account classes (SYSCOHADA revised):
    1  Comptes de ressources durables          -> passif
    2  Comptes d'actif immobilise              -> actif
    3  Comptes de stocks                       -> actif
    4  Comptes de tiers                        -> actif (4xx debit) or passif (4xx credit)
    5  Comptes de tresorerie                   -> actif (52-54) or passif (56)
    6  Charges                                 -> compte de resultat, not the balance sheet
    7  Produits                                -> compte de resultat, not the balance sheet
    8  Comptes des autres charges et produits  -> compte de resultat
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

from app.core.syscohada_rules import get_category_for_account, resolve_tiers_side

# Monetary tolerance in XOF. SYSCOHADA statements are presented in whole francs,
# so anything at or below one franc is a rounding artefact, not an imbalance.
TOLERANCE_XOF: float = 1.0

Side = Literal["actif", "passif", "hors_bilan"]

CLASS_LABELS: Dict[str, str] = {
    "1": "Classe 1 - Ressources durables",
    "2": "Classe 2 - Actif immobilise",
    "3": "Classe 3 - Stocks",
    "4": "Classe 4 - Tiers",
    "5": "Classe 5 - Tresorerie",
    "6": "Classe 6 - Charges",
    "7": "Classe 7 - Produits",
    "8": "Classe 8 - Autres charges et produits",
}

# Classes that belong on the balance sheet at all.
BALANCE_SHEET_CLASSES: tuple[str, ...] = ("1", "2", "3", "4", "5")


@dataclass(frozen=True)
class AccountAnomaly:
    """One account implicated in a balance-sheet imbalance."""

    compte: str
    classe: str
    classe_label: str
    side: Side
    category: str
    code_dgid: str
    debit: float
    credit: float
    solde: float
    motif: str


@dataclass(frozen=True)
class CoherenceReport:
    """Result of the Total Actif == Total Passif check."""

    is_balanced: bool
    total_actif: float
    total_passif: float
    ecart: float
    tolerance: float = TOLERANCE_XOF
    anomalies: List[AccountAnomaly] = field(default_factory=list)
    totaux_par_classe: Dict[str, float] = field(default_factory=dict)

    @property
    def sens_ecart(self) -> str:
        """Human-readable direction of the imbalance."""
        if self.is_balanced:
            return "equilibre"
        return "actif > passif" if self.ecart > 0 else "passif > actif"

    def to_dict(self) -> Dict:
        return {
            "is_balanced": self.is_balanced,
            "total_actif": self.total_actif,
            "total_passif": self.total_passif,
            "ecart": self.ecart,
            "sens_ecart": self.sens_ecart,
            "tolerance": self.tolerance,
            "totaux_par_classe": self.totaux_par_classe,
            "anomalies": [
                {
                    "compte": a.compte,
                    "classe": a.classe,
                    "classe_label": a.classe_label,
                    "side": a.side,
                    "category": a.category,
                    "code_dgid": a.code_dgid,
                    "debit": a.debit,
                    "credit": a.credit,
                    "solde": a.solde,
                    "motif": a.motif,
                }
                for a in self.anomalies
            ],
        }


def get_account_class(compte: str) -> str:
    """Return the SYSCOHADA class (first digit) of an account number."""
    acc = str(compte).strip()
    return acc[0] if acc else ""


def _resolve(compte: str, solde_debiteur: float) -> Dict:
    """Return the settled mapping for an account, tiers side included."""
    return resolve_tiers_side(get_category_for_account(compte), solde_debiteur)


def _side_for(compte: str, solde_debiteur: float = 0.0) -> Side:
    """Map an account to the balance-sheet side it contributes to."""
    mapping = _resolve(compte, solde_debiteur)
    if mapping["type"] == "bilan_actif":
        return "actif"
    if mapping["type"] == "bilan_passif":
        return "passif"
    return "hors_bilan"


def check_balance_coherence(
    parsed_balance: List[Dict],
    tolerance: float = TOLERANCE_XOF,
) -> CoherenceReport:
    """Verify Total Actif == Total Passif on a parsed trial balance.

    Args:
        parsed_balance: rows of ``{"compte": str, "debit": float, "credit": float}``.
        tolerance: maximum absolute gap, in XOF, still considered balanced.

    Returns:
        A :class:`CoherenceReport`. When the sheet is unbalanced, ``anomalies``
        lists the class 1-5 accounts that plausibly caused the gap, ordered by
        decreasing absolute balance so the largest suspect comes first.
    """
    total_actif = 0.0
    total_passif = 0.0
    totaux_par_classe: Dict[str, float] = {}
    candidates: List[AccountAnomaly] = []

    for row in parsed_balance or []:
        compte = str(row.get("compte", "")).strip()
        if not compte:
            continue

        debit = float(row.get("debit", 0.0) or 0.0)
        credit = float(row.get("credit", 0.0) or 0.0)
        classe = get_account_class(compte)
        mapping = _resolve(compte, debit - credit)
        side = _side_for(compte, debit - credit)
        is_contra = mapping.get("contra", False)

        # Actif accounts carry a debit balance, passif accounts a credit
        # balance. Contra accounts (amortissements, depreciations) sit on the
        # actif side but carry a credit balance and are DEDUCTED from it.
        if is_contra:
            solde = credit - debit
            total_actif -= solde
            contribution = -solde
        elif side == "actif":
            solde = debit - credit
            total_actif += solde
            contribution = solde
        elif side == "passif":
            solde = credit - debit
            total_passif += solde
            contribution = solde
        else:
            solde = debit - credit
            contribution = solde

        if classe in BALANCE_SHEET_CLASSES:
            totaux_par_classe[classe] = totaux_par_classe.get(classe, 0.0) + contribution

        motif = _diagnose(compte, classe, side, solde, mapping["type"], is_contra)
        if motif:
            candidates.append(
                AccountAnomaly(
                    compte=compte,
                    classe=classe,
                    classe_label=CLASS_LABELS.get(classe, f"Classe {classe} - inconnue"),
                    side=side,
                    category=mapping["category"],
                    code_dgid=mapping["code"],
                    debit=debit,
                    credit=credit,
                    solde=solde,
                    motif=motif,
                )
            )

    ecart = round(total_actif - total_passif, 2)
    is_balanced = abs(ecart) <= tolerance

    anomalies = (
        sorted(candidates, key=lambda a: abs(a.solde), reverse=True)
        if not is_balanced
        else []
    )

    return CoherenceReport(
        is_balanced=is_balanced,
        total_actif=round(total_actif, 2),
        total_passif=round(total_passif, 2),
        ecart=ecart,
        tolerance=tolerance,
        anomalies=anomalies,
        totaux_par_classe={k: round(v, 2) for k, v in sorted(totaux_par_classe.items())},
    )


def _diagnose(
    compte: str,
    classe: str,
    side: Side,
    solde: float,
    cat_type: str,
    is_contra: bool = False,
) -> str:
    """Return why an account is suspect, or an empty string when it is not.

    Only class 1-5 accounts can unbalance a balance sheet, so classes 6-8 are
    reported solely when they leak into the bilan, which would itself be a bug.
    """
    if is_contra:
        # A contra account's natural balance is credit, i.e. solde >= 0 here.
        if solde < 0:
            return (
                f"Solde debiteur anormal pour un compte d'amortissement ou de "
                f"depreciation (classe {classe}) - sens inverse probable"
            )
        return ""

    if classe not in BALANCE_SHEET_CLASSES:
        if side in ("actif", "passif"):
            return (
                f"Compte de gestion (classe {classe}) mappe sur le bilan "
                f"({side}) - anomalie de mapping"
            )
        return ""

    if cat_type == "unknown":
        return (
            f"Compte de bilan non mappe (classe {classe}) - exclu des totaux, "
            "cause probable de l'ecart"
        )

    # A negative balance on its natural side means the account is inverted.
    if solde < 0:
        sens = "debiteur" if side == "passif" else "crediteur"
        return (
            f"Solde {sens} anormal pour un compte d'{side} "
            f"(classe {classe}) - sens inverse probable"
        )

    return ""


def format_anomaly_report(report: CoherenceReport) -> str:
    """Render a coherence report as plain text for logs or PDF annexes."""
    if report.is_balanced:
        return (
            f"BILAN EQUILIBRE - Total Actif = Total Passif = "
            f"{report.total_actif:,.2f} XOF (tolerance {report.tolerance:,.2f})"
        )

    lines = [
        "RAPPORT D'ANOMALIES - INCOHERENCE DU BILAN SYSCOHADA",
        "=" * 60,
        f"Total Actif   : {report.total_actif:>18,.2f} XOF",
        f"Total Passif  : {report.total_passif:>18,.2f} XOF",
        f"Ecart         : {report.ecart:>18,.2f} XOF ({report.sens_ecart})",
        f"Tolerance     : {report.tolerance:>18,.2f} XOF",
        "",
        "Totaux par classe SYSCOHADA :",
    ]
    for classe, total in report.totaux_par_classe.items():
        lines.append(f"  {CLASS_LABELS.get(classe, classe):<42} {total:>18,.2f}")

    if report.anomalies:
        lines += ["", f"Comptes suspects ({len(report.anomalies)}) :"]
        for a in report.anomalies:
            lines.append(
                f"  [{a.compte:<8}] {a.classe_label:<38} "
                f"solde {a.solde:>14,.2f} | {a.code_dgid} | {a.motif}"
            )
    else:
        lines += [
            "",
            "Aucun compte individuellement suspect : l'ecart provient probablement",
            "d'une ecriture manquante ou d'un compte absent de la balance.",
        ]

    return "\n".join(lines)
