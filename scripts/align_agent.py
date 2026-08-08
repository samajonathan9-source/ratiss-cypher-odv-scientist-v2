#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          ALIGNEUR D'AGENT — RATISS CYPHER ODV V2
================================================================================
1. Vérifie la présence des clés API requises (via variables d'environnement).
2. Configure l'agent pour utiliser Nemotron via OpenRouter.
3. Vérifie l'intégrité du skill principal RATISS (cerveau).
4. Teste l'enchaînement complet : requête → planification → exécution → réponse.

Usage :
    python3 scripts/align_agent.py [--full]
================================================================================
"""
import argparse
import json
import os
import sys
import time

# On positionne la racine du dépôt dans PYTHONPATH
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
os.environ.setdefault("SESSIONS_DB_PATH", os.path.join(ROOT, "data", "sessions.db"))
os.environ.setdefault("TOKEN_VAULT_DB_PATH", os.path.join(ROOT, "data", "tokens.db"))

REQUIRED_KEYS = [
    "OPENROUTER_API_KEY",
]

OPTIONAL_KEYS = [
    "IBM_QUANTUM_TOKEN",
    "QUANDELA_API_TOKEN",
]

NEMOTRON_MODEL_FREE = "nvidia/nemotron-3-ultra-550b-a55b:free"
NEMOTRON_MODEL_AUTO = "openrouter/auto"


def check_keys() -> dict:
    """Vérifie la présence des clés API (jamais affichées en clair)."""
    report = {"required": {}, "optional": {}}
    missing = []
    for key in REQUIRED_KEYS:
        present = bool(os.environ.get(key))
        report["required"][key] = "present" if present else "MISSING"
        if not present:
            missing.append(key)
    for key in OPTIONAL_KEYS:
        report["optional"][key] = "present" if os.environ.get(key) else "absent"

    # Enregistrer les hachages des clés disponibles dans le coffre-fort
    try:
        from security.token_vault import TokenVault, sha256
        for key in REQUIRED_KEYS + OPTIONAL_KEYS:
            val = os.environ.get(key)
            if val:
                TokenVault.register(key, val)
        report["vault"] = TokenVault.registered_services()
    except Exception as e:
        report["vault"] = f"error: {e}"

    return report, missing


def check_ratiss_core() -> dict:
    """Vérifie que le cerveau RATISS est importable et fonctionnel."""
    report = {"importable": False, "modules": {}}
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    modules = {
        "backend_pur": "ratiss_v9_aeon_prime.backend_pur",
        "transdipl_y": "ratiss_v9_aeon_prime.transdipl_y",
        "agentic_light": "ratiss_v9_aeon_prime.agentic_light",
        "file_manager": "ratiss_v9_aeon_prime.file_manager",
    }
    ok = True
    for label, modpath in modules.items():
        try:
            __import__(modpath)
            report["modules"][label] = "OK"
        except Exception as e:
            report["modules"][label] = f"ERREUR: {e}"
            ok = False
    report["importable"] = ok
    return report


def test_pipeline(task: str = None) -> dict:
    """Teste la chaîne requête → planification → exécution → réponse."""
    from ratiss_v9_aeon_prime.transdipl_y import TransDIPLY
    from ratiss_v9_aeon_prime.agentic_light import RATISSAgentEngine

    task = task or "Analyse la structure protéique 4MZI et simule son repliement topologique."
    engine = RATISSAgentEngine()
    t0 = time.time()
    result = engine.run_agent(task)
    elapsed = round(time.time() - t0, 2)
    return {
        "task": task,
        "route": result.get("route", {}),
        "tool_executed": result.get("tool_executed", "?"),
        "raw_result_keys": list(result.get("raw_result", {}).keys()) if isinstance(result.get("raw_result"), dict) else str(result.get("raw_result")),
        "elapsed_seconds": elapsed,
        "success": bool(result.get("raw_result")),
    }


def main():
    parser = argparse.ArgumentParser(description="Aligner l'agent RATISS sur Nemotron via OpenRouter.")
    parser.add_argument("--full", action="store_true", help="Exécuter aussi le test de pipeline complet")
    args = parser.parse_args()

    print("=" * 72)
    print("   ALIGN_AGENT — RATISS CYPHER ODV SCIENTIST V2")
    print("=" * 72)

    # 1. Vérification des clés API
    report, missing = check_keys()
    print("\n[1] CLÉS API :")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    if missing:
        print(f"\n[ERREUR] Clés manquantes : {', '.join(missing)}")
        print("Définissez-les en variables d'environnement ou dans le fichier .env")
        sys.exit(1)

    # 2. Configuration Nemotron
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_MODEL", NEMOTRON_MODEL_FREE)
    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    os.environ.setdefault("OPENROUTER_MODEL", model)
    os.environ.setdefault("OPENROUTER_BASE_URL", base_url)
    print(f"\n[2] CONFIGURATION LLM :")
    print(f"    Modèle      : {model}")
    print(f"    Base URL    : {base_url}")
    print(f"    Clé         : present (hachée dans le coffre-fort)")

    # 3. Intégrité du cerveau RATISS
    core = check_ratiss_core()
    print(f"\n[3] CERVEAU RATISS : importable = {core['importable']}")
    for m, s in core["modules"].items():
        print(f"    {m:15s} -> {s}")
    if not core["importable"]:
        print("\n[ERREUR] Le cerveau RATISS n'est pas entièrement importable.")
        sys.exit(1)

    # 4. Test de pipeline (optionnel / --full)
    if args.full:
        print("\n[4] TEST DE PIPELINE (requête → planification → exécution → réponse) :")
        try:
            test = test_pipeline()
            print(json.dumps(test, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            print(f"    Échec du test de pipeline : {e}")
            sys.exit(1)
    else:
        print("\n[4] Test de pipeline complet : omis (utiliser --full pour l'exécuter)")

    print("\n" + "=" * 72)
    print("   ALIGNEMENT RÉUSSI — l'agent est prêt à utiliser Nemotron.")
    print("=" * 72)


if __name__ == "__main__":
    main()
