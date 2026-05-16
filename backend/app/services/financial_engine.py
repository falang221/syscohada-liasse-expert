from typing import List, Dict
from app.core.syscohada_rules import get_category_for_account

def compute_financial_statements(parsed_balance: List[Dict]) -> Dict:
    """
    Processes a list of raw accounts (parsed balance) and aggregates them
    into SYSCOHADA reporting categories.
    """
    statements = {
        "bilan_actif": {},
        "bilan_passif": {},
        "resultat_charge": {},
        "resultat_produit": {},
        "unknown": {}
    }
    
    for row in parsed_balance:
        # Robustly extract account and values, handling varying Excel column names
        compte = str(row.get("compte") or row.get("Compte") or row.get("Account") or "")
        
        # Determine the net balance for the account
        debit = float(row.get("débit") or row.get("Debit") or row.get("debit") or 0.0)
        credit = float(row.get("crédit") or row.get("Credit") or row.get("credit") or 0.0)
        solde_debit = float(row.get("solde_debit") or 0.0)
        solde_credit = float(row.get("solde_credit") or 0.0)
        
        # Calculate net if explicit soldes are missing
        if solde_debit == 0 and solde_credit == 0:
            net = debit - credit
            if net > 0:
                solde_debit = net
            else:
                solde_credit = abs(net)
                
        # Get mapping rules
        mapping = get_category_for_account(compte)
        cat_type = mapping["type"]
        cat_name = mapping["category"]
        
        # Initialize category if not exists
        if cat_name not in statements[cat_type]:
            statements[cat_type][cat_name] = {"brut": 0.0, "net": 0.0}
            
        # Add to category
        # Actif & Charges normally have debit balances
        if cat_type in ["bilan_actif", "resultat_charge"]:
            value = solde_debit - solde_credit
            statements[cat_type][cat_name]["brut"] += value
            statements[cat_type][cat_name]["net"] += value
            
        # Passif & Produits normally have credit balances
        elif cat_type in ["bilan_passif", "resultat_produit"]:
            value = solde_credit - solde_debit
            statements[cat_type][cat_name]["brut"] += value
            statements[cat_type][cat_name]["net"] += value
            
        else:
            # Handle unclassified
            if cat_name not in statements["unknown"]:
                statements["unknown"][cat_name] = {"brut": 0.0, "net": 0.0}
            statements["unknown"][cat_name]["brut"] += (solde_debit - solde_credit)
            statements["unknown"][cat_name]["net"] += (solde_debit - solde_credit)
            
    return statements
