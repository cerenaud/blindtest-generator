# Plan : ajout des genres Movies & Series (issue #31)

## Contexte / problème

Le mécanisme actuel (`import_by_genre`) fonctionne en cherchant un **artiste** sur
Deezer puis en récupérant ses **top tracks**. Ça marche pour un groupe/artiste
musical classique, mais pas pour un compositeur de musique de film
(ex: Hans Zimmer a scoré 50+ films ; ses "top tracks" Deezer sont dominés par
ses BO les plus streamées globalement, pas forcément celle qu'on vise).

Décisions prises :
- Deux genres séparés : `movies` et `series` (usages différents en blindtest).
- Sous-genres organisés **par type** (action, animation, sci-fi_fantasy,
  horror_thriller, comedy, drama...), pas par année.
- Le filtre par année reste possible indépendamment via `min_year`/`max_year`
  (déjà supportés par `get_tracks`/`generate_blindtest_iterative`) grâce à la
  colonne `year` déjà remplie par `_insert_tracks`. Pas besoin de dimension
  année dans `genres.py`.

## Format de données (v2, révisé le 12/08/2026 — voir "Re-curation" plus bas)

Chaque sous-genre movies/series n'est **pas** une liste de strings (comme les
genres musicaux) mais un **dict** `{query_de_recherche: (titre_affiché, compositeur_attendu)}` :

```python
sci_fi = {
    "Duel of the Fates": ("Star Wars : La Menace fantôme", "John Williams"),
    "The Imperial March": ("Star Wars : L'Empire contre-attaque", "John Williams"),
}
```

- La clé = titre exact du thème/morceau tel qu'il existe **réellement sur
  Deezer** (vérifié par recherche, pas deviné — voir "Re-curation" plus bas).
- La valeur = tuple `(titre affiché dans le blindtest, compositeur/artiste
  attendu)`. Le compositeur sert à la fois à construire la query Deezer
  (`f"{clé} {compositeur}"`) et à vérifier le résultat (voir plus bas).
- Plusieurs clés peuvent pointer vers le même film (franchises à plusieurs
  thèmes iconiques).
- ⚠️ Ancien format v1 `{query: titre}` (string seule) encore présent sur les
  sous-genres pas encore migrés — `import_movies_series` supporte les deux en
  parallèle via un shim de compatibilité temporaire (à retirer une fois tout
  migré, voir tracker plus bas).

## Affichage au reveal

Le reveal (`video.py`) affiche aujourd'hui partout `f"{track.artist} - {track.title}"`
(dupliqué ~10 fois dans les 5 fonctions `build_clip_*`, + `make_reveal_frame`
dans `visuals.py`). Il faut :

- Pour `track.genre in ("movies", "series")` : afficher seulement le titre du
  film/série (stocké dans le champ `artist` en DB à l'import, cf. plus bas).
- Pour tout le reste : garder `artiste - titre` comme actuellement.
- Option supplémentaire : paramètre `show_year` pour afficher l'année en plus.
  - Format validé : année brute entre parenthèses, ex. `"Star Wars (1979)"`,
    `"John Williams - Duel of the Fates (1979)"` — juste le nombre à 4
    chiffres (`track.year`), pas de texte autour.
  - Stocké comme attribut sur l'objet `track` (`track.show_year`), plutôt que
    de faire traverser un booléen dans les ~5 fonctions `build_clip_*`.

## Étapes d'implémentation

1. **Structure `genres.py`** : ajouter les genres `movies` et `series` avec
   leurs sous-genres (dict `{query: titre}` comme décrit ci-dessus).
2. **Curation des données** : rédiger les entrées (thèmes iconiques → film/série)
   pour chaque sous-genre.
3. **Fix bug `core/audio.py`** (ligne ~81) :
   ```python
   instance.genre = db_row[4]
   instance.genre = db_row[5]   # BUG : écrase instance.genre au lieu de subgenre
   ```
   → doit être `instance.subgenre = db_row[5]`. Sans ce fix, `track.genre`
   contient en réalité le subgenre et on ne peut pas fiabiliser la condition
   d'affichage.
4. **Helper d'affichage centralisé** (`video.py`/`visuals.py`) :
   - Nouvelle fonction (ex: `reveal_label(track)`) qui centralise la logique :
     - `movies`/`series` → titre seul (+ année si `track.show_year`)
     - autres genres → `artiste - titre` (+ année si `track.show_year`)
   - Remplacer les ~10 occurrences dupliquées de
     `f"{track.artist} - {track.title}"` par un appel à ce helper.
5. **Paramètre `show_year`** dans `generate_blindtest`/`generate_blindtest_iterative`
   (`core/generator.py`), par défaut `False`, assigné sur `track.show_year` au
   moment de `AudioTrack.from_db(...)`.
6. **Nouvelle fonction d'import** `import_movies_series(genre_name, nb_tracks)`
   dans `core/database.py` — voir section "Re-curation" plus bas pour la
   version actuelle (v2) de la logique de vérification, plus stricte que ce
   qui est décrit ici initialement.
7. **Câblage `main.py`** : ajouter les appels
   `import_movies_series("movies", N)` et `import_movies_series("series", N)`.
8. **Test** : import limité + génération d'un petit blindtest movies pour
   vérifier que le reveal affiche bien le titre seul, et qu'un blindtest
   musique classique n'est pas affecté (garde `artiste - titre`).

## Ordre de démarrage validé

Points **1 et 2** en premier (structure + curation des données), puis 3 à 8.

## Sous-genres validés

**movies** (17, basé sur la nomenclature Wikipedia des genres cinématographiques,
en fusionnant les genres trop proches côté "son de BO" et en écartant ceux
dont le vivier de thèmes iconiques est trop mince pour un blindtest) :

action, aventure, sci_fi (fusionne anticipation), casse, catastrophe, comedie,
criminel, drame, fantasy (fusionne fantastique), horreur, historique, peplum,
noel, romance, thriller, western, musical

Écartés : cape et d'épée (Pirates of the Caribbean classé en `aventure`,
vivier trop mince à part), film d'opéra (trop confidentiel pour du grand
public).

**series** (7, regroupements plus larges que les films car la TV a moins de
thèmes composés vraiment iconiques par genre) :

sci_fi, fantasy, horreur, thriller_policier (fusionne crime+thriller),
drame, comedie_sitcom, animation

Romance écartée côté series (vivier trop mince pour un thème hummable
vraiment iconique).

## Re-curation des queries (12/08/2026) — pourquoi et comment

**Problème découvert en conditions réelles** : après un premier import complet
via `import_movies_series`, quasi aucun morceau n'a été inséré en DB. Cause :
la majorité des entrées suivaient le pattern générique `"<Titre film> Theme"`
(fallback utilisé quand on ne connaissait pas de nom de thème précis). Or ce
pattern remonte quasi systématiquement des **compilations génériques**
("Movie Sound Orchestra", "Hollywood Symphony Orchestra Selected Hits"...)
plutôt que l'enregistrement original — rejetées en masse par le filtre
anti-cover (mot-clé "orchestra" dans le nom d'artiste).

**Nouvelle méthode de vérification** (`core/database.py`, fonctions
`_artist_matches_composer` et `_title_matches_query`) :
1. La query réellement envoyée à Deezer est `f"{clé} {compositeur}"`.
2. Un résultat n'est accepté que si (a) son artiste ne contient pas de
   mot-clé suspect (cover/tribute/orchestra/karaoke/instrumental), **ET**
   (b) le dernier mot du compositeur attendu apparaît dans le nom d'artiste
   retourné (`_artist_matches_composer`), **ET** (c) au moins un mot
   significatif (> 3 caractères, hors mots génériques comme "theme") de la
   clé apparaît dans le titre du morceau retourné (`_title_matches_query`).
3. Le check (b) seul ne suffit pas : un compositeur prolifique (ex: Lalo
   Schifrin) peut avoir des dizaines de morceaux sans rapport sur Deezer —
   sans le check (c) sur le titre, une recherche "Bullitt Theme Lalo
   Schifrin" pouvait renvoyer un tout autre morceau de Schifrin
   ("The James Bond Theme (Live)"), composeur correct mais film faux.

**Comment les clés/compositeurs sont maintenant déterminés** : plus jamais de
mémoire/devinette seule. Chaque entrée est vérifiée par recherche réelle sur
l'API Deezer (`https://api.deezer.com/search?q=...`) avant d'être écrite dans
`genres.py`, pour confirmer que l'artiste et le titre exacts existent
vraiment dans le catalogue. Certaines entrées sans résultat fiable trouvé
après plusieurs tentatives de reformulation ont été **supprimées** plutôt que
laissées avec une query qui échouera systématiquement (ex: Speed, Point
Break, Dirty Dozen dans `action`).

**Tracker de migration** (sous-genres passés du format v1 `{query: titre}`
au format v2 `{query: (titre, compositeur)}`, avec vérification live) :

| Sous-genre | Genre | Statut | Entrées (avant → après) |
|---|---|---|---|
| action | movies | ✅ migré + vérifié | 34 → 31 |
| aventure | movies | ✅ migré + vérifié | 24 → 24 |
| sci_fi | movies | ✅ migré + vérifié | 35 → 34 |
| casse | movies | ✅ migré + vérifié | 13 → 10 |
| catastrophe | movies | ✅ migré + vérifié | 19 → 17 |
| comedie | movies | ✅ migré + vérifié | 29 → 20 |
| criminel | movies | ✅ migré + vérifié | 19 → 14 |
| drame | movies | ✅ migré + vérifié | 38 → 33 |
| fantasy | movies | ✅ migré + vérifié | 23 → 23 |
| horreur | movies | ✅ migré + vérifié | 26 → 23 |
| historique | movies | ✅ migré + vérifié | 29 → 26 |
| peplum | movies | ✅ migré + vérifié | 14 → 14 |
| noel | movies | ✅ migré + vérifié | 11 → 9 |
| romance | movies | ✅ migré + vérifié | 29 → 25 |
| thriller | movies | ✅ migré + vérifié | 28 → 22 |
| western | movies | ✅ migré + vérifié | 22 → 19 |
| musical | movies | ✅ migré + vérifié | 26 → 26 |
| series_sci_fi | series | ✅ migré + vérifié | 24 → 22 |
| series_fantasy | series | ✅ migré + vérifié | 16 → 13 |
| series_horreur | series | ✅ migré + vérifié | 11 → 10 |
| series_thriller_policier | series | ✅ migré + vérifié | 26 → 17 |
| series_drame | series | ✅ migré + vérifié | 27 → 19 |
| series_comedie_sitcom | series | ✅ migré + vérifié | 19 → 12 |
| series_animation | series | ✅ migré + vérifié | 17 → 11 |

**Migration terminée (12/08/2026)** : 24/24 sous-genres migrés et vérifiés
(17 movies + 7 series). Movies : 419 → 370 entrées. Series : 140 → 104
entrées. Total : 559 → 474 entrées, 100% vérifiées en direct sur l'API
Deezer (artiste + titre du morceau).

Le shim de compatibilité v1/v2 a été retiré de `import_movies_series`
(`core/database.py`) puisque tous les sous-genres sont maintenant au format
v2 `{query: (titre, compositeur)}`.
