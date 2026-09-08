# flightdeals-web

Page web statique affichant les **aubaines de vols** détectées par le pipeline
[`flightdeals`](../flightdeals). Conçue pour déploiement **Netlify** — zéro
serveur, zéro dépendance JS.

## Aperçu

Chaque aubaine s'affiche sous forme de **carte** avec :

- 📸 **photo placeholder** (via Picsum, changera par de vraies photos plus tard)
- 🏷️ **prix trouvé** vs **prix moyen** (barré), avec barre de comparaison visuelle
- 📅 **dates** aller / retour
- ✈️ **compagnie aérienne**
- 🔍 **sources** ayant détecté l'offre (badge ✅ si confirmée multi-source)
- 💰 **économie potentielle** en $
- 🔗 **lien de réservation** (Google Flights / Aviasales)

Le tout dans un design sombre, responsive, qui se charge instantanément (les
données sont **embarquées dans le HTML** au build — pas de fetch réseau).

## Structure

```
flightdeals-web/
├── index.html              ← template (design + JS de rendu)
├── data/
│   └── latest-scan.json    ← JSON du dernier scan (entrée du build)
├── build.py                ← script: injecte le JSON dans index.html -> dist/
├── dist/                   ← sortie du build (servi par Netlify)
│   └── index.html          ← page autonome avec données embarquées
├── netlify.toml            ← config Netlify (build + publish)
├── package.json
└── README.md
```

## Build

```bash
# 1. Générer le JSON du scan depuis le pipeline
cd ../flightdeals
python3 -m flightdeals.cli scan --config config.toml --format json > ../flightdeals-web/data/latest-scan.json

# 2. Construire la page
cd ../flightdeals-web
python3 build.py

# 3. Prévisualiser localement
npm run serve    # ou: python3 -m http.server 8080 --directory dist
# → http://localhost:8080
```

## Déploiement Netlify

### Option A — Drag & drop
1. `python3 build.py`
2. Glisser le dossier `dist/` sur https://app.netlify.com/drop

### Option B — Git (auto-déploiement)
1. Push ce repo sur GitHub
2. Netlify → "Add new site" → "Import from Git"
3. Config détectée automatiquement via `netlify.toml` :
   - **Build command**: `python3 build.py`
   - **Publish directory**: `dist`
4. Déploiement automatique à chaque push

### Option C — CLI Netlify
```bash
npm i -g netlify-cli
python3 build.py
netlify deploy --dir=dist --prod
```

## Workflow continu (optionnel)

Pour un site qui se met à jour automatiquement :

1. **GitHub Action** ou **cron** qui lance le pipeline + build + push sur la
   branche `main` → Netlify re-déploie.
2. Ou **Netlify scheduled function** qui exécute le scan et rebuild.

## Personnalisation

- **Photos** : remplacer Picsum par de vraies photos de destinations dans
  `ROUTE_META` (index.html, ligne ~230).
- **Routes** : ajouter des entrées dans `ROUTE_META` pour nouvelles destinations.
- **Compagnies** : étendre `AIRLINE_NAMES` pour afficher le nom complet.
- **Couleurs** : éditer les variables CSS `:root` en haut de `index.html`.
- **Seuils de détection** : voir `../flightdeals/config.toml` `[detector]`.

## Tech

- HTML/CSS/JS vanilla — aucun framework, aucune dépendance
- Python 3.11+ pour le build (`json`, `pathlib` — stdlib uniquement)
- Données embarquées au build → page 100% statique
- Compatible Netlify, Vercel, Cloudflare Pages, GitHub Pages, etc.