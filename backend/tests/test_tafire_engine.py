import pytest
from app.services.tafire_engine import compute_tafire

def test_compute_tafire_balanced():
    # Bilan N-1 (Resultat N-1 = 0 for simplicity in this baseline)
    # Actif: Stocks 80 + Créances 60 + Immo 400 + TrésoA 100 = 640
    # Passif: Capital 350 + Résultat 0 + DettesF 140 + PassifC 130 + TrésoP 20 = 640
    
    # Bilan N:
    # Actif: Stocks 100 (+20) + Créances 50 (-10) + Immo 500 (+100) + TrésoA 130 (+30) = 780
    # Passif: Capital 400 (+50) + Résultat 50 (+50) + DettesF 200 (+60) + PassifC 110 (-20) + TrésoP 20 (0) = 780
    
    statements = {
        "bilan_actif": {
            "Stocks": {"net": 100, "net_n_1": 80},
            "Créances et emplois assimilés": {"net": 50, "net_n_1": 60},
            "Immobilisations incorporelles et corporelles": {"net": 500, "net_n_1": 400},
            "Charges immobilisées": {"net": 0, "net_n_1": 0},
            "Immobilisations financières": {"net": 0, "net_n_1": 0},
            "Trésorerie-Actif": {"net": 130, "net_n_1": 100},
        },
        "bilan_passif": {
            "Capital, Réserves et Primes": {"net": 400, "net_n_1": 350},
            "Résultat net de l'exercice": {"net": 50, "net_n_1": 0},
            "Dettes financières": {"net": 200, "net_n_1": 140},
            "Passif Circulant": {"net": 110, "net_n_1": 130},
            "Trésorerie-Passif": {"net": 20, "net_n_1": 20},
        }
    }
    
    result = compute_tafire(statements)
    
    # Activité: 50 (Résultat) - 20 (Stocks) + 10 (Créances) - 20 (PassifC) = 20
    assert result["activite"] == 20.0
    
    # Investissement: -100 (Immo)
    assert result["investissement"] == -100.0
    
    # Financement: 50 (Capital) + 60 (DettesF) = 110
    assert result["financement"] == 110.0
    
    # Total Flux: 20 - 100 + 110 = 30
    assert result["variation_tresorerie"] == 30.0
    
    # Coherence check:
    # Var Cash = (130 - 20) - (100 - 20) = 110 - 80 = 30. Matches!
    assert result["coherence_check"] is True

def test_compute_tafire_graceful_missing_n_1():
    statements = {
        "bilan_actif": {
            "Stocks": {"net": 100, "net_n_1": 0},
            "Trésorerie-Actif": {"net": 50, "net_n_1": 0},
        },
        "bilan_passif": {
            "Résultat net de l'exercice": {"net": 150, "net_n_1": 0},
        }
    }
    result = compute_tafire(statements)
    # Activité: 150 (Profit) - 100 (Stocks) = 50
    assert result["activite"] == 50.0
    assert result["variation_tresorerie"] == 50.0
    assert result["coherence_check"] is True
