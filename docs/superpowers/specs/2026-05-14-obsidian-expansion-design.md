# Spec Design : Expansion du Cerveau Contextuel Obsidian

**Date** : 2026-05-14
**Topic** : Structuration et automatisation du vault Obsidian pour le suivi de projet et l'apprentissage IA.

## 1. Objectifs
- Standardiser la création de notes via des templates.
- Assurer la traçabilité des projets de développement (Postefinances).
- Mettre en place un journal quotidien pour la capture rapide et le suivi des objectifs.

## 2. Architecture du Vault (MyVault)
- `00_Contexte/` : Index et cartes de navigation.
- `10_Projets/` : Fiches projets actives.
- `20_Journal/` : Notes quotidiennes (format `YYYY-MM-DD.md`).
- `30_Connaissances/` : Base de connaissances atomiques.
- `90_Systeme/Templates/` : Modèles de notes.

## 3. Composants à Implémenter

### 3.1. Templates (`90_Systeme/Templates/`)
- **Note_Quotidienne.md** : Sections pour Objectifs, Journal, Tâches et Réflexions.
- **Projet_Dev.md** : Sections pour Architecture, Stack, Décisions (ADR), et Prochaines étapes.

### 3.2. Initialisation des Données
- Création de `20_Journal/2026-05-14.md`.
- Création de `10_Projets/Postefinances_Stock.md` en récupérant le contexte des sessions précédentes.

### 3.3. Maintenance de l'Index
- Mise à jour de `00_Contexte/Index_Memoire.md` pour inclure les nouveaux liens.

## 4. Succès Critère
- Les templates sont utilisables.
- Le projet Postefinances est documenté dans le vault.
- L'index reflète l'état actuel de l'espace de travail.

## 5. Auto-Révision (Self-Review)
- **Placeholders** : Aucun.
- **Consistance** : Alignement avec la structure existante de MyVault.
- **Portée** : Réaliste pour une phase d'implémentation immédiate.
