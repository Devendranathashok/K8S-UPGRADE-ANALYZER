# K8s Upgrade Analyzer

A CLI tool that connects to a live Kubernetes cluster, collects its full state, and uses **Claude AI** to produce an exhaustive upgrade feasibility and risk assessment report.

It answers: *"Can I safely upgrade my cluster from version X to version Y — and what will break if I do?"*

---

## How It Works

```
Live Cluster ──► kubectl collect ──► Claude AI ──► Markdown Report
```

1. **Collect** — runs `kubectl` commands to gather nodes, workloads, CRDs, webhooks, API resources, and resource metrics
2. **Analyze** — sends the full cluster snapshot to Claude with a structured prompt covering 16 assessment areas
3. **Report** — saves a Markdown + JSON report to disk

---

## Assessment Coverage

The generated report covers:

| Area | What Is Checked |
|---|---|
| API Removals | Removed APIs in use (CRITICAL) |
| Deprecated APIs | APIs deprecated in target version |
| CRD Compatibility | Per-CRD break risk |
| Controllers & Operators | Version support range, upgrade timing |
| Admission Webhooks | Risk of blocking deployments post-upgrade |
| Networking | CNI, ingress, network policy compatibility |
| Storage | StorageClass, PVC, CSI driver risks |
| Security | PSP removal, RBAC changes, enforcement shifts |
| Runtime | CRI and OS compatibility |
| Resource Pressure | OOMKill/eviction risk during rolling upgrade |
| Upgrade Simulation | Per-area pass/warn/fail across control plane, nodes, APIs |
| Failure Scenarios | 10 failure scenario answers (YES/NO + reason) |
| Risk Matrix | Severity table across all areas |
| Readiness Score | 0–100 readiness + confidence score |
| Executive Summary | Decision, critical issues, required actions, upgrade order |

---

## Tool Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| CLI framework | [Click](https://click.palletsprojects.com/) |
| AI model | [Claude](https://www.anthropic.com/) via Anthropic SDK |
| Terminal output | [Rich](https://github.com/Textualize/rich) |
| Data validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Cluster access | `kubectl` (uses your kubeconfig) |
| Container runtime | Docker / Podman / Colima |
| Kubernetes deploy | Job + RBAC + Secret manifests |

---

## Prerequisites

- Python 3.11+
- `kubectl` configured and pointing at your cluster
- An [Anthropic API key](https://console.anthropic.com/)

---

## Installation

```bash
git clone https://github.com/Devendranathashok/K8S-UPGRADE-ANALYZER.git
cd K8S-UPGRADE-ANALYZER
pip install -e .
```

---

## Configuration

Copy the example env file and set your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
KUBECONFIG=~/.kube/config         # optional, defaults to this
CLAUDE_MODEL=claude-sonnet-4-6    # optional
```

---

## Usage

```bash
k8s-upgrade-analyzer --source <current-version> --target <target-version>
```

**Examples:**

```bash
# Basic usage
k8s-upgrade-analyzer --source 1.27 --target 1.30

# Custom kubeconfig
k8s-upgrade-analyzer --source 1.27 --target 1.30 --kubeconfig ~/.kube/prod.yaml

# Save report to a specific directory
k8s-upgrade-analyzer --source 1.27 --target 1.30 --output-dir ./reports

# Collect cluster data only — skip Claude (useful for debugging)
k8s-upgrade-analyzer --source 1.27 --target 1.30 --dry-run

# Pass API key directly without .env
k8s-upgrade-analyzer --source 1.27 --target 1.30 --api-key sk-ant-xxx
```

**All options:**

| Flag | Description | Default |
|---|---|---|
| `--source` | Current Kubernetes version | required |
| `--target` | Target Kubernetes version | required |
| `--kubeconfig` | Path to kubeconfig file | `~/.kube/config` |
| `--api-key` | Anthropic API key | `ANTHROPIC_API_KEY` env |
| `--model` | Claude model ID | `claude-sonnet-4-6` |
| `--output-dir` | Directory to save reports | `reports/` |
| `--no-stream` | Wait for full response before printing | false |
| `--dry-run` | Collect data only, skip Claude | false |

---

## Output

Reports are automatically saved to the `reports/` directory (or your `--output-dir`):

```
reports/
  assessment_1_31_to_1_32_20240621T103045Z.md    # full Claude analysis (Markdown)
  assessment_1_31_to_1_32_20240621T103045Z.json   # metadata (versions, timestamp)
```

To also capture terminal output to a log file:

```bash
k8s-upgrade-analyzer --source 1.31 --target 1.32 --output-dir ./reports 2>&1 | tee terminal.log
```

> **Kubernetes upgrade path:** Always upgrade **one minor version at a time** (e.g. 1.31 → 1.32, then 1.32 → 1.33). Skipping minor versions is not supported.

---

## Running as a Kubernetes Job

Use this when you want to run the analyzer from inside the cluster itself.

### 1. Create the API key secret

```bash
kubectl create secret generic k8s-upgrade-analyzer-secret \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-xxxxxxxx \
  --namespace default
```

### 2. Create the image pull secret (Docker Hub)

```bash
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<your-dockerhub-username> \
  --docker-password=<your-dockerhub-token> \
  --docker-email=<your-email> \
  --namespace default
```

### 3. Build and push the image

```bash
docker build -t <your-dockerhub-username>/k8s-upgrade-analyzer:v1.0 .
docker push <your-dockerhub-username>/k8s-upgrade-analyzer:v1.0
```

Update the `image:` field in `deploy/job.yaml` to match.

### 4. Apply manifests

```bash
kubectl apply -f deploy/rbac.yaml
kubectl apply -f deploy/job.yaml
```

### 5. View logs

```bash
kubectl logs -f job/k8s-upgrade-analyzer
```

### 6. Copy the report

```bash
POD=$(kubectl get pod -l job-name=k8s-upgrade-analyzer -o name)
kubectl cp $POD:/reports ./reports
```

---

## Project Structure

```
k8s_upgrade_analyzer/
  cli.py                  # entry point and CLI flags
  collector/
    cluster_info.py       # kubectl data collection
  claude/
    client.py             # Anthropic API calls
  reporter/
    report_generator.py   # saves Markdown + JSON reports
  models/
    assessment.py         # Pydantic data models
prompts/
  system_prompt.md        # Claude assessment prompt
deploy/
  rbac.yaml               # ServiceAccount + ClusterRole
  job.yaml                # Kubernetes Job manifest
Dockerfile
```
