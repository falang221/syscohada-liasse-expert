# Design Document : SYSCOHADA Liasse-Expert

**Date :** 15 mai 2026
**Auteur :** Gemini CLI (Expert Vibe Coding) & Expert Comptable / Contrôleur de Gestion
**Statut :** Brouillon approuvé

## 1. Vision du Produit
`SYSCOHADA Liasse-Expert` est un micro-SaaS destiné aux cabinets comptables et directions financières au Sénégal. Son objectif est de transformer une balance générale et un grand livre en une liasse fiscale complète et conforme aux normes du SYSCOHADA révisé en quelques minutes.

### Problèmes résolus :
- Lenteur et erreurs manuelles lors du remplissage des liasses fiscales.
- Difficulté à justifier les montants des états financiers (manque de traçabilité).
- Complexité de rédaction des notes annexes (36 notes requises).

## 2. Architecture Technique
- **Backend :** FastAPI (Python 3.11+) pour la rapidité de traitement des données financières.
- **Frontend :** Next.js (TypeScript) avec Material UI ou Tailwind CSS pour une interface professionnelle.
- **Base de données :** PostgreSQL (via Prisma ORM) pour la persistance des dossiers clients et des audits logs.
- **Traitement de fichiers :** Pandas (Python) pour l'analyse des Grands Livres et Balances.
- **Génération PDF :** WeasyPrint ou ReportLab (templates HTML -> PDF) pour la conformité visuelle.

## 3. Fonctionnalités (MVP)

### 3.1. Gestion des Dossiers & Cabinet
- Système Multi-locataire (Multi-tenant) : Isolation stricte des données par cabinet.
- Rôles : **Administrateur (Expert)** et **Collaborateur (Assistant)**.
- Workflow de revue : Un collaborateur prépare, l'administrateur valide avant génération.

### 3.2. Importation des Données
- **Template Unique :** Fichier Excel standardisé avec deux onglets (`Balance`, `Grand_Livre`).
- Validation immédiate des colonnes et des types de données à l'upload.

### 3.3. Le "Validation Hub" (Dashboard)
- **Check d'Équilibre :** Calcul en temps réel de l'équilibre Bilan (Actif/Passif) et Compte de Résultat.
- **Explorateur de Flux (Drill-down) :** Cliquer sur un montant pour afficher les écritures comptables sources du Grand Livre.
- **Gestion des Notes Annexes :** Liste des 36 notes avec indicateur de statut (Complété, À valider, Manquant).
- **Éditeur de Commentaires :** Saisie directe des explications pour chaque note.

### 3.4. Génération de la Liasse
- **Pack Complet :** Bilan, Compte de Résultat, TAFIRE, et les 36 Notes Annexes.
- **Format :** PDF haute définition respectant scrupuleusement le canevas officiel de la DGID Sénégal.

## 4. Modèle de Données (Prisma)
- `User` : Authentification et rôles.
- `Cabinet` : Entité parente regroupant utilisateurs et dossiers.
- `Dossier` : Représente un client du cabinet pour un exercice donné (ex: Sonatel 2025).
- `AccountMapping` : Dictionnaire liant les racines de comptes aux rubriques SYSCOHADA.
- `NoteContent` : Contenu textuel et chiffré des notes annexes.

## 5. Sécurité & Conformité
- Chiffrement des données au repos.
- Conformité CDP (Commission de Protection des Données Personnelles du Sénégal).
- Option de purge automatique des données sensibles (Grand Livre) après génération.

## 6. Prochaines étapes (Plan d'implémentation)
1. Initialisation du projet (Scaffold FastAPI/Next.js).
2. Développement du moteur de mapping Balance -> Bilan.
3. Création de l'analyseur de Grand Livre pour les notes annexes.
4. Développement du Dashboard de Validation (React).
5. Intégration du moteur de génération PDF.
