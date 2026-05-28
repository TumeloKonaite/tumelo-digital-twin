import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class PromptResources:
    linkedin: str
    summary: str
    facts: dict[str, Any]
    style: str


def load_resources(data_dir: Path | None = None) -> PromptResources:
    resolved_data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR

    try:
        reader = PdfReader(str(resolved_data_dir / "linkedin.pdf"))
        linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text
    except FileNotFoundError:
        linkedin = "LinkedIn profile not available"

    with open(resolved_data_dir / "summary.txt", "r", encoding="utf-8") as f:
        summary = f.read()

    with open(resolved_data_dir / "style.txt", "r", encoding="utf-8") as f:
        style = f.read()

    with open(resolved_data_dir / "facts.json", "r", encoding="utf-8") as f:
        facts = json.load(f)

    return PromptResources(
        linkedin=linkedin,
        summary=summary,
        facts=facts,
        style=style,
    )


default_resources = load_resources()
linkedin = default_resources.linkedin
summary = default_resources.summary
facts = default_resources.facts
style = default_resources.style
