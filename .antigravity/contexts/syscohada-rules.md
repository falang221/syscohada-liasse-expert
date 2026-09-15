# SYSCOHADA — règles métier du moteur comptable

Contexte partagé Claude Code / Antigravity.
Dernière mise à jour : 2026-09-15 (garde anti-fantôme, N-1 rendu) · branche `fix/syscohada-bilan-coherence`

## 1. Invariant fondamental du bilan

> **Total Actif = Total Passif**

C'est l'équation comptable de base du SYSCOHADA révisé. Tout écart signale une
balance tronquée, un compte non mappé, ou une écriture de sens inversé.

Implémentation : `backend/app/core/coherence.py`
Mapping : `backend/app/core/syscohada_rules.py`
Agrégation : `backend/app/services/financial_engine.py` (`_aggregate_balance`)
Tests : `backend/tests/test_coherence.py` (58) + `test_liasse_template.py` (10)

```python
from app.core.coherence import check_balance_coherence, format_anomaly_report

report = check_balance_coherence(parsed_balance)
if not report.is_balanced:
    print(format_anomaly_report(report))
```

Le résultat est aussi exposé par le moteur : `compute_financial_statements()`
renvoie une clé `coherence` (dict sérialisable JSON), et une clé `coherence_n_1`
lorsqu'une balance N-1 est fournie. Les deux exercices sont contrôlés
indépendamment — un N équilibré ne garantit rien sur N-1.

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
| `Dépréciation sans créance / immobilisation / stock correspondant` | Tout contra (`28x`, `29x`, `39x`, `49x`, `59x`) dont le seau cible est absent ou de `brut` nul — y compris un compte soldé. Déduit du Total Actif mais non imputé à une ligne. |

Les anomalies sont triées par **solde absolu décroissant** : le plus gros suspect
apparaît en premier.

> ⚠️ **`totaux_par_classe` est NET, pas brut.** Les contras (28, 29, 39, 49, 59)
> y sont déduits de leur classe. Un rapprochement avec une balance brute doit en
> tenir compte : la classe 2 affichée est `immobilisations − amortissements`.

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
| `29` | Dépréciations des immobilisations | `bilan_actif` **contra miroir** | `AF` |
| `39` | Dépréciations des stocks | `bilan_actif` **contra** | `AQ` |
| `49` | Dépréciations des comptes de tiers | `bilan_actif` **contra miroir** | `BA` |
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

### Cible dynamique : le miroir `49D → 4D` et `29D → 2D`

Les contras ne visent pas tous un seau fixe. Convention de numérotation du plan :
**le 3ᵉ chiffre d'un compte de dépréciation reprend le 2ᵉ chiffre du compte
qu'il déprécie.**

```
491 → 41x (clients)              291 → 21x (incorporelles)
496 → 46x (débiteurs divers)     294 → 24x (corporelles)
497 → 47x                        296 → 26x (titres de participation)
```

**Pourquoi c'est nécessaire.** Une créance `461` débitrice est agrégée dans
« Autres créances » (BJ) par la résolution `sign_based`, pas dans « Créances et
emplois assimilés » (BA). Une règle statique `49 → BA` faisait donc atterrir la
dépréciation d'un `461` sur un seau au `brut` nul → **ligne nette négative**,
pendant que le `461` restait présenté brut, non déprécié. Les totaux restaient
justes (`coherence` déduit du Total Actif) ; seule la présentation mentait.

**Pas de fusion des seaux.** BA et BJ sont deux lignes distinctes de la liasse
DGID. Les fusionner corrigerait le symptôme en cassant le format réglementaire.

`28`, `39`, `59` gardent une cible statique : leur miroir donnerait le même seau.

### Les trois passes de `_aggregate_balance`

1. **Lignes non-contra.** Résolution `sign_based` des 45-48 ici. Chaque atterrissage
   à l'actif est mémorisé par préfixe à 2 chiffres.
2. **Lignes contra.** Cible statique pour 28/39/59 ; miroir pour 29/49.
3. **`net = brut − amort`.**

L'ordre des lignes n'a donc aucune importance : un `496` placé avant son `461`
donne le même résultat (`test_amort_miroir_ordre_inverse`).

### Règle d'imputation : seau cible avec `brut != 0`

La règle vaut pour **tous** les contras, statiques comme miroirs :

> Un contra n'est imputé que si son seau cible **existe déjà avec un `brut`
> non nul** à l'issue de la passe 1.

Le test se fait par **accès en lecture** (`res["bilan_actif"].get(...)`), jamais
par `_ensure_bucket` — qui créerait le fantôme au moment même de le tester.

Quatre situations laissent un contra non imputé :

| Cas | Exemple |
|---|---|
| Cible absente de la balance | `2841` seul, sans aucun `2x` |
| Miroir absent | `496` sans `46x` à l'actif |
| **Compte soldé** (`débit == crédit`) | `461` 100k/100k → seau créé mais `brut = 0` |
| Miroir résolu au passif | `461` créditeur est une dette, pas une créance |
| Numéro de moins de 3 chiffres | `49` sans chiffre miroir |

Le cas du **compte soldé** est fréquent dans les exports réels : la passe 1 crée
bien le seau, mais avec un `brut` nul. Sans la garde, le contra s'y imputait et
produisait une ligne nette négative.

Dans tous ces cas la dépréciation reste **déduite du Total Actif** par
`check_balance_coherence`, le compte est signalé avec un motif dédié, et un
`logger.warning` est émis côté moteur :

```
Depreciation sans creance correspondante : aucun compte 46 a l'actif
- deduite du total mais non imputee

Depreciation sans immobilisation correspondante : aucun brut sur
'Immobilisations incorporelles et corporelles' - deduite du total mais non imputee
```

> ⚠️ **Divergence assumée des deux totaux.** En présence d'un orphelin, le TOTAL
> ACTIF du tableau (somme des seaux) et celui de l'annexe
> (`coherence.total_actif`, qui déduit le contra) **ne coïncident pas**. Exemple :
> un `2841` seul donne `0` au tableau et `-200 000` à l'annexe. C'est voulu — le
> tableau ne doit afficher aucune ligne fantôme, et l'annexe doit signaler
> l'anomalie sur le total.

### Imputation agrégée au seau

L'imputation vise **la ligne agrégée de la liasse**, pas le compte individuel.
Si `461` est soldé mais que `471` alimente « Autres créances », un `496`
s'impute sur BJ. BJ étant une ligne agrégée du formulaire DGID, le comportement
est acceptable — verrouillé par `test_imputation_agregee_au_seau`.

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

## 6. Restitution dans la liasse PDF

`backend/app/templates/liasse_template.html` — tests : `backend/tests/test_liasse_template.py`

### Colonne Amort/Prov

La colonne était **codée en dur à `0`** dans le template (ligne de détail et
ligne TOTAL ACTIF). Même une fois `amort` correctement alimenté par le moteur, le
PDF aurait continué d'afficher zéro. Elle lit maintenant `values.amort` et le
total agrège les amortissements.

### Bandeau d'alerte

Affiché en tête du BILAN - ACTIF uniquement si `statements.coherence.is_balanced`
est faux : montant de l'écart, sens, renvoi vers l'annexe.

Un second bandeau, dans l'annexe, signale un **exercice N-1 déséquilibré**
(`coherence_n_1`). Un N équilibré ne masque donc plus un N-1 qui ne l'est pas.

### Annexe de contrôle

Nouvelle page en fin de document, toujours présente quand la clé `coherence`
existe :

- Total Actif / Total Passif / écart / tolérance
- si équilibré : mention de validation
- sinon : totaux par classe SYSCOHADA, puis tableau des comptes suspects
  (compte, classe, réf. DGID, débit, crédit, solde, motif)

Le payload expose `coherence.classes` — la même donnée que `totaux_par_classe`
mais avec le libellé attaché — pour éviter d'injecter `CLASS_LABELS` dans le
contexte Jinja.

### Rétrocompatibilité

Un `statements` sans clé `coherence` se rend sans erreur : l'annexe et le bandeau
sont simplement omis (`test_rendu_sans_cle_coherence_ne_casse_pas`).

## 7. Fixtures de test

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

## 8. Commandes

```bash
cd backend
./venv/bin/pytest tests/test_coherence.py -v        # 58 tests
./venv/bin/pytest tests/test_liasse_template.py -v # 10 tests de rendu
./venv/bin/pytest tests/ -q                        # suite complète, 79 tests
```
