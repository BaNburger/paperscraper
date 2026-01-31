"""AI content generators for papers (pitch, simplified abstract)."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from paper_scraper.modules.scoring.llm_client import get_llm_client

PROMPTS_DIR = Path(__file__).parent / "prompts"


class SimplifiedAbstractGenerator:
    """Generate simplified abstracts for papers."""

    def __init__(self) -> None:
        """Initialize generator with LLM client and template."""
        self.llm = get_llm_client()
        self.env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        self.template = self.env.get_template("simplified_abstract.jinja2")

    async def generate(
        self,
        title: str,
        abstract: str,
    ) -> str:
        """Generate simplified abstract for paper.

        Args:
            title: Paper title.
            abstract: Original paper abstract.

        Returns:
            Simplified abstract string (max 150 words).
        """
        if not abstract:
            return ""

        prompt = self.template.render(
            title=title,
            abstract=abstract,
        )

        simplified = await self.llm.complete(
            prompt=prompt,
            temperature=0.3,  # More deterministic for clarity
            max_tokens=300,
        )

        # Clean up response
        simplified = simplified.strip()

        # Enforce max length of 150 words
        words = simplified.split()
        if len(words) > 150:
            simplified = " ".join(words[:150]) + "..."

        return simplified


class PitchGenerator:
    """Generate compelling one-line pitches for papers."""

    def __init__(self) -> None:
        """Initialize pitch generator with LLM client and template."""
        self.llm = get_llm_client()
        self.env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        self.template = self.env.get_template("one_line_pitch.jinja2")

    async def generate(
        self,
        title: str,
        abstract: str | None,
        keywords: list[str] | None = None,
    ) -> str:
        """Generate one-line pitch for paper.

        Args:
            title: Paper title.
            abstract: Paper abstract (optional but recommended).
            keywords: List of keywords (optional).

        Returns:
            One-line pitch string (max 15 words).
        """
        prompt = self.template.render(
            title=title,
            abstract=abstract or "",
            keywords=keywords or [],
        )

        pitch = await self.llm.complete(
            prompt=prompt,
            temperature=0.7,  # Slightly creative
            max_tokens=50,
        )

        # Clean up response
        pitch = pitch.strip().strip('"').strip("'").strip()

        # Remove any leading/trailing punctuation that might have been added
        if pitch.startswith("-"):
            pitch = pitch[1:].strip()

        # Enforce max length of 15 words
        words = pitch.split()
        if len(words) > 15:
            pitch = " ".join(words[:15])

        return pitch
