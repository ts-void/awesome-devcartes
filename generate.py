#!/usr/bin/env python3
"""Erzeugt aus tools.toml die README (GitHub) oder eine Zola-Seite (Blog).

Beispiele:
    python generate.py tools.toml --format readme --lang en --out README.md
    python generate.py tools.toml --format zola --lang de --out content/awesome.md

Benötigt Python 3.11+ (tomllib), keine weiteren Abhängigkeiten.
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path

LANGS = ("en", "de")
CONTENTS = {"en": "Contents", "de": "Inhalt"}


def slug(text: str) -> str:
    """GitHub-kompatibler Anker: klein, Satzzeichen weg, jedes Leerzeichen -> '-'."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return text.replace(" ", "-")


def get(d: dict, key: str, lang: str) -> str:
    return str(d.get(f"{key}_{lang}", "")).strip()


def validate(data: dict) -> list[str]:
    errors = []
    meta = data.get("meta", {})
    for lang in LANGS:
        if not get(meta, "description", lang):
            errors.append(f"[meta] description_{lang} fehlt")
    for cat in data.get("category", []):
        cname = cat.get("name_en") or cat.get("name_de") or "?"
        for lang in LANGS:
            if not get(cat, "name", lang):
                errors.append(f"[{cname}] name_{lang} fehlt")
        for tool in cat.get("tool", []):
            tname = tool.get("name", "?")
            for key in ("name", "url"):
                if not str(tool.get(key, "")).strip():
                    errors.append(f"[{cname}] {tname}: '{key}' fehlt")
            for lang in LANGS:
                if not get(tool, "why", lang):
                    errors.append(f"[{cname}] {tname}: why_{lang} fehlt")
    return errors


def render_categories(data: dict, lang: str) -> str:
    parts = []
    for cat in data.get("category", []):
        parts.append(f"## {get(cat, 'name', lang)}\n")
        for tool in cat.get("tool", []):
            parts.append(f"- [{tool['name']}]({tool['url']}) - {get(tool, 'why', lang)}")
        parts.append("")
    return "\n".join(parts)


def render_readme(data: dict, lang: str) -> str:
    meta = data.get("meta", {})
    lines = [f"# {meta.get('title', 'Awesome List')}\n", f"{get(meta, 'description', lang)}\n"]
    lines.append(f"## {CONTENTS[lang]}\n")
    for cat in data.get("category", []):
        name = get(cat, "name", lang)
        lines.append(f"- [{name}](#{slug(name)})")
    lines.append("")
    lines.append(render_categories(data, lang))
    return "\n".join(lines).rstrip() + "\n"


def render_zola(data: dict, lang: str) -> str:
    meta = data.get("meta", {})
    title = meta.get("title", "Awesome List").replace('"', '\\"')
    desc = get(meta, "description", lang)
    front = f'+++\ntitle = "{title}"\ndescription = "{desc.replace(chr(34), chr(92) + chr(34))}"\n+++\n\n'
    return front + f"{desc}\n\n" + render_categories(data, lang).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="Pfad zur tools.toml")
    parser.add_argument("--format", choices=["readme", "zola"], required=True)
    parser.add_argument("--lang", choices=LANGS, help="Sprache (Standard: en für readme, de für zola)")
    parser.add_argument("--out", type=Path, required=True, help="Ausgabedatei")
    args = parser.parse_args()
    lang = args.lang or ("en" if args.format == "readme" else "de")

    with args.source.open("rb") as f:
        data = tomllib.load(f)

    errors = validate(data)
    if errors:
        print("Validierung fehlgeschlagen:", *errors, sep="\n  - ", file=sys.stderr)
        return 1

    output = render_readme(data, lang) if args.format == "readme" else render_zola(data, lang)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8")
    count = sum(len(c.get("tool", [])) for c in data.get("category", []))
    print(f"{args.out} geschrieben ({count} Tools, {lang})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
