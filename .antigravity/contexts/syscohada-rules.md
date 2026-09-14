# SYSCOHADA — règles métier du moteur comptable

Contexte partagé Claude Code / Antigravity.
Dernière mise à jour : 2026-09-14 · branche `test-agent/roo-syscohada-coherence`

## 1. Invariant fondamental du bilan

> **Total Actif = Total Passif**

C'est l'équation comptable de base du SYSCOHADA révisé. Tout écart signale une
balance tronquée, un compte non mappé, ou une écriture de sens inversé.

Implémentation : `backend/app/core/coherence.py`
Tests : `backend/tests/test_coherence.py` (23 tests)

```python
from app.core.coherence import check_balance_coherence, format_anomaly_report

report = check_balance_coherence(parsed_balance)
if not report.is_balanced:
    print(format_anomaly_report(report))
```

Le résultat est aussi exposé par le moteur : `compute_financial_statements()`
renvoie désormais une clé `coherence` (dict sérialisable JSON).

### Tolérance

`TOLERANCE_XOF = 1.0`. Les états SYSCOHADA sont présentés en francs entiers ;
un écart d'un franc ou moins est un artefact d'arrondi, pas un déséquilibre.
Surchargeable : `check_balance_coherence(rows, tolerance=200.0)`.

## 2. Classes de comptes SYSCOHADA

| Classe | Intitulé | Destination | Sens normal |
|---|---|---|---|
| 1 | Ressources durables | Bilan — Passif | Créditeur |
| 2 | Actif immobilisé | Bilan — Actif | Débiteur |
| 3 | Stocks | Bilan — Actif | Débiteur |
| 4 | Tiers | Bilan — Actif **ou** Passif | Selon le compte |
| 5 | Trésorerie | Bilan — Actif (52-54) ou Passif (56) | Selon le compte |
| 6 | Charges | Compte de résultat | Débiteur |
| 7 | Produits | Compte de résultat | Créditeur |
| 8 | Autres charges et produits | Compte de résultat | Variable |

**Seules les classes 1 à 5 peuvent déséquilibrer un bilan.** Si un compte de
classe 6, 7 ou 8 se retrouve mappé sur le bilan, c'est une anomalie de mapping —
le détecteur la signale explicitement.

### Calcul du solde

```
compte d'actif  : solde = débit  − crédit
compte de passif: solde = crédit − débit
```

Un solde négatif sur son côté naturel = **sens inversé**, signalé comme anomalie.

## 3. Motifs d'anomalie produits

| Motif | Signification |
|---|---|
| `Compte de bilan non mappé (classe N)` | Le compte existe dans la balance mais aucune règle de `MAPPING_RULES` ne le capte → il disparaît des deux totaux. Cause la plus fréquente d'écart. |
| `Solde débiteur/créditeur anormal` | Sens inversé par rapport à la nature du compte. |
| `Compte de gestion mappé sur le bilan` | Un compte de classe 6-8 pollue le bilan : bug de mapping. |

Les anomalies sont triées par **solde absolu décroissant** : le plus gros suspect
apparaît en premier.

## 4. ⚠️ Trous connus dans `MAPPING_RULES`

`backend/app/core/syscohada_rules.py` ne couvre pas ces préfixes de bilan.
Tout compte commençant par l'un d'eux est **silencieusement exclu des totaux** :

```
15, 18, 19, 25, 28, 29, 45, 46, 47, 48, 49, 55, 57, 58, 59
```

Les plus impactants :

| Préfixe | Comptes | Conséquence |
|---|---|---|
| `15` | Provisions pour risques et charges | Passif manquant → Actif > Passif |
| `19` | Provisions financières pour risques | Idem |
| `28` / `29` | Amortissements et dépréciations des immobilisations | Actif brut non déprécié → Actif surévalué |
| `39` | Dépréciations des stocks | Idem (`39` est capté par la règle `("3",)`, donc **ajouté** à l'actif au lieu d'en être déduit) |
| `49` | Dépréciations des comptes de tiers | Idem |
| `45`-`48` | État, organismes sociaux, débiteurs/créditeurs divers | Tiers manquants des deux côtés |
| `55`, `57` | Instruments de monnaie électronique, caisse | Trésorerie sous-évaluée |

**Ce n'est pas théorique** : un bilan contenant un compte `151` de 200 000 XOF
est rapporté déséquilibré de 200 000 XOF, avec `151` désigné comme cause.

Corriger `MAPPING_RULES` est la suite logique de ce ticket — non fait ici pour
garder le diff centré sur la règle de cohérence.

## 5. Piège : les comptes d'amortissement

La règle actuelle `{"prefix": ("21","22","23","24"), ...}` capte l'actif immobilisé
brut, mais `28xx` (amortissements) n'est pas mappé. En SYSCOHADA l'actif se présente
en **brut / amortissements / net**. Le champ `amort` existe dans la structure du
moteur (`_aggregate_balance`) mais **n'est jamais alimenté** : il reste à `0.0`.
Le `net` est donc égal au `brut`, ce qui surévalue l'actif dès qu'il y a des
immobilisations amorties.

## 6. Fixtures de test

Aucune donnée comptable réelle dans les tests. Deux fixtures de référence :

**Bilan équilibré** — Actif 1 500 000 = Passif 1 500 000
```
241 matériel      1 000 000 D    101 capital       1 200 000 C
311 stocks          300 000 D    401 fournisseurs    300 000 C
521 banque          200 000 D
```

**Bilan déséquilibré** — écart 300 000 (le `401` manque)
```
241 matériel      1 000 000 D    101 capital       1 200 000 C
311 stocks          300 000 D
521 banque          200 000 D
```

## 7. Commandes

```bash
cd backend
./venv/bin/pytest tests/test_coherence.py -q     # 23 tests
./venv/bin/pytest tests/ -q                      # suite complète, 34 tests
```
