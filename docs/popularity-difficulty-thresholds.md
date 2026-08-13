# Seuils de difficulté par genre (colonne `popularity`)

Issue #33.

## Problème

La colonne `popularity` (remplie depuis le champ `rank` de l'API Deezer) va
de 0 à ~1 000 000, mais cette échelle n'a pas le même sens selon le genre :
un seuil fixe comme `popularity > 900000` fonctionne pour la pop ou la
chanson française, mais élimine quasiment tout le catalogue `movies`/`series`
(dont le maximum dépasse à peine 900000).

## Méthodologie

Stats calculées sur `data/blindtest.db` le 13/08/2026, groupées par **genre**
(pas sous-genre), sur la colonne `popularity` (valeurs non nulles) :

| genre | n | min | p25 | médiane | moyenne | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|
| chanson_fr | 814 | 3096 | 534315 | 736586 | 647078 | 838791 | 910404 | 999849 |
| pop | 917 | 6915 | 538264 | 722545 | 664116 | 852541 | 935467 | 999852 |
| rap | 899 | 2755 | 387433 | 601977 | 566092 | 766403 | 888937 | 1000000 |
| rock | 1386 | 693 | 310513 | 514819 | 498571 | 696157 | 839205 | 983791 |
| country | 175 | 138 | 354203 | 454613 | 428545 | 534628 | 646525 | 794208 |
| electro | 1087 | 425 | 261003 | 419085 | 423228 | 572376 | 725559 | 992922 |
| funk_soul | 199 | 15690 | 334358 | 566530 | 506034 | 710823 | 791435 | 971939 |
| metal | 1017 | 1919 | 223000 | 344997 | 362543 | 472025 | 617648 | 982895 |
| movies | 363 | 2 | 107340 | 200074 | 274488 | 419652 | 593184 | 918197 |
| series | 103 | 17786 | 172570 | 308094 | 317598 | 439332 | 565901 | 781689 |

## Seuils retenus : tertiles (33% / 67%) par genre

Plutôt qu'un seuil absolu global, 3 niveaux équilibrés propres à chaque genre,
basés sur les tertiles de sa propre distribution :

| genre | Difficile (< ) | Intermédiaire | Facile (≥ ) |
|---|---|---|---|
| chanson_fr | 617069 | 617069 – 810047 | 810047 |
| pop | 612272 | 612272 – 816284 | 816284 |
| rap | 474900 | 474900 – 715719 | 715719 |
| rock | 386515 | 386515 – 632738 | 632738 |
| country | 386787 | 386787 – 510484 | 510484 |
| electro | 317417 | 317417 – 510583 | 510583 |
| funk_soul | 435504 | 435504 – 649426 | 649426 |
| metal | 267768 | 267768 – 424762 | 424762 |
| movies | 141699 | 141699 – 346471 | 346471 |
| series | 206094 | 206094 – 411353 | 411353 |

## Utilisation dans le code

Table figée + helper dans `core/database.py` (`DIFFICULTY_THRESHOLDS`,
`popularity_range_for_difficulty(genre, difficulty)`), qui convertit un
niveau (`"facile"`, `"intermediaire"`, `"difficile"`) en
`(min_popularity, max_popularity)` directement utilisable par `get_tracks()` :

```python
min_pop, max_pop = popularity_range_for_difficulty("movies", "facile")
get_tracks(nb_tracks=20, genre="movies", min_popularity=min_pop, max_popularity=max_pop)
```

## ⚠️ Limite : c'est un instantané (snapshot)

Ces seuils sont calculés une fois sur l'état de la DB au 13/08/2026. Si la DB
est réimportée/enrichie significativement plus tard (nouveaux genres, plus
d'artistes), la distribution réelle bougera et ces seuils resteront figés —
donc de moins en moins précis avec le temps. Alternative envisagée mais non
retenue pour l'instant : calcul dynamique en SQL via une fonction fenêtrée
(`PERCENT_RANK() OVER (PARTITION BY genre ORDER BY popularity)`), qui resterait
toujours juste mais complexifie `get_tracks()`. À reconsidérer si les seuils
dérivent trop.
