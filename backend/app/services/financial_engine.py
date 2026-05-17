from typing import List, Dict, Optional
from app.core.syscohada_rules import get_category_for_account
from app.services.tafire_engine import compute_tafire

def _aggregate_balance(parsed_balance: List[Dict]) -> Dict:
    """Helper to aggregate a single balance sheet."""
    res = { "bilan_actif": {}, "bilan_passif": {}, "resultat_charge": {}, "resultat_produit": {}, "unknown": {} }
    if not parsed_balance:
        return res
        
    for row in parsed_balance:
        compte = str(row.get("compte", ""))
        debit = float(row.get("debit", 0.0))
        credit = float(row.get("credit", 0.0))
        
        # Calculate net balance for the year
        # In a trial balance: Debit - Credit
        net_balance = debit - credit
        
        mapping = get_category_for_account(compte)
        cat_type = mapping["type"]
        cat_name = mapping["category"]
        cat_code = mapping["code"]
        
        if cat_name not in res[cat_type]:
            res[cat_type][cat_name] = {"brut": 0.0, "amort": 0.0, "net": 0.0, "code": cat_code}
            
        if cat_type in ["bilan_actif", "resultat_charge"]:
            # Normal balance is Debit
            res[cat_type][cat_name]["brut"] += net_balance
            res[cat_type][cat_name]["net"] += net_balance
        elif cat_type in ["bilan_passif", "resultat_produit"]:
            # Normal balance is Credit (so we take Credit - Debit)
            val = credit - debit
            res[cat_type][cat_name]["brut"] += val
            res[cat_type][cat_name]["net"] += val
        else:
            # Handle unclassified
            if cat_name not in res["unknown"]:
                res["unknown"][cat_name] = {"brut": 0.0, "amort": 0.0, "net": 0.0, "code": "XX"}
            res["unknown"][cat_name]["brut"] += net_balance
            res["unknown"][cat_name]["net"] += net_balance
    return res

def compute_financial_statements(parsed_balance_n: List[Dict], parsed_balance_n_1: Optional[List[Dict]] = None) -> Dict:
    """
    Processes both N and N-1 balances and merges them into a single structure.
    """
    agg_n = _aggregate_balance(parsed_balance_n)
    agg_n_1 = _aggregate_balance(parsed_balance_n_1) if parsed_balance_n_1 else {}
    
    statements = { "bilan_actif": {}, "bilan_passif": {}, "resultat_charge": {}, "resultat_produit": {}, "unknown": {} }
    
    # Merge all possible categories across all types
    for cat_type in statements.keys():
        all_cats = set(list(agg_n.get(cat_type, {}).keys()) + list(agg_n_1.get(cat_type, {}).keys()))
        for cat_name in all_cats:
            data_n = agg_n.get(cat_type, {}).get(cat_name, {"brut": 0.0, "amort": 0.0, "net": 0.0, "code": "XX"})
            data_n_1 = agg_n_1.get(cat_type, {}).get(cat_name, {"net": 0.0})
            
            statements[cat_type][cat_name] = {
                "brut": data_n["brut"],
                "amort": data_n["amort"],
                "net": data_n["net"],
                "net_n_1": data_n_1["net"],
                "code": data_n.get("code", "XX") if data_n.get("code") != "XX" else agg_n_1.get(cat_type, {}).get(cat_name, {}).get("code", "XX")
            }
            
    # Compute TAFIRE
    statements["tafire"] = compute_tafire(statements)
    
    # Debug info
    actif_total_n = sum(c['net'] for c in statements['bilan_actif'].values())
    actif_total_n_1 = sum(c['net_n_1'] for c in statements['bilan_actif'].values())
    print(f"DEBUG: N-1 Engine complete. Actif Total N: {actif_total_n}, N-1: {actif_total_n_1}")
    
    return statements
