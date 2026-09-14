# SYSCOHADA Revised - Mapping Rules with DGID Codes
#
# Rule resolution is FIRST MATCH WINS, so ordering matters:
# specific prefixes must come before the broader ones they would otherwise
# be swallowed by (e.g. "39" before "3", "28"/"29" before "21"-"24").
#
# Optional keys:
#   contra   True  -> the account is a deduction (amortissement / depreciation).
#                     Its balance feeds the `amort` column, never `brut`.
#   reduces  str   -> category name whose `brut` this contra account reduces.
#   sign_based True -> side (actif/passif) is decided by the account's balance
#                     sign rather than statically (class 4 tiers accounts).

MAPPING_RULES = [
    # --- CONTRA ACCOUNTS (amortissements et depreciations) ---
    # Listed first: "39" would otherwise match the broad ("3",) stocks rule,
    # and be ADDED to the actif instead of deducted from it.
    {"prefix": ("28",), "category": "Immobilisations incorporelles et corporelles",
     "type": "bilan_actif", "code": "AE", "contra": True,
     "reduces": "Immobilisations incorporelles et corporelles"},
    {"prefix": ("29",), "category": "Immobilisations financières",
     "type": "bilan_actif", "code": "AF", "contra": True,
     "reduces": "Immobilisations financières"},
    {"prefix": ("39",), "category": "Stocks",
     "type": "bilan_actif", "code": "AQ", "contra": True,
     "reduces": "Stocks"},
    {"prefix": ("49",), "category": "Créances et emplois assimilés",
     "type": "bilan_actif", "code": "BA", "contra": True,
     "reduces": "Créances et emplois assimilés"},
    {"prefix": ("59",), "category": "Trésorerie-Actif",
     "type": "bilan_actif", "code": "BQ", "contra": True,
     "reduces": "Trésorerie-Actif"},

    # --- BILAN: ACTIF ---
    {"prefix": ("20",), "category": "Charges immobilisées", "type": "bilan_actif", "code": "AD"},
    {"prefix": ("21", "22", "23", "24"), "category": "Immobilisations incorporelles et corporelles", "type": "bilan_actif", "code": "AE"},
    {"prefix": ("25",), "category": "Avances et acomptes sur immobilisations", "type": "bilan_actif", "code": "AN"},
    {"prefix": ("26", "27"), "category": "Immobilisations financières", "type": "bilan_actif", "code": "AF"},
    {"prefix": ("3",), "category": "Stocks", "type": "bilan_actif", "code": "AQ"},
    {"prefix": ("41",), "category": "Créances et emplois assimilés", "type": "bilan_actif", "code": "BA"},
    {"prefix": ("52", "53", "54", "55", "57", "58"), "category": "Trésorerie-Actif", "type": "bilan_actif", "code": "BQ"},

    # --- BILAN: TIERS (side decided by balance sign) ---
    # Classes 45-48 can settle either way: 4xx debiteur -> actif (creance),
    # 4xx crediteur -> passif (dette).
    {"prefix": ("45", "46", "47", "48"), "category": "Comptes de tiers divers",
     "type": "bilan_tiers", "code": "BJ", "sign_based": True,
     "category_actif": "Autres créances", "code_actif": "BJ",
     "category_passif": "Autres dettes", "code_passif": "DJ"},

    # --- BILAN: PASSIF ---
    {"prefix": ("10", "11", "12"), "category": "Capital, Réserves et Primes", "type": "bilan_passif", "code": "CA"},
    {"prefix": ("13",), "category": "Résultat net de l'exercice", "type": "bilan_passif", "code": "CB"},
    {"prefix": ("15", "19"), "category": "Provisions pour risques et charges", "type": "bilan_passif", "code": "DP"},
    {"prefix": ("18",), "category": "Dettes liées aux participations", "type": "bilan_passif", "code": "DD"},
    {"prefix": ("16", "17"), "category": "Dettes financières", "type": "bilan_passif", "code": "DA"},
    {"prefix": ("40", "42", "43", "44"), "category": "Passif Circulant", "type": "bilan_passif", "code": "DB"},
    {"prefix": ("56",), "category": "Trésorerie-Passif", "type": "bilan_passif", "code": "DQ"},

    # --- COMPTE DE RÉSULTAT ---
    {"prefix": ("70",), "category": "Chiffre d'affaires", "type": "resultat_produit", "code": "TA"},
    {"prefix": ("60",), "category": "Achats de marchandises", "type": "resultat_charge", "code": "RA"},
]

_UNKNOWN = {"category": "Autres", "type": "unknown", "code": "XX"}


def get_category_for_account(account_number: str) -> dict:
    """Returns the matching category dict for a given account number.

    Falls back to an 'unknown' descriptor when no rule matches. The returned
    dict always carries the `contra` and `sign_based` keys so callers never
    need to probe for them.
    """
    acc_str = str(account_number).strip()
    for rule in MAPPING_RULES:
        if acc_str.startswith(rule["prefix"]):
            return {**_UNKNOWN, **rule,
                    "contra": rule.get("contra", False),
                    "sign_based": rule.get("sign_based", False)}
    return {**_UNKNOWN, "contra": False, "sign_based": False}


def resolve_tiers_side(mapping: dict, solde_debiteur: float) -> dict:
    """Resolve a sign-based tiers rule into a concrete actif/passif mapping.

    Args:
        mapping: a rule dict from :func:`get_category_for_account`.
        solde_debiteur: debit minus credit for the account.

    Returns:
        A mapping dict whose `type`, `category` and `code` are settled.
        Non sign-based mappings are returned untouched.
    """
    if not mapping.get("sign_based"):
        return mapping

    if solde_debiteur >= 0:
        return {**mapping, "type": "bilan_actif",
                "category": mapping["category_actif"], "code": mapping["code_actif"]}
    return {**mapping, "type": "bilan_passif",
            "category": mapping["category_passif"], "code": mapping["code_passif"]}
