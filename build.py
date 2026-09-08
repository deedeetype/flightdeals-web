#!/usr/bin/env python3
"""build.py — génère la page HTML avec les données du dernier scan.

Usage:
  python3 build.py                          # lit data/latest-scan.json
  python3 build.py --input data.json --output dist/index.html

Le script:
  1. Lit le JSON du scan (depuis --input ou data/latest-scan.json)
  2. Lit le template index.html
  3. Injecte le JSON dans une balise <script> avant le fetch
  4. Écrit le résultat (défaut: dist/index.html)

Résultat: une page 100% autonome — pas de fetch réseau, pas de serveur.
Le JSON contient déjà les top deals si aucune aubaine n'est détectée.
Parfait pour Netlify: on dépose dist/ et c'est tout.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_INPUT  = HERE / "data" / "latest-scan.json"
DEFAULT_OUTPUT = HERE / "dist" / "index.html"
TEMPLATE       = HERE / "index.html"

INJECT_MARKER = "// ======================== LOAD ========================"


def build(input_path: Path, output_path: Path) -> None:
    scan_json = input_path.read_text(encoding="utf-8")
    scan = json.loads(scan_json)  # valide

    template = TEMPLATE.read_text(encoding="utf-8")
    inject = f"window.__SCAN_DATA__ = {json.dumps(scan, ensure_ascii=False)};\n"
    html = template.replace(INJECT_MARKER, inject + INJECT_MARKER, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    n = len(scan.get("deals", []))
    label = "top deals" if scan.get("is_top_deals") else "aubaines"
    print(f"[build] {input_path.name} -> {output_path}")
    print(f"        {n} {label} embarqués dans index.html")
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