import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from src.app.core.content_paths import (
    LINKEDIN_FILENAME,
    STYLE_FILENAME,
    SUMMARY_FILENAME,
    TWIN_PROFILE_FILENAME,
    resolve_data_dir,
    resolve_data_path,
)


@dataclass(frozen=True)
class PromptResources:
    linkedin: str
    summary: str
    facts: dict[str, Any]
    style: str


def load_resources(data_dir: Path | None = None) -> PromptResources:
    resolved_data_dir = resolve_data_dir(data_dir)

    try:
        reader = PdfReader(str(resolve_data_path(LINKEDIN_FILENAME, resolved_data_dir)))
        linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text
    except FileNotFoundError:
        linkedin = "LinkedIn profile not available"

    with resolve_data_path(SUMMARY_FILENAME, resolved_data_dir).open(
        "r",
        encoding="utf-8",
    ) as f:
        summary = f.read()

    with resolve_data_path(STYLE_FILENAME, resolved_data_dir).open(
        "r",
        encoding="utf-8",
    ) as f:
        style = f.read()

    with resolve_data_path(TWIN_PROFILE_FILENAME, resolved_data_dir).open(
        "r",
        encoding="utf-8",
    ) as f:
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
