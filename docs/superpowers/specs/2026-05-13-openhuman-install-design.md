# Design Spec: Openhuman Installation (Discovery Mode)

- **Date:** 2026-05-13
- **Topic:** installation-openhuman
- **Status:** Approved (Conceptual)

## Purpose
Installer Openhuman en utilisant la méthode binaire officielle ("Discovery Mode") pour permettre une exploration rapide des fonctionnalités d'agent IA personnel sans complexité de compilation.

## Architecture
- **Type:** Application de bureau (Tauri / Rust + TypeScript).
- **Mode d'installation:** Script de déploiement automatique téléchargeant des binaires pré-compilés.
- **Persistence:** Données stockées localement dans `~/Library/Application Support/OpenHuman` (macOS).
- **Mémoire:** Base SQLite locale et intégration Obsidian.

## Installation Flow
1. **Fetch & Execute:** Téléchargement du script `install.sh` depuis le dépôt GitHub `tinyhumansai/openhuman`.
2. **Detection:** Identification automatique de l'OS (macOS dans ce cas).
3. **Download:** Récupération de l'archive `.app.tar.gz` de la dernière release stable.
4. **Deploy:** Extraction dans `/Applications/OpenHuman.app`.

## Verification Plan
1. **Lancement:** Vérifier que l'application s'ouvre correctement.
2. **Initialisation:** Suivre l'assistant de configuration pour l'indexation de la mémoire.
3. **Connectivité:** Tester une intégration de base (ex: recherche web ou accès à un fichier local).

## Risks & Constraints
- **Permissions:** Le script peut demander des permissions sudo ou d'accessibilité (TCC) sur macOS.
- **Privacy:** Bien que locale, l'IA peut nécessiter une clé API (OpenAI/Anthropic) si un LLM local (Ollama) n'est pas utilisé.

## Success Criteria
- L'application est présente dans `/Applications`.
- L'interface de la mascotte est fonctionnelle.
- La base de connaissances locale commence à s'indexer.
