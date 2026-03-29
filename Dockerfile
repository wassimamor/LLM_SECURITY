# 1. Utilisation d'une image Python stable
FROM python:3.10-slim

# 2. Variables d'environnement pour la performance
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# 3. Dépendances système minimales (ajout de curl pour le healthcheck)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. ÉTAPE CRUCIALE : Installation de Torch version CPU uniquement
# Cela divise le poids de l'image par 3 et accélère le build !
RUN pip install --upgrade pip && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu

# 5. Copie et installation des autres bibliothèques
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 6. Copie du code source
COPY . .

# Ports pour ton PFA
EXPOSE 8000
EXPOSE 8501