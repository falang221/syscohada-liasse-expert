import httpx
import os

PRICE_PER_LIASSE = 10000 # 10 000 FCFA

async def initiate_payment(dossier_id: str, item_name: str) -> str:
    """
    Simule l'initiation d'un paiement et retourne une URL de redirection.
    Pour le MVP, on redirige vers une page de mock sur le frontend.
    """
    # Dans une implémentation réelle, on appellerait une API de paiement (PayTech, PayExpresse, etc.)
    # pour obtenir une URL de paiement réelle.
    
    # MOCK implementation for testing
    return f"http://localhost:3000/payment/mock?dossier_id={dossier_id}"
