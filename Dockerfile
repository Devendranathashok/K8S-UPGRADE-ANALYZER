FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml setup.py ./
COPY k8s_upgrade_analyzer/ ./k8s_upgrade_analyzer/
COPY prompts/ ./prompts/

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["k8s-upgrade-analyzer"]
