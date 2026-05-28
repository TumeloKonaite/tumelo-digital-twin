from __future__ import annotations

from datetime import datetime

from src.app.domain.twin.prompt_builder import TwinPromptBuilder


def test_build_system_prompt_includes_style_guidance() -> None:
    prompt = TwinPromptBuilder().build_system_prompt(
        style="Use a warm and concise tone."
    )

    assert "Style guidelines:" in prompt
    assert "Use a warm and concise tone." in prompt


def test_format_memory_renders_list_items() -> None:
    rendered = TwinPromptBuilder().format_memory(
        [
            {"content": "User prefers clear explanations."},
            {"content": "User likes backend architecture discussions."},
        ]
    )

    assert "Relevant memory:" in rendered
    assert "- User prefers clear explanations." in rendered
    assert "- User likes backend architecture discussions." in rendered


def test_format_profile_renders_dict_entries() -> None:
    rendered = TwinPromptBuilder().format_profile(
        {
            "name": "Tumelo",
            "role": "AI Engineer",
        }
    )

    assert "User profile:" in rendered
    assert "- name: Tumelo" in rendered
    assert "- role: AI Engineer" in rendered


def test_empty_sections_are_omitted() -> None:
    prompt = TwinPromptBuilder().build_system_prompt(
        profile=None,
        memory=None,
        style=None,
        summary=None,
        linkedin=None,
        contact_links=None,
        current_datetime="",
    )

    assert "User profile:" not in prompt
    assert "Relevant memory:" not in prompt
    assert "Style guidelines:" not in prompt
    assert "For reference, here is the current date and time:" not in prompt


def test_build_system_prompt_preserves_custom_context_sections() -> None:
    prompt = TwinPromptBuilder().build_system_prompt(
        full_name="Tumelo Tshana Konaite",
        name="Tumelo",
        profile="{'role': 'AI Engineer'}",
        profile_heading="Here is some basic information about Tumelo:",
        summary="Builds backend systems.",
        summary_heading="Here are summary notes from Tumelo:",
        linkedin="LinkedIn profile text.",
        linkedin_heading="Here is the LinkedIn profile of Tumelo:",
        style="Confident and concise.",
        style_heading="Here are some notes from Tumelo about their communications style:",
        contact_links="- Email: test@example.com",
        contact_links_heading="Here are direct contact/profile links for Tumelo (share these when asked):",
        current_datetime=datetime(2026, 5, 28, 12, 30, 0),
    )

    assert "# Your Role" in prompt
    assert "Here is some basic information about Tumelo:" in prompt
    assert "Here are summary notes from Tumelo:" in prompt
    assert "Here is the LinkedIn profile of Tumelo:" in prompt
    assert "Here are some notes from Tumelo about their communications style:" in prompt
    assert "Here are direct contact/profile links for Tumelo (share these when asked):" in prompt
    assert "2026-05-28 12:30:00" in prompt
