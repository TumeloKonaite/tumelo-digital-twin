from pathlib import Path

from src.app.core.content_paths import resolve_data_dir
from src.app.infrastructure.content import PromptResources, ResourceLoader


def load_resources(data_dir: Path | None = None) -> PromptResources:
    return ResourceLoader(data_dir=resolve_data_dir(data_dir)).load_prompt_resources()
