# SYSCOHADA Revised - Mapping Rules with DGID Codes

MAPPING_RULES = [
    # --- BILAN: ACTIF ---
    {"prefix": ("20",), "category": "Charges immobilisées", "type": "bilan_actif", "code": "AD"},
    {"prefix": ("21", "22", "23", "24"), "category": "Immobilisations incorporelles et corporelles", "type": "bilan_actif", "code": "AE"},
    {"prefix": ("26", "27"), "category": "Immobilisations financières", "type": "bilan_actif", "code": "AF"},
    {"prefix": ("3",), "category": "Stocks", "type": "bilan_actif", "code": "AQ"},
    {"prefix": ("41",), "category": "Créances et emplois assimilés", "type": "bilan_actif", "code": "BA"},
    {"prefix": ("52", "53", "54"), "category": "Trésorerie-Actif", "type": "bilan_actif", "code": "BQ"},
    
    # --- BILAN: PASSIF ---
    {"prefix": ("10", "11", "12"), "category": "Capital, Réserves et Primes", "type": "bilan_passif", "code": "CA"},
    {"prefix": ("13",), "category": "Résultat net de l'exercice", "type": "bilan_passif", "code": "CB"},
    {"prefix": ("16", "17"), "category": "Dettes financières", "type": "bilan_passif", "code": "DA"},
    {"prefix": ("40", "42", "43", "44"), "category": "Passif Circulant", "type": "bilan_passif", "code": "DB"},
    {"prefix": ("56",), "category": "Trésorerie-Passif", "type": "bilan_passif", "code": "DQ"},
    
    # --- COMPTE DE RÉSULTAT ---
    {"prefix": ("70",), "category": "Chiffre d'affaires", "type": "resultat_produit", "code": "TA"},
    {"prefix": ("60",), "category": "Achats de marchandises", "type": "resultat_charge", "code": "RA"},
]

def get_category_for_account(account_number: str) -> dict:
    """Returns the matching category dict for a given account number, or None if not found."""
    acc_str = str(account_number).strip()
    for rule in MAPPING_RULES:
        if acc_str.startswith(rule["prefix"]):
            return rule
    return {"category": "Autres", "type": "unknown", "code": "XX"}
