import logging
from typing import List, Dict, Optional

from app.core.coherence import check_balance_coherence
from app.core.syscohada_rules import get_category_for_account, resolve_tiers_side
from app.services.tafire_engine import compute_tafire

logger = logging.getLogger(__name__)

def _ensure_bucket(res: Dict, cat_type: str, cat_name: str, cat_code: str) -> Dict:
    """Return the accumulator for a category, creating it when needed."""
    if cat_name not in res[cat_type]:
        res[cat_type][cat_name] = {"brut": 0.0, "amort": 0.0, "net": 0.0, "code": cat_code}
    return res[cat_type][cat_name]


def _aggregate_balance(parsed_balance: List[Dict]) -> Dict:
    """Aggregate a parsed trial balance into SYSCOHADA statement buckets.

    Actif categories are presented brut / amort / net. Contra accounts
    (28, 29, 39, 49, 59) feed `amort`; `net` is computed as brut - amort in a
    final pass, so a depreciation row may appear before the asset it reduces.
    """
    res = { "bilan_actif": {}, "bilan_passif": {}, "resultat_charge": {}, "resultat_produit": {}, "unknown": {} }
    if not parsed_balance:
        return res

    for row in parsed_balance:
        compte = str(row.get("compte", "")).strip()
        if not compte:
            continue
        debit = float(row.get("debit", 0.0) or 0.0)
        credit = float(row.get("credit", 0.0) or 0.0)

        # In a trial balance the debit-side balance is debit - credit.
        solde_debiteur = debit - credit

        mapping = resolve_tiers_side(get_category_for_account(compte), solde_debiteur)
        cat_type = mapping["type"]
        cat_name = mapping["category"]
        cat_code = mapping["code"]

        # Contra accounts: amortissements and depreciations. Their natural
        # balance is credit; they reduce the gross value of another category.
        if mapping.get("contra"):
            target = mapping.get("reduces", cat_name)
            bucket = _ensure_bucket(res, "bilan_actif", target, cat_code)
            bucket["amort"] += credit - debit
            continue

        if cat_type in ("bilan_actif", "resultat_charge"):
            # Normal balance is debit.
            _ensure_bucket(res, cat_type, cat_name, cat_code)["brut"] += solde_debiteur
        elif cat_type in ("bilan_passif", "resultat_produit"):
            # Normal balance is credit.
            _ensure_bucket(res, cat_type, cat_name, cat_code)["brut"] += credit - debit
        else:
            _ensure_bucket(res, "unknown", cat_name, "XX")["brut"] += solde_debiteur

    # Final pass: net = brut - amort. Only actif carries an amort column.
    for cat_type, buckets in res.items():
        for bucket in buckets.values():
            bucket["net"] = bucket["brut"] - bucket["amort"]

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

    # SYSCOHADA invariant: Total Actif == Total Passif, checked on the raw
    # trial balance so unmapped accounts are still visible as anomalies.
    statements["coherence"] = check_balance_coherence(parsed_balance_n).to_dict()

    actif_total_n = sum(c['net'] for c in statements['bilan_actif'].values())
    actif_total_n_1 = sum(c['net_n_1'] for c in statements['bilan_actif'].values())
    logger.debug(
        "N-1 engine complete. Actif total N: %s, N-1: %s, bilan equilibre: %s",
        actif_total_n, actif_total_n_1, statements["coherence"]["is_balanced"],
    )

    return statements
