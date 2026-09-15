import os
from mistralai import Mistral
from typing import Dict

# Key is handled in .env
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

def generate_financial_commentary(statements: Dict) -> str:
    """
    Analyzes the financial statements and uses Mistral to generate a professional
    commentary on the significant variations.
    """
    if not MISTRAL_API_KEY:
        return "Erreur : Clé API Mistral non configurée."
        
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
    
    try:
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": "Tu es un expert-comptable de haut niveau."},
                {"role": "user", "content": prompt},
            ]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        print(f"Mistral API Error: {str(e)}")
        return f"Une erreur est survenue lors de la génération IA : {str(e)}"
