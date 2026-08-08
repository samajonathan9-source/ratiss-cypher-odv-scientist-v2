# RATISS CYPHER ODV SCIENTIST V2 — Hugging Face Spaces (mode Docker)
FROM python:3.11-slim

# Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_ANALYTICS_ENABLED=false

WORKDIR /app

# Dépendances système minimales
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends \
        git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Code source
COPY app.py .
COPY src/ src/
COPY security/ security/
COPY scripts/ scripts/
COPY docs/ docs/
COPY skills/ skills/

# Dossiers runtime
RUN mkdir -p data workspace

# Hugging Face Spaces : port 7860
EXPOSE 7860

# Démarrage de l'interface Chainlit
# CHAINLIT_AUTH_SECRET doit être fourni en variable d'environnement (secret HF)
CMD ["sh", "-c", "chainlit run app.py --port 7860 --host 0.0.0.0 --no-cache"]
