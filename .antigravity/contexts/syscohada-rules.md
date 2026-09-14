# SYSCOHADA — règles métier du moteur comptable

Contexte partagé Claude Code / Antigravity.
Dernière mise à jour : 2026-09-14 (mapping corrigé) · branche `test-agent/roo-syscohada-coherence`

## 1. Invariant fondamental du bilan

> **Total Actif = Total Passif**

C'est l'équation comptable de base du SYSCOHADA révisé. Tout écart signale une
balance tronquée, un compte non mappé, ou une écriture de sens inversé.

Implémentation : `backend/app/core/coherence.py`
Mapping : `backend/app/core/syscohada_rules.py`
Agrégation : `backend/app/services/financial_engine.py` (`_aggregate_balance`)
Tests : `backend/tests/test_coherence.py` (45 tests)

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
| 4 | Tiers | Bilan — Actif **ou** Passif | Selon le compte (41 actif, 40/42-44 passif, 45-48 selon le sens, 49 contra) |
| 5 | Trésorerie | Bilan — Actif (52-55, 57, 58) ou Passif (56), 59 contra | Selon le compte |
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

## 4. ✅ Mapping corrigé (2026-09-14)

Les 15 préfixes de bilan qui manquaient sont désormais couverts.

### Préfixes ajoutés

| Préfixe | Catégorie | Type | Code |
|---|---|---|---|
| `15`, `19` | Provisions pour risques et charges | `bilan_passif` | `DP` |
| `18` | Dettes liées aux participations | `bilan_passif` | `DD` |
| `25` | Avances et acomptes sur immobilisations | `bilan_actif` | `AN` |
| `55`, `57`, `58` | Trésorerie-Actif | `bilan_actif` | `BQ` |
| `45`, `46`, `47`, `48` | Comptes de tiers divers | `bilan_tiers` | `BJ` / `DJ` |
| `28` | Amortissements des immobilisations | `bilan_actif` **contra** | `AE` |
| `29` | Dépréciations des immobilisations financières | `bilan_actif` **contra** | `AF` |
| `39` | Dépréciations des stocks | `bilan_actif` **contra** | `AQ` |
| `49` | Dépréciations des comptes de tiers | `bilan_actif` **contra** | `BA` |
| `59` | Dépréciations de trésorerie | `bilan_actif` **contra** | `BQ` |

### ⚠️ L'ordre des règles est significatif

`get_category_for_account` applique **la première règle qui matche**. Les préfixes
contra sont donc placés **en tête** de `MAPPING_RULES` :

- `39` serait sinon capté par la règle large `("3",)` et **ajouté** à l'actif au
  lieu d'en être déduit — c'était le bug d'origine.
- Toute nouvelle règle plus spécifique qu'une règle existante doit être insérée
  **avant** elle.

### Comptes de tiers 45-48 : côté décidé par le sens

Un compte `4xx` de ces classes peut être une créance ou une dette selon son solde.
`resolve_tiers_side()` tranche :

```
solde débiteur (débit ≥ crédit) -> actif  "Autres créances" (BJ)
solde créditeur                 -> passif "Autres dettes"   (DJ)
```

### Reste non mappé

`14` (subventions d'investissement) est **toujours absent**. C'est volontaire :
il sert de cas de test au détecteur d'anomalies
(`test_signale_un_compte_de_bilan_non_mappe`). À mapper quand le besoin métier
se présente — vers `bilan_passif`.

## 5. Présentation brut / amortissements / net

En SYSCOHADA l'actif se présente en trois colonnes. Le moteur les alimente
désormais correctement.

### Mécanique

Les comptes contra (`28`, `29`, `39`, `49`, `59`) ont un **solde créditeur
naturel** et ne sont jamais ajoutés au `brut`. Ils alimentent `amort` de la
catégorie qu'ils réduisent, via la clé `reduces` de la règle.

```
net = brut − amort
```

Le `net` est calculé en **passe finale**, après lecture de toutes les lignes.
Conséquence : l'ordre des lignes dans la balance n'a aucune importance — un
amortissement peut précéder l'immobilisation qu'il réduit
(`test_amort_avant_immobilisation_dans_la_balance`).

### Dans `check_balance_coherence`

Un compte contra est **déduit** du Total Actif :

```python
if is_contra:
    solde = credit - debit
    total_actif -= solde
```

Un solde débiteur sur un compte d'amortissement est signalé comme sens inversé.

### Exemple

```
241  matériel        1 000 000 D
2841 amortissement     200 000 C
101  capital            800 000 C
```

donne `brut = 1 000 000`, `amort = 200 000`, `net = 800 000`, et le bilan est
équilibré. Avant la correction, l'actif valait `1 000 000` et le bilan était
rapporté déséquilibré de 200 000 XOF.

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
./venv/bin/pytest tests/test_coherence.py -v    # 45 tests
./venv/bin/pytest tests/ -k coherence -q       # 45 tests, 11 deselected
./venv/bin/pytest tests/ -q                    # suite complète, 56 tests
```
