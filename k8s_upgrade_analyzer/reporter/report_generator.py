import json
from datetime import datetime
from pathlib import Path


def save(
    raw_analysis: str,
    source_version: str,
    target_version: str,
    output_dir: str = "reports",
) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    slug = f"{source_version.replace('.', '_')}_to_{target_version.replace('.', '_')}"
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    md_path = out / f"assessment_{slug}_{ts}.md"
    md_path.write_text(raw_analysis)

    meta = {
        "source_version": source_version,
        "target_version": target_version,
        "generated_at": ts,
        "report_file": str(md_path),
    }
    (out / f"assessment_{slug}_{ts}.json").write_text(
        json.dumps(meta, indent=2)
    )

    return md_path
