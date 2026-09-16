from weasyprint import HTML
import jinja2
import os
from datetime import datetime

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

def generate_liasse_pdf(data: dict) -> bytes:
    """
    Génère un fichier PDF à partir d'un template HTML et des données fournies.
    
    Les données attendues dans le dictionnaire 'data' :
    - cabinet_name: str
    - dossier_name: str
    - exercice: str
    - title: str (optionnel)
    - table_rows: list[dict] (chaque dict ayant code, label, brut, amort, net_n, net_n_1, is_total)
    """
    # Ajouter la date de génération si non présente
    if "generated_at" not in data:
        data["generated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    
    # On peut charger le template principal
    # Note: On pourrait aussi passer le nom du template dynamiquement
    template_name = data.get("template_name", "liasse_template.html")
    template = template_env.get_template(template_name)
    
    html_out = template.render(data)
    
    # Génération du PDF
    return HTML(string=html_out).write_pdf()
