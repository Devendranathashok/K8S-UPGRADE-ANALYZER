import subprocess
from k8s_upgrade_analyzer.models import ClusterSnapshot


def _run(cmd: str, kubeconfig: str | None = None) -> tuple[str, str | None]:
    env = {}
    if kubeconfig:
        env["KUBECONFIG"] = kubeconfig

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    if result.returncode != 0:
        return result.stdout, result.stderr.strip()
    return result.stdout, None


def collect(kubeconfig: str | None = None) -> ClusterSnapshot:
    snapshot = ClusterSnapshot()
    errors: list[str] = []

    steps: list[tuple[str, str]] = [
        ("kubectl_version", "kubectl version"),
        ("cluster_info", "kubectl cluster-info"),
        ("nodes", "kubectl get nodes -o wide"),
        ("namespaces", "kubectl get ns"),
        ("api_resources", "kubectl api-resources"),
        ("api_services", "kubectl get apiservices"),
        ("all_resources", "kubectl get all -A"),
        ("deployments", "kubectl get deploy -A"),
        ("statefulsets", "kubectl get sts -A"),
        ("daemonsets", "kubectl get ds -A"),
        ("jobs", "kubectl get jobs -A"),
        ("cronjobs", "kubectl get cronjobs -A"),
        ("crds_list", "kubectl get crd"),
        ("crds_yaml", "kubectl get crd -o yaml"),
        ("validating_webhooks", "kubectl get validatingwebhookconfigurations"),
        ("mutating_webhooks", "kubectl get mutatingwebhookconfigurations"),
        ("nodes_yaml", "kubectl get nodes -o yaml"),
        ("top_nodes", "kubectl top nodes"),
        ("top_pods", "kubectl top pods -A"),
    ]

    for field, cmd in steps:
        output, err = _run(cmd, kubeconfig)
        setattr(snapshot, field, output)
        if err:
            errors.append(f"{cmd}: {err}")

    snapshot.errors = errors
    return snapshot
