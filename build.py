#!/usr/bin/env python3
"""build.py — génère la page HTML avec les données du dernier scan.

Usage:
  python3 build.py                          # lit data/latest-scan.json
  python3 build.py --input data.json --output dist/index.html

Le script:
  1. Lit le JSON du scan (depuis --input ou data/latest-scan.json)
  2. Si pas d'aubaines détectées, lit la DB SQLite et génère des "top deals"
     (les meilleurs prix trouvés par route) pour ne pas afficher une page vide.
  3. Lit le template index.html
  4. Injecte le JSON dans une balise <script> avant le fetch
  5. Écrit le résultat (défaut: dist/index.html)

Résultat: une page 100% autonome — pas de fetch réseau, pas de serveur.
"""
import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_INPUT  = HERE / "data" / "latest-scan.json"
DEFAULT_OUTPUT = HERE / "dist" / "index.html"
TEMPLATE       = HERE / "index.html"
DB_PATH        = HERE.parent / "flightdeals" / "flightdeals.db"

INJECT_MARKER = "// ======================== LOAD ========================"


def top_deals_from_db(db_path: Path, limit: int = 12) -> list[dict]:
    """Quand aucune aubaine n'est détectée, on extrait les meilleurs prix
    par route depuis la DB pour afficher quand même quelque chose."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT route, price, currency, depart_date, return_date,
                  airline, source, deep_link
           FROM observations
           WHERE depart_date IS NOT NULL
           ORDER BY price ASC"""
    ).fetchall()
    conn.close()

    # Un seul deal par corridor (route + depart_date) — le moins cher
    seen = set()
    deals = []
    for r in rows:
        corridor = f"{r['route']}|{r['depart_date']}"
        if corridor in seen:
            continue
        seen.add(corridor)

        # baseline = prix médian de la route (approximatif)
        route_prices = [row["price"] for row in rows if row["route"] == r["route"]]
        route_prices.sort()
        mid = len(route_prices) // 2
        baseline = route_prices[mid] if route_prices else r["price"]
        drop_pct = max(0, (baseline - r["price"]) / baseline) if baseline > 0 else 0

        deals.append({
            "route": r["route"],
            "price": r["price"],
            "currency": r["currency"],
            "baseline": round(baseline, 2),
            "drop_pct": round(drop_pct, 4),
            "z_score": 0.0,
            "depart_date": r["depart_date"],
            "return_date": r["return_date"],
            "airline": r["airline"] or "",
            "sources": [r["source"]] if r["source"] else [],
            "confirmations": 1,
            "confirmed": False,
            "reasons": [f"Prix le plus bas trouvé pour {r['route']}"],
            "deep_link": r["deep_link"] or f"https://www.google.com/travel/flights?q={r['route'].replace('-', '%20')}",
        })
        if len(deals) >= limit:
            break
    return deals


def build(input_path: Path, output_path: Path, db_path: Path) -> None:
    scan = json.loads(input_path.read_text(encoding="utf-8"))

    # Si aucune aubaine détectée, on ajoute les top deals de la DB
    if not scan.get("deals"):
        top = top_deals_from_db(db_path)
        if top:
            scan["deals"] = top
            scan["deals_total"] = len(top)
            scan["deals_new"] = len(top)
            scan["is_top_deals"] = True  # flag pour le frontend

    scan_json = json.dumps(scan, ensure_ascii=False)
    template = TEMPLATE.read_text(encoding="utf-8")

    inject = f"window.__SCAN_DATA__ = {scan_json};\n"
    html = template.replace(INJECT_MARKER, inject + INJECT_MARKER, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    n_deals = len(scan.get("deals", []))
    is_top = scan.get("is_top_deals", False)
    label = "top deals (meilleurs prix)" if is_top else "aubaines"
    print(f"[build] {input_path.name} -> {output_path}")
    print(f"        {n_deals} {label} embarqués dans index.html")
    print(f"        Page autonome prête pour Netlify: {output_path.parent}/")


def main() -> None:
    p = argparse.ArgumentParser(description="Build la page flightdeals-web")
    p.add_argument("--input",  type=Path, default=DEFAULT_INPUT,
                   help="JSON du scan (défaut: data/latest-scan.json)")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                   help="HTML de sortie (défaut: dist/index.html)")
    p.add_argument("--db",     type=Path, default=DB_PATH,
                   help="Chemin vers flightdeals.db (défaut: ../flightdeals/flightdeals.db)")
    args = p.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input introuvable: {args.input}")
    if not TEMPLATE.exists():
        raise SystemExit(f"Template introuvable: {TEMPLATE}")
    build(args.input, args.output, args.db)


if __name__ == "__main__":
    main()