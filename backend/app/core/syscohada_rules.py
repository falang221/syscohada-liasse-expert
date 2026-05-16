# SYSCOHADA Revised - Simplified Mapping Rules for MVP
# Maps account prefixes to major reporting categories

MAPPING_RULES = [
    # --- BILAN: ACTIF ---
    {"prefix": ("2",), "category": "Actif Immobilisé", "type": "bilan_actif"},
    {"prefix": ("3", "41"), "category": "Actif Circulant", "type": "bilan_actif"},
    {"prefix": ("52", "53", "54"), "category": "Trésorerie Actif", "type": "bilan_actif"},
    
    # --- BILAN: PASSIF ---
    {"prefix": ("10", "11", "12", "13", "14", "15"), "category": "Capitaux Propres", "type": "bilan_passif"},
    {"prefix": ("16", "17"), "category": "Dettes Financières", "type": "bilan_passif"},
    {"prefix": ("40", "42", "43", "44"), "category": "Passif Circulant", "type": "bilan_passif"},
    {"prefix": ("56",), "category": "Trésorerie Passif", "type": "bilan_passif"},
    
    # --- COMPTE DE RÉSULTAT: CHARGES ---
    {"prefix": ("60", "61", "62", "63", "64", "65"), "category": "Charges d'Exploitation", "type": "resultat_charge"},
    {"prefix": ("66",), "category": "Charges Financières", "type": "resultat_charge"},
    {"prefix": ("67", "68"), "category": "Charges Hors Activité Ordinaire (HAO) & Dotations", "type": "resultat_charge"},
    
    # --- COMPTE DE RÉSULTAT: PRODUITS ---
    {"prefix": ("70", "71", "72", "73", "74", "75"), "category": "Produits d'Exploitation", "type": "resultat_produit"},
    {"prefix": ("77",), "category": "Produits Financiers", "type": "resultat_produit"},
    {"prefix": ("78", "79"), "category": "Produits Hors Activité Ordinaire (HAO) & Reprises", "type": "resultat_produit"},
]

def get_category_for_account(account_number: str) -> dict:
    """Returns the matching category dict for a given account number, or None if not found."""
    acc_str = str(account_number).strip()
    for rule in MAPPING_RULES:
        if acc_str.startswith(rule["prefix"]):
            return rule
    return {"category": "Non Classé / Attente", "type": "unknown"}
