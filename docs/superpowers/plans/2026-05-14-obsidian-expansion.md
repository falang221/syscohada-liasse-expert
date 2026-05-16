# Expansion du Cerveau Contextuel Obsidian Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Structurer le vault Obsidian avec des templates, une note quotidienne et une fiche projet détaillée pour Postefinances.

**Architecture:** Utilisation d'une structure de dossiers organisée par type (Contexte, Journal, Projets, Système). Les notes sont reliées entre elles par des wikilinks pour former un graphe de connaissances.

**Tech Stack:** Obsidian (Markdown), Gemini CLI (pour l'automatisation).

---

### Task 1: Création des Templates

**Files:**
- Create: `MyVault/90_Systeme/Templates/Note_Quotidienne.md`
- Create: `MyVault/90_Systeme/Templates/Projet_Dev.md`

- [ ] **Step 1: Créer le template de Note Quotidienne**

```markdown
---
type: journal
tags: [journal/quotidien]
---
# {{date}}

## 🎯 Objectifs du Jour
- [ ] 

## 📝 Journal / Notes de Session
- 

## ✅ Tâches Complétées
- 

## 💡 Réflexions & Apprentissages
- 
```

- [ ] **Step 2: Créer le template de Projet de Développement**

```markdown
---
type: projet
status: actif
tags: [projet/dev]
---
# Nom du Projet

## 📋 Résumé
[Description courte du projet]

## 🏗️ Architecture & Stack
- **Backend** : 
- **Frontend** : 
- **Base de données** : 

## 📜 Décisions Clés (ADR)
- [YYYY-MM-DD] : 

## 🚀 Prochaines Étapes
- [ ] 

## 🔗 Liens
- [[00_Contexte/Index_Memoire|Index Principal]]
```

- [ ] **Step 3: Vérifier la création des fichiers**

Run: `ls MyVault/90_Systeme/Templates/`

### Task 2: Initialisation de la Note du Jour

**Files:**
- Create: `MyVault/20_Journal/2026-05-14.md`

- [ ] **Step 1: Créer la note du jour pour le 14 mai 2026**

```markdown
---
type: journal
tags: [journal/quotidien]
created: 2026-05-14
---
# 2026-05-14

## 🎯 Objectifs du Jour
- [x] Initialisation de la structure du vault Obsidian.
- [ ] Documenter le projet Postefinances Stock.
- [ ] Mettre en place le système de templates.

## 📝 Journal / Notes de Session
- Travail sur la structuration du "Second Brain" avec Gemini CLI.
- Adoption d'une nomenclature claire pour les dossiers.

## ✅ Tâches Complétées
- [x] Création des dossiers de base.
- [x] Création de l'index mémoire.

## 💡 Réflexions & Apprentissages
- Utiliser Obsidian comme mémoire contextuelle permet de décharger le prompt de Gemini CLI et de garder une trace long-terme.
```

### Task 3: Documentation du Projet Postefinances Stock

**Files:**
- Create: `MyVault/10_Projets/Postefinances_Stock.md`

- [ ] **Step 1: Créer la fiche projet Postefinances_Stock**

```markdown
---
type: projet
status: actif
tags: [projet/dev, postefinances, stock]
created: 2026-05-14
---
# Postefinances Stock

## 📋 Résumé
Application de gestion de stock pour Postefinances SA. Gère les produits, les commandes, les rapports et les audits.

## 🏗️ Architecture & Stack
- **Backend** : FastAPI (Python)
- **Frontend** : Next.js (React)
- **Base de données** : PostgreSQL avec Prisma ORM
- **Serveur** : 10.2.0.242 (glpi)

## 📜 Décisions Clés (ADR)
- **Soft Deletes** : Implémenté pour Product, Request, User, etc. via Prisma Middleware.
- **Audit Log** : Système de traçabilité complet des actions administratives.
- **Enums** : Harmonisés en anglais (DRAFT, PENDING) avec traduction frontend en français.
- **Auth** : JWT avec Blacklist pour le logout sécurisé.

## 🚀 Prochaines Étapes
- [ ] Finaliser l'intégration du module Budget (en cours).
- [ ] Optimiser les performances des rapports complexes.

## 🔗 Liens
- [[00_Contexte/Index_Memoire|Index Principal]]
```

### Task 4: Mise à jour de l'Index Mémoire

**Files:**
- Modify: `MyVault/00_Contexte/Index_Memoire.md`

- [ ] **Step 1: Ajouter les nouveaux liens dans l'index**

```markdown
---
type: index
status: actif
---
# Index Mémoire

Ce fichier est la source de vérité pour l'état actuel de mes connaissances et projets.

## Projets Actifs
- [[Initialisation_Vault]] : Mise en place de la structure du cerveau IA.
- [[Postefinances_Stock]] : Gestion de stock (FastAPI/Next.js).
- [[Apprentissage_IA_et_Code]] : Hub de connaissances sur le développement assisté par IA.
- [[Organisation_Vie_Numerique]] : Plan de structuration de l'écosystème numérique.

## Ressources Clés
- [[00_Contexte/Index_Memoire|Cet Index]]
- [[90_Systeme/Templates/Note_Base|Template de Base]]
- [[90_Systeme/Templates/Note_Quotidienne|Template Quotidien]]
- [[90_Systeme/Templates/Projet_Dev|Template Projet Dev]]

## Historique Récent
- [2026-05-14] Création du vault Obsidian et initialisation de la note quotidienne.
- [2026-05-14] Documentation du projet Postefinances Stock.
```
