from unittest.mock import patch
from k8s_upgrade_analyzer.collector.cluster_info import collect


def _mock_run(cmd, kubeconfig=None):
    return f"mock output for: {cmd}", None


def test_collect_returns_snapshot():
    with patch("k8s_upgrade_analyzer.collector.cluster_info._run", side_effect=_mock_run):
        snapshot = collect()
    assert snapshot.kubectl_version.startswith("mock output")
    assert snapshot.errors == []


def test_collect_captures_errors():
    def run_with_error(cmd, kubeconfig=None):
        if "top" in cmd:
            return "", "metrics-server not available"
        return "ok", None

    with patch("k8s_upgrade_analyzer.collector.cluster_info._run", side_effect=run_with_error):
        snapshot = collect()

    assert any("metrics-server" in e for e in snapshot.errors)
