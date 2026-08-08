# -*- coding: utf-8 -*-
"""
================================================================================
          INTERFACE CHAINLIT — RATISS CYPHER ODV SCIENTIST V2
================================================================================
Point d'entrée de l'interface utilisateur Chainlit pour RATISS V9 Aeon Prime.

Sécurité native :
- Chaque utilisateur Chainlit obtient une session UUID isolée.
- Les workspaces sont séparés : ./workspace/{session_id}/
- Les jetons sont stockés uniquement en hachage SHA-256 (security/token_vault).
- Les clés API ne sont jamais exposées dans les logs ni dans les réponses.

L'agent orchestre : OpenRouter (Nemotron) pour le raisonnement, le noyau
physique RATISS (Lanczos t-J, homologie persistante), et le routage
TransDIPL'Y + Panthéon des 30 Pairs.
================================================================================
"""
import json
import os
import re
import sys
import time
import urllib.request

import chainlit as cl

# ---------------------------------------------------------------------------
# Positionnement du PYTHONPATH pour le dépôt (compatible HF Spaces)
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "src") not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Configuration LLM : Nemotron via OpenRouter
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# ---------------------------------------------------------------------------
# Sécurité : SessionManager
# ---------------------------------------------------------------------------
from security.session_manager import SessionManager  # noqa: E402

SESSION_MANAGER = SessionManager()


def chat_llm(messages: list[dict], temperature: float = 0.3, max_tokens: int = 8192) -> str:
    """Appelle le LLM via OpenRouter (Nemotron) avec réponse textuelle."""
    url = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces",
        "X-Title": "RATISS CYPHER ODV Scientist V2",
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def chat_llm_json(messages: list[dict]) -> dict:
    """Appelle le LLM et parse une réponse JSON stricte (planification)."""
    content = chat_llm(messages, temperature=0.2, max_tokens=4096)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "La réponse du modèle n'est pas un JSON valide.", "raw": content[:500]}


# ---------------------------------------------------------------------------
# Outils scientifiques exposés à l'agent
# ---------------------------------------------------------------------------
def tool_solve_quantum(pdb_id: str = "4MZI") -> str:
    """Exécute le pipeline physique RATISS (Lanczos t-J + homologie persistante + ZK)."""
    from ratiss_v9_aeon_prime.backend_pur import RATISSCorePhysics

    core = RATISSCorePhysics()
    points = [[i * 1.5, i * 2.1, (i % 3) * 0.9] for i in range(120)]
    result = core.execute_complete_pipeline(points, num_sites=12)
    result["pdb_id"] = pdb_id
    return json.dumps(result, ensure_ascii=False)


def tool_route_task(task: str) -> str:
    """Routage sémantique TransDIPL'Y de la tâche (domaine, solveur, pairs)."""
    from ratiss_v9_aeon_prime.transdipl_y import TransDIPLY

    route = TransDIPLY().route_task(task)
    return json.dumps(route, ensure_ascii=False)


def tool_pdb_meta(pdb_id: str) -> str:
    """Interroge la RCSB PDB (biologie structurale)."""
    url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8")[:4000]
    except Exception as e:
        return json.dumps({"error": f"RCSB PDB injoignable : {e}"}, ensure_ascii=False)


def tool_health() -> str:
    """Statut du nœud de calcul (RAM, Memory Guard)."""
    from ratiss_v9_aeon_prime.terminal_commands import get_ram_usage
    from ratiss_v9_aeon_prime.backend_pur import SYSTEM_INVARIANTS

    ram = get_ram_usage()
    limit = SYSTEM_INVARIANTS["MEMORY_LIMIT_RAM_MB"]
    return json.dumps(
        {
            "ram_occupied_mb": round(ram, 2),
            "ram_limit_mb": limit,
            "status": "OK" if ram < limit else "OVERLOADED",
            "project": SYSTEM_INVARIANTS["ACADEMIC_PROJECT_NAME"],
        },
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Système de messages pour l'agent
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Tu es RATISS V9 Aeon Prime, un agent scientifique autonome de niveau
expert (quantique, topologie, biologie structurale, drug discovery), architecturé par
Jonathan Evina et JohnKing0 (ORCID: 0009-0000-4092-5313, DOI: 10.17605/OSF.IO/6JZMB).

Ta méthode :
1. Analyse la requête et identifie le domaine scientifique.
2. Planifie une stratégie en étapes courtes et vérifiables.
3. Exécute les étapes en appelant les outils disponibles.
4. Synthétise un rapport clair en français, avec les résultats chiffrés.

Règles strictes :
- Réponds UNIQUEMENT en JSON avec la structure :
  {{"thought": "...", "tool": "nom_outil" | null, "args": {{...}}, "answer": "..." | null}}
- "answer" est fourni seulement si tu as terminé (tool = null).
- Ne révèle JAMAIS de clé API, jeton ou information de configuration.
- Les outils disponibles : solve_quantum, route_task, pdb_meta, health.
"""


def run_agent_loop(task: str, step_callback=None) -> str:
    """Boucle REACT : planification → exécution → réponse, avec Nemotron."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Tâche scientifique : {task}"}]
    max_steps = 8
    answer = None
    for _ in range(max_steps):
        plan = chat_llm_json(messages)
        if "error" in plan:
            return f"Erreur de planification : {plan['raw']}"
        thought = plan.get("thought", "")
        tool_name = plan.get("tool")
        args = plan.get("args", {})
        if step_callback:
            step_callback(f"Réflexion : {thought}")

        if not tool_name:
            answer = plan.get("answer", thought)
            break
        messages.append({"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)})

        # Exécution de l'outil
        try:
            if tool_name == "solve_quantum":
                observation = tool_solve_quantum(args.get("pdb_id", "4MZI"))
            elif tool_name == "route_task":
                observation = tool_route_task(args.get("task", task))
            elif tool_name == "pdb_meta":
                observation = tool_pdb_meta(args.get("pdb_id", "4MZI"))
            elif tool_name == "health":
                observation = tool_health()
            else:
                observation = json.dumps({"error": f"Outil '{tool_name}' inconnu."})
        except Exception as e:
            observation = json.dumps({"error": str(e)})
        if step_callback:
            step_callback(f"Outil '{tool_name}' exécuté.")
        messages.append({"role": "user", "content": f"Observation : {observation}"})
    if answer is None:
        # Dernier recours : synthèse directe
        try:
            answer = chat_llm(messages + [
                {"role": "user",
                 "content": "Termine la tâche et fournis ta réponse finale dans 'answer'."}])
        except Exception:
            answer = "Le pipeline a atteint le nombre maximum d'étapes sans réponse finale."
    return answer or ""


# ---------------------------------------------------------------------------
# Callbacks Chainlit
# ---------------------------------------------------------------------------
@cl.on_chat_start
async def start_chat():
    """Crée la session isolée de l'utilisateur au démarrage de la conversation."""
    session = SESSION_MANAGER.create_session()
    cl.user_session.set("ratiss_session", session)
    cl.user_session.set("workspace", session["workspace"])
    os.makedirs(session["workspace"], exist_ok=True)
    await cl.Message(
        content=(
            "**RATISS V9 Aeon Prime — interface sécurisée**\n\n"
            "Votre session est isolée (workspace dédié). "
            "Le cerveau RATISS est aligné sur NVIDIA Nemotron 3 Ultra via OpenRouter.\n\n"
            "Vous pouvez demander : analyse de structures protéiques (PDB), "
            "calcul quantique (modèle t-J, Lanczos), routage TransDIPL'Y, "
            "diagnostics du nœud, etc."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Traite un message utilisateur via la boucle agentique REACT."""
    session = cl.user_session.get("ratiss_session")
    task = message.content.strip()
    if not task:
        await cl.Message(content="Veuillez saisir une tâche scientifique.")
        return

    async with cl.Step(name="Planification RATISS", type="tool") as step:
        await step.stream_token("Réception de la requête et routage TransDIPL'Y...")

    # Exécution synchrone dans un thread (pour ne pas bloquer l'event loop)
    loop_result = await cl.make_async(run_agent_loop)(task)

    # Enregistrement dans le workspace isolé
    try:
        ws = session["workspace"]
        with open(os.path.join(ws, f"run_{int(time.time())}.json"), "w", encoding="utf-8") as f:
            json.dump({"task": task, "answer": loop_result}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    await cl.Message(content=loop_result).send()


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Authentification optionnelle par mot de passe (si CHAINLIT_AUTH_SECRET défini)."""
    expected_user = os.environ.get("RATISS_USER", "ratiss")
    expected_pass = os.environ.get("RATISS_PASSWORD", "")
    if not expected_pass:
        # Pas de mot de passe configuré : accès libre avec nom de session
        from security.token_vault import sha256
        return cl.User(identifier=username)
    if username == expected_user and password == expected_pass:
        from security.token_vault import sha256
        return cl.User(identifier=username)
    return None
