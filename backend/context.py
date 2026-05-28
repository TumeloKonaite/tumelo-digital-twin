from datetime import datetime
from pathlib import Path

from src.app.core.content_paths import resolve_data_dir
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.infrastructure.content import ResourceLoader


def build_prompt_context(data_dir: Path | None = None, now: datetime | None = None) -> dict[str, str]:
    return ResourceLoader(data_dir=resolve_data_dir(data_dir)).build_prompt_context(now=now)


def prompt(
    builder: TwinPromptBuilder | None = None,
    now: datetime | None = None,
    data_dir: Path | None = None,
) -> str:
    prompt_builder = builder or TwinPromptBuilder()
    return prompt_builder.build_system_prompt(
        **build_prompt_context(data_dir=data_dir, now=now)
    )
