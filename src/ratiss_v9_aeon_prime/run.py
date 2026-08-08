
# -*- coding: utf-8 -*-
"""
================================================================================
          ORCHESTRATEUR DE DÉMARRAGE ET SERVEUR API — RATISS V9
================================================================================
Propriété Intellectuelle : JohnKing0 & Architecte Jonathan Evina
Version du Système       : RATISS V9 AEON PRIME - INTEGRATED QUANTUM ECOSYSTEM
ID ORCID de l'Auteur     : 0009-0000-4092-5313
Ancrage DOI Académique   : 10.17605/OSF.IO/6JZMB
================================================================================

Ce script est le point d'entrée universel de l'infrastructure RATISS.
Il démarre un serveur d'API REST (FastAPI) pour exposer les solveurs physiques,
topologiques, et le routage transdisciplinaire TransDIPL'Y sur le port 3000.

---
ENDPOINTS MICRO-SERVICES DISPONIBLES :
- GET  /api/health : Vérification de la santé et diagnostics de la RAM.
- POST /api/route  : Soumission d'une tâche textuelle brute au TransDIPL'Y.
- POST /api/solve  : Exécution complète du pipeline quantique et topologique.

================================================================================
"""

import os
import sys
import json
import time

try:
    from fastapi import FastAPI, Body
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# Imports locaux sécurisés
from ratiss_v9_aeon_prime.backend_pur import RATISSCorePhysics, SYSTEM_INVARIANTS
from ratiss_v9_aeon_prime.transdipl_y import TransDIPLY
from ratiss_v9_aeon_prime.agentic_light import RATISSAgentEngine

if FASTAPI_AVAILABLE:
    from ratiss_v9_aeon_prime.file_server import router as file_server_router

    app = FastAPI(
        title="RATISS V9 Aeon Prime Engine API",
        description="Serveur d'orchestration scientifique et physique quantique/topologique.",
        version="9.0.0"
    )

    # Configuration du CORS pour autoriser l'intégration avec le terminal web
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusion du routeur de gestion et conversion de fichiers
    app.include_router(file_server_router)

    # Instances globales de calcul et d'aiguillage
    core_physics = RATISSCorePhysics()
    trans_diply = TransDIPLY()
    agent_engine = RATISSAgentEngine()

    @app.get("/api/health")
    def health_check():
        """Renvoie le statut matériel, logiciel et de la RAM du nœud."""
        from ratiss_v9_aeon_prime.terminal_commands import get_ram_usage
        ram = get_ram_usage()
        limit = SYSTEM_INVARIANTS["MEMORY_LIMIT_RAM_MB"]
        
        return {
            "status": "operational",
            "project": SYSTEM_INVARIANTS["ACADEMIC_PROJECT_NAME"],
            "academic_credits": {
                "orcid": SYSTEM_INVARIANTS["ACADEMIC_ORCID"],
                "doi": SYSTEM_INVARIANTS["ACADEMIC_DOI"]
            },
            "memory_guard": {
                "ram_occupied_mb": round(ram, 2),
                "ram_limit_mb": limit,
                "status": "OK" if ram < limit else "OVERLOADED"
            }
        }

    @app.post("/api/route")
    def route_task(payload: dict = Body(...)):
        """Route sémantiquement une tâche scientifique brute."""
        task_description = payload.get("task", "")
        if not task_description:
            return {"error": "Le paramètre 'task' est requis."}
        return trans_diply.route_task(task_description)

    @app.post("/api/solve")
    def solve_pipeline(payload: dict = Body(...)):
        """Exécute de bout en bout l'analyse physique, topologique et produit un reçu ZK-STARK."""
        pdb_id = payload.get("pdb_id", "4MZI")
        # Simule des coordonnées de repliement atomique
        fake_coords = [[i * 1.2, i * 2.3, (i % 5) * 0.8] for i in range(130)]
        result = core_physics.execute_complete_pipeline(fake_coords, num_sites=12)
        return {
            "pdb_id": pdb_id,
            "pipeline_results": result
        }

    @app.post("/api/agent/run")
    def run_agent_task(payload: dict = Body(...)):
        """Soumet une tâche à l'agent autonome avec boucle REACT et double flux cognitif."""
        task_description = payload.get("task", "")
        if not task_description:
            return {"error": "Le paramètre 'task' est requis."}
        return agent_engine.run_agent(task_description)


def run_standalone_cli():
    """Démarre une simulation interactive CLI locale si FastAPI n'est pas disponible."""
    print("======================================================================")
    print("           RATISS V9 AEON PRIME — EMBEDDED CLI RUNNER")
    print("======================================================================")
    print("[INFO] Librairies FastAPI / Uvicorn non installées dans cette Sandbox.")
    print("[INFO] Lancement du pipeline local autonome de validation...")
    
    physics = RATISSCorePhysics()
    fake_points = [[i * 1.5, i * 2.1, (i % 3) * 0.9] for i in range(100)]
    result = physics.execute_complete_pipeline(fake_points, num_sites=12)
    
    print("\n[RÉSULTATS DU PIPELINE CONVERGÉ] :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("======================================================================")


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        print("[INIT] Démarrage du serveur RATISS V9 Aeon Prime REST API...")
        uvicorn.run(app, host="0.0.0.0", port=3000)
    else:
        run_standalone_cli()
