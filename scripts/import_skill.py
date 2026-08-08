#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          IMPORTATEUR DE COMPÉTENCES (SKILLS) — RATISS CYPHER ODV V2
================================================================================
Clone un dépôt GitHub dans /skills/, analyse son contenu pour identifier
l'entrée principale (run.py, main.py, app.py, ...), installe ses dépendances
et génère un fichier skill_config.json standardisé pour l'orchestrateur.

Usage :
    python3 scripts/import_skill.py https://github.com/owner/repo.git [--name nom]
================================================================================
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills"))

# Entrées principales candidates, par ordre de priorité
ENTRY_CANDIDATES = [
    "run.py", "main.py", "app.py", "__main__.py",
    "agent.py", "cli.py", "launch.py", "start.py",
]


def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr


def clone_repo(url: str, name: str) -> str:
    """Clone le dépôt dans skills/{name}/."""
    dest = os.path.join(SKILLS_DIR, name)
    if os.path.exists(dest):
        # Mise à jour si déjà cloné
        rc, out, err = run_cmd("git pull", cwd=dest)
        print(f"[import_skill] Dépôt déjà présent, mise à jour : {'OK' if rc == 0 else err.strip()}")
        return dest
    rc, out, err = run_cmd(f"git clone --depth 1 {url} {dest}")
    if rc != 0:
        raise RuntimeError(f"Échec du clone : {err.strip()}")
    print(f"[import_skill] Dépôt cloné dans {dest}")
    return dest


def find_entry_point(dest: str) -> str:
    """Recherche l'entrée principale du dépôt."""
    for candidate in ENTRY_CANDIDATES:
        if os.path.exists(os.path.join(dest, candidate)):
            return candidate
    # Fallback : premier fichier .py à la racine du dépôt
    for f in sorted(os.listdir(dest)):
        if f.endswith(".py") and not f.startswith("_"):
            return f
    return ""


def find_requirements(dest: str) -> str:
    for candidate in ("requirements.txt", "requirements.txt", "pyproject.toml", "Pipfile"):
        if os.path.exists(os.path.join(dest, candidate)):
            return candidate
    return ""


def install_deps(dest: str, req_file: str):
    """Installe les dépendances Python du skill dans l'environnement."""
    if not req_file:
        return
    rc, out, err = run_cmd(f"pip install -r {req_file} -q", cwd=dest)
    print(f"[import_skill] Dépendances ({req_file}) : {'installées' if rc == 0 else 'échec : ' + err.strip()}")


def build_config(url: str, name: str, entry: str, req_file: str) -> dict:
    """Génère la configuration standardisée du skill."""
    return {
        "name": name,
        "source": url,
        "entry_point": entry or None,
        "requirements_file": req_file or None,
        "installed": True,
        "invoke": f"python3 {entry}" if entry else None,
        "notes": "Configuration générée automatiquement par import_skill.py. "
                 "Ajustez 'entry_point' si l'analyse automatique est incorrecte.",
    }


def main():
    parser = argparse.ArgumentParser(description="Importer un skill GitHub dans RATISS.")
    parser.add_argument("repo_url", help="URL du dépôt GitHub à cloner")
    parser.add_argument("--name", help="Nom du skill (défaut : nom du dépôt)", default=None)
    args = parser.parse_args()

    name = args.name or os.path.basename(args.repo_url.rstrip("/").replace(".git", ""))
    os.makedirs(SKILLS_DIR, exist_ok=True)

    dest = clone_repo(args.repo_url, name)
    entry = find_entry_point(dest)
    req_file = find_requirements(dest)
    install_deps(dest, req_file)
    config = build_config(args.repo_url, name, entry, req_file)

    config_path = os.path.join(dest, "skill_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"[import_skill] Configuration enregistrée : {config_path}")
    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
