try:
    from .resources import linkedin, summary, facts, style
except ImportError:
    from resources import linkedin, summary, facts, style
from datetime import datetime

from src.app.domain.twin.prompt_builder import TwinPromptBuilder


full_name = facts["full_name"]
name = facts["name"]
email = facts.get("email")
linkedin_url = facts.get("linkedin")
github_url = facts.get("github")


def _as_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _contact_block() -> str:
    items = []
    if email:
        items.append(f"- Email: {email}")
    if linkedin_url:
        items.append(f"- LinkedIn: {_as_url(linkedin_url)}")
    if github_url:
        items.append(f"- GitHub: {_as_url(github_url)}")

    if not items:
        return "No direct contact or profile links are available."

    return "\n".join(items)


def build_prompt_context(now: datetime | None = None) -> dict[str, str]:
    rendered_datetime = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "full_name": full_name,
        "name": name,
        "profile": str(facts),
        "profile_heading": f"Here is some basic information about {name}:",
        "summary": summary,
        "summary_heading": f"Here are summary notes from {name}:",
        "linkedin": linkedin,
        "linkedin_heading": f"Here is the LinkedIn profile of {name}:",
        "style": style,
        "style_heading": f"Here are some notes from {name} about their communications style:",
        "contact_links": _contact_block(),
        "contact_links_heading": f"Here are direct contact/profile links for {name} (share these when asked):",
        "current_datetime": rendered_datetime,
    }


def prompt(builder: TwinPromptBuilder | None = None, now: datetime | None = None) -> str:
    prompt_builder = builder or TwinPromptBuilder()
    return prompt_builder.build_system_prompt(**build_prompt_context(now=now))
