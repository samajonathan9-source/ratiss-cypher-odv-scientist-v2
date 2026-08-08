# RATISS CYPHER ODV SCIENTIST V2

**Agent scientifique autonome RATISS V9 Aeon Prime** — interface sécurisée multi-utilisateurs déployée sur Hugging Face Spaces (mode Docker).

> Propriété Intellectuelle : **JohnKing0 & Architecte Jonathan Evina**
> ORCID : [0009-0000-4092-5313](https://orcid.org/0009-0000-4092-5313) — DOI : [10.17605/OSF.IO/6JZMB](https://doi.org/10.17605/OSF.IO/6JZMB)

---

## 1. Architecture

Le système est organisé en quatre couches principales. La couche d'**interface** repose sur Chainlit et expose une conversation en français avec une boucle agentique REACT. La couche **LLM** interroge NVIDIA **Nemotron 3 Ultra** (550B A55B, version `:free`) via OpenRouter, avec `openrouter/auto` en repli configuré par la variable `OPENROUTER_MODEL`. La couche **cerveau scientifique** contient le noyau RATISS : diagonalisation de Lanczos (modèle t-J exact), homologie persistante (nombres de Betti) sur les structures protéiques, reçus ZK-STARK, et le routage sémantique TransDIPL'Y avec le Panthéon des 30 Pairs. Enfin, la couche **sécurité native** garantit des sessions UUID isolées avec workspaces dédiés et un stockage des jetons uniquement en hachage SHA-256.

| Dossier | Rôle |
|---|---|
| `app.py` | Interface Chainlit + boucle agentique REACT (point d'entrée HF Spaces) |
| `src/ratiss_v9_aeon_prime/` | Cerveau scientifique RATISS (physique, topologie, agent, CLI) |
| `src/connectors/` | Connecteurs quantiques (IBM Quantum, Quandela, PennyLane, fallback CPU) |
| `security/` | Gestionnaire de sessions (UUID, SQLite, isolation) et coffre-fort de jetons SHA-256 |
| `scripts/` | `import_skill.py` (import de skills GitHub) et `align_agent.py` (alignement Nemotron) |
| `docs/` | Mémoire agentique `AGENTS.md` |

## 2. Sécurité native

Chaque utilisateur obtient à la connexion une **session UUID4** avec un jeton d'accès fort qui n'est remis qu'une seule fois et jamais stocké en clair : seul son **hachage SHA-256** est persisté dans `data/sessions.db`. Les workspaces sont strictement isolés (`workspace/{session_id}/`) et les sessions expirent par défaut après 24 heures (configurable via `SESSION_TTL_HOURS`). Les clés API sont vérifiées par comparaison de hachage (`security/token_vault.py`) et ne transitent jamais dans les logs ou les réponses de l'agent.

## 3. Déploiement Hugging Face Spaces

1. Créez un nouveau Space en mode **Docker** sur [huggingface.co/spaces](https://huggingface.co/spaces).
2. Reliez le dépôt GitHub `ratiss-cypher-odv-scientist-v2` (Settings → Linked resources).
3. Ajoutez les **secrets** du dépôt (Settings → Repository secrets) :

| Secret | Valeur |
|---|---|
| `OPENROUTER_API_KEY` | Clé OpenRouter (commençant par `sk-or-v1-`) |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `CHAINLIT_AUTH_SECRET` | Secret JWT (générable avec `chainlit create-secret`) |
| `IBM_QUANTUM_TOKEN` | (optionnel) Jeton IBM Quantum |
| `QUANDELA_API_TOKEN` | (optionnel) Jeton Quandela |

4. L'espace démarre automatiquement sur le port 7860.

## 4. Utilisation locale

```bash
# Configuration
cp .env.example .env      # éditez .env avec vos clés
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Alignement de l'agent (vérifie clés + cerveau + Nemotron)
python3 scripts/align_agent.py --full

# Lancement de l'interface
CHAINLIT_AUTH_SECRET=$(chainlit create-secret) chainlit run app.py --port 8000
```

## 5. Outils scientifiques exposés

| Outil | Description |
|---|---|
| `solve_quantum` | Pipeline RATISS complet : Lanczos t-J, homologie persistante, reçu ZK-STARK |
| `route_task` | Routage sémantique TransDIPL'Y (domaine, solveur, pairs experts) |
| `pdb_meta` | Métadonnées RCSB PDB d'une structure protéique |
| `health` | Diagnostic du nœud (RAM, Memory Guard 7.5 Go) |

## 6. Import de nouvelles compétences

```bash
python3 scripts/import_skill.py https://github.com/owner/repo.git [--name nom]
```

Le script clone le dépôt dans `skills/`, détecte le point d'entrée, installe les dépendances et génère un `skill_config.json` standardisé consommé par l'orchestrateur.
