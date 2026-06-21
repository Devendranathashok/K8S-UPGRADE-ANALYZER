FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml setup.py ./
COPY k8s_upgrade_analyzer/ ./k8s_upgrade_analyzer/
COPY prompts/ ./prompts/

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["k8s-upgrade-analyzer"]
