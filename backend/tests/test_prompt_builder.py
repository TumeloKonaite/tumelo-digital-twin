import os
import unittest
from datetime import datetime


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.domain.twin.prompt_builder import TwinPromptBuilder


class TwinPromptBuilderTestCase(unittest.TestCase):
    def setUp(self):
        self.builder = TwinPromptBuilder()

    def test_build_system_prompt_includes_style(self):
        prompt = self.builder.build_system_prompt(style="Use a warm and concise tone.")

        self.assertIn("Style guidelines:", prompt)
        self.assertIn("Use a warm and concise tone.", prompt)

    def test_format_memory_renders_list_items(self):
        memory = [
            {"content": "User prefers clear explanations."},
            {"content": "User likes backend architecture discussions."},
        ]

        rendered = self.builder.format_memory(memory)

        self.assertIn("Relevant memory:", rendered)
        self.assertIn("- User prefers clear explanations.", rendered)
        self.assertIn("- User likes backend architecture discussions.", rendered)

    def test_format_profile_renders_dict(self):
        profile = {
            "name": "Tumelo",
            "role": "AI Engineer",
        }

        rendered = self.builder.format_profile(profile)

        self.assertIn("User profile:", rendered)
        self.assertIn("- name: Tumelo", rendered)
        self.assertIn("- role: AI Engineer", rendered)

    def test_empty_values_are_omitted(self):
        prompt = self.builder.build_system_prompt(
            profile=None,
            memory=None,
            style=None,
        )

        self.assertNotIn("Style guidelines:", prompt)
        self.assertNotIn("Relevant memory:", prompt)
        self.assertNotIn("User profile:", prompt)

    def test_build_system_prompt_preserves_existing_context_sections(self):
        prompt = self.builder.build_system_prompt(
            full_name="Tumelo M",
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

        self.assertIn("# Your Role", prompt)
        self.assertIn("Here is some basic information about Tumelo:", prompt)
        self.assertIn("Here are summary notes from Tumelo:", prompt)
        self.assertIn("Here is the LinkedIn profile of Tumelo:", prompt)
        self.assertIn(
            "Here are some notes from Tumelo about their communications style:",
            prompt,
        )
        self.assertIn(
            "Here are direct contact/profile links for Tumelo (share these when asked):",
            prompt,
        )
        self.assertIn("2026-05-28 12:30:00", prompt)


if __name__ == "__main__":
    unittest.main()
