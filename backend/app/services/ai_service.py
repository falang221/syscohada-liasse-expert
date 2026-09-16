import logging
import os
from mistralai.client.sdk import Mistral
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Key is handled in .env
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

# The model is deliberately configurable: API tiers differ, and a hardcoded
# name that the account cannot reach fails on every single call.
DEFAULT_MISTRAL_MODEL = "mistral-large-latest"


def get_mistral_model() -> str:
    """Model used for the commentary. Override with MISTRAL_MODEL."""
    return os.environ.get("MISTRAL_MODEL") or DEFAULT_MISTRAL_MODEL


def generate_financial_commentary(statements: Dict) -> Optional[str]:
    """
    Analyzes the financial statements and uses Mistral to generate a professional
    commentary on the significant variations.

    Returns None when the commentary cannot be produced - missing key, API
    error, empty response. Callers must treat None as "no commentary" and omit
    the section entirely. NEVER return an error string: this value is rendered
    in the liasse PDF under "NOTE DE SYNTHÈSE DE LA DIRECTION", a document
    handed to the client.
    """
    if not MISTRAL_API_KEY:
        logger.warning("MISTRAL_API_KEY absente - commentaire IA ignore")
        return None

    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # 1. Extract significant data
    produits_n = sum(v.get("net", 0) for v in statements.get("resultat_produit", {}).values())
    produits_n_1 = sum(v.get("net_n_1", 0) for v in statements.get("resultat_produit", {}).values())
    
    charges_n = sum(v.get("net", 0) for v in statements.get("resultat_charge", {}).values())
    charges_n_1 = sum(v.get("net_n_1", 0) for v in statements.get("resultat_charge", {}).values())
    
    res_n = produits_n - charges_n
    res_n_1 = produits_n_1 - charges_n_1
    
    # Calculate variation percentages safely
    ca_var = ((produits_n - produits_n_1) / produits_n_1 * 100) if produits_n_1 else 0
    res_var = ((res_n - res_n_1) / abs(res_n_1) * 100) if res_n_1 else 0
    
    # 2. Build the prompt
    prompt = f"""
    Agis comme un Expert-Comptable sénégalais très expérimenté.
    Rédige une "Note de Synthèse de la Direction" professionnelle (max 3 paragraphes) basée sur ces données du SYSCOHADA :
    
    - Produits d'exploitation (N) : {produits_n:,.0f} FCFA (Variations: {ca_var:+.1f}%)
    - Charges d'exploitation (N) : {charges_n:,.0f} FCFA
    - Résultat Net (N) : {res_n:,.0f} FCFA (Variations: {res_var:+.1f}%)
    
    Instructions :
    - Ton ton doit être très formel et rassurant.
    - Analyse brièvement la performance (Hausse/Baisse).
    - Ne mets pas d'introduction du type "Voici la note". Donne directement le texte final.
    """
    
    model = get_mistral_model()
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": "Tu es un expert-comptable de haut niveau."},
                {"role": "user", "content": prompt},
            ]
        )
        commentaire = chat_response.choices[0].message.content
    except Exception:
        # Full context stays in the logs; nothing leaks into the PDF.
        logger.exception("Appel Mistral echoue (modele=%s) - commentaire ignore", model)
        return None

    if not commentaire or not commentaire.strip():
        logger.warning("Reponse Mistral vide (modele=%s) - commentaire ignore", model)
        return None

    return commentaire.strip()
