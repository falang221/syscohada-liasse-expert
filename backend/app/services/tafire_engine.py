def compute_tafire(statements: dict) -> dict:
    """
    Computes the TAFIRE (Cash Flow Statement) based on the variations 
    between balance sheet items of year N and year N-1.
    """
    flows = {
        "activite": 0.0,
        "investissement": 0.0,
        "financement": 0.0,
        "variation_tresorerie": 0.0,
        "coherence_check": False
    }

    # Helper function to get variation (Increase = positive, Decrease = negative)
    def get_var(section, key):
        data = statements.get(section, {}).get(key, {})
        return data.get("net", 0.0) - data.get("net_n_1", 0.0)

    # 1. Operating Activities (Flux d'activité)
    # Requirement: Résultat Net + variations in inventories (cl. 3), receivables (cl. 41), payables (cl. 40)
    # Note: Increase in Assets = Cash Outflow (-), Increase in Liabilities = Cash Inflow (+)
    
    profit_n = statements.get("bilan_passif", {}).get("Résultat net de l'exercice", {}).get("net", 0.0)
    
    # Variations (Increase in Asset is a negative flow for cash)
    var_stocks = get_var("bilan_actif", "Stocks")
    var_creances = get_var("bilan_actif", "Créances et emplois assimilés")
    
    # Variations (Increase in Liability is a positive flow for cash)
    var_passif_circulant = get_var("bilan_passif", "Passif Circulant")
    
    flows["activite"] = profit_n - var_stocks - var_creances + var_passif_circulant

    # 2. Investing Activities (Flux d'investissement)
    # Requirement: Variations in Fixed Assets (cl. 2)
    # Accounts: Charges immobilisées, Immobilisations incorporelles et corporelles, Immobilisations financières
    
    var_charges_immo = get_var("bilan_actif", "Charges immobilisées")
    var_immo_corp_incorp = get_var("bilan_actif", "Immobilisations incorporelles et corporelles")
    var_immo_fin = get_var("bilan_actif", "Immobilisations financières")
    
    # Increase in Fixed Assets = Cash Outflow
    flows["investissement"] = - (var_charges_immo + var_immo_corp_incorp + var_immo_fin)

    # 3. Financing Activities (Flux de financement)
    # Requirement: Variations in Equity (cl. 10-15) and Financial Debts (cl. 16-17)
    
    var_capitaux = get_var("bilan_passif", "Capital, Réserves et Primes")
    var_dettes_fin = get_var("bilan_passif", "Dettes financières")
    
    # Increase in Equity/Debt = Cash Inflow
    flows["financement"] = var_capitaux + var_dettes_fin

    # 4. Total Cash Flow
    flows["variation_tresorerie"] = flows["activite"] + flows["investissement"] + flows["financement"]

    # 5. Coherence Check
    # Requirement: Total Net Flow = Change in Cash at Bank (cl. 52-54)
    # Cash Net = (Trésorerie-Actif) - (Trésorerie-Passif)
    
    treso_a_n = statements.get("bilan_actif", {}).get("Trésorerie-Actif", {}).get("net", 0.0)
    treso_a_n_1 = statements.get("bilan_actif", {}).get("Trésorerie-Actif", {}).get("net_n_1", 0.0)
    
    treso_p_n = statements.get("bilan_passif", {}).get("Trésorerie-Passif", {}).get("net", 0.0)
    treso_p_n_1 = statements.get("bilan_passif", {}).get("Trésorerie-Passif", {}).get("net_n_1", 0.0)
    
    cash_net_n = treso_a_n - treso_p_n
    cash_net_n_1 = treso_a_n_1 - treso_p_n_1
    
    actual_cash_var = cash_net_n - cash_net_n_1
    
    # We allow a small rounding difference
    if abs(flows["variation_tresorerie"] - actual_cash_var) < 0.01:
        flows["coherence_check"] = True
    
    return flows
