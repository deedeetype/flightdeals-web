#!/usr/bin/env python3
"""build.py — génère la page HTML avec les données du dernier scan embarquées.

Usage:
  python3 build.py                          # lit ../flightdeals/scan.json
  python3 build.py --input data.json --output dist/index.html

Le script:
  1. Lit le JSON du scan (depuis --input ou ../flightdeals-web/data/latest-scan.json)
  2. Lit le template index.html
  3. Injecte le JSON dans une balise <script> avant le fetch
  4. Écrit le résultat (défaut: dist/index.html)

Résultat: une page 100% autonome — pas de fetch réseau, pas de serveur.
Parfait pour Netlify: on dépose dist/ et c'est tout.
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_INPUT  = HERE / "data" / "latest-scan.json"
DEFAULT_OUTPUT = HERE / "dist" / "index.html"
TEMPLATE       = HERE / "index.html"

INJECT_MARKER = "// ======================== LOAD ========================"


def build(input_path: Path, output_path: Path) -> None:
    scan_json = input_path.read_text(encoding="utf-8")
    # valide le JSON
    scan = json.loads(scan_json)

    template = TEMPLATE.read_text(encoding="utf-8")

    inject = f"window.__SCAN_DATA__ = {json.dumps(scan, ensure_ascii=False)};\n"
    html = template.replace(INJECT_MARKER, inject + INJECT_MARKER, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    n_deals = len(scan.get("deals", []))
    n_confirmed = sum(1 for d in scan.get("deals", []) if d.get("confirmed"))
    print(f"[build] {input_path.name} -> {output_path}")
    print(f"        {n_deals} aubaines ({n_confirmed} confirmées) embarquées dans index.html")
    print(f"        Page autonome prête pour Netlify: {output_path.parent}/")


def main() -> None:
    p = argparse.ArgumentParser(description="Build la page flightdeals-web")
    p.add_argument("--input",  type=Path, default=DEFAULT_INPUT,
                   help="JSON du scan (défaut: data/latest-scan.json)")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                   help="HTML de sortie (défaut: dist/index.html)")
    args = p.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input introuvable: {args.input}")
    if not TEMPLATE.exists():
        raise SystemExit(f"Template introuvable: {TEMPLATE}")
    build(args.input, args.output)


if __name__ == "__main__":
    main()