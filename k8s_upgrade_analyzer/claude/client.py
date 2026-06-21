import os
from pathlib import Path
import anthropic
from k8s_upgrade_analyzer.models import ClusterSnapshot


_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "system_prompt.md"

_DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 16000


def _load_prompt(
    source_version: str,
    target_version: str,
    snapshot: ClusterSnapshot,
) -> str:
    template = _PROMPT_PATH.read_text()
    return template.format(
        source_version=source_version,
        target_version=target_version,
        kubectl_version=snapshot.kubectl_version or "(not available)",
        cluster_info=snapshot.cluster_info or "(not available)",
        nodes=snapshot.nodes or "(not available)",
        namespaces=snapshot.namespaces or "(not available)",
        api_resources=snapshot.api_resources or "(not available)",
        api_services=snapshot.api_services or "(not available)",
        all_resources=snapshot.all_resources or "(not available)",
        deployments=snapshot.deployments or "(not available)",
        statefulsets=snapshot.statefulsets or "(not available)",
        daemonsets=snapshot.daemonsets or "(not available)",
        jobs=snapshot.jobs or "(not available)",
        cronjobs=snapshot.cronjobs or "(not available)",
        crds_list=snapshot.crds_list or "(not available)",
        crds_yaml=snapshot.crds_yaml or "(not available)",
        validating_webhooks=snapshot.validating_webhooks or "(not available)",
        mutating_webhooks=snapshot.mutating_webhooks or "(not available)",
        nodes_yaml=snapshot.nodes_yaml or "(not available)",
        top_nodes=snapshot.top_nodes or "(not available)",
        top_pods=snapshot.top_pods or "(not available)",
        collection_errors="\n".join(snapshot.errors) if snapshot.errors else "None",
    )


def analyze(
    source_version: str,
    target_version: str,
    snapshot: ClusterSnapshot,
    api_key: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> str:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Set it in your environment or pass --api-key."
        )

    model = model or os.environ.get("CLAUDE_MODEL", _DEFAULT_MODEL)
    prompt = _load_prompt(source_version, target_version, snapshot)

    client = anthropic.Anthropic(api_key=api_key)

    if stream:
        full_text = ""
        with client.messages.stream(
            model=model,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        ) as s:
            for text in s.text_stream:
                print(text, end="", flush=True)
                full_text += text
        print()
        return full_text
    else:
        message = client.messages.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
