import pytest
from app.services.financial_engine import compute_financial_statements

def test_compute_financial_statements_with_tafire():
    # Mock data for parsed balance N
    parsed_n = [
        {"compte": "131", "debit": 0, "credit": 50},  # Résultat net (Credit)
        {"compte": "311", "debit": 100, "credit": 0}, # Stocks (Debit)
        {"compte": "521", "debit": 50, "credit": 0},  # Trésorerie-Actif (Debit)
    ]
    
    # Mock data for parsed balance N-1
    parsed_n_1 = [
        {"compte": "311", "debit": 80, "credit": 0},  # Stocks N-1
        {"compte": "521", "debit": 20, "credit": 0},  # Trésorerie-Actif N-1
    ]
    
    statements = compute_financial_statements(parsed_n, parsed_n_1)
    
    assert "tafire" in statements
    tafire = statements["tafire"]
    
    # Activité: 50 (Resultat) - 20 (Var Stocks: 100-80) = 30
    assert tafire["activite"] == 30.0
    
    # Var Cash = 50 - 20 = 30
    assert tafire["variation_tresorerie"] == 30.0
    assert tafire["coherence_check"] is True
